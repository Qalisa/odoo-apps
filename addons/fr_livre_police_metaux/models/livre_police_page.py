# -*- coding: utf-8 -*-
"""La page du jour, et le chiffre de contrôle qui la relie à la précédente.

Le texte décrit ce mécanisme sans le nommer ainsi. Il exige, du registre tenu
par logiciel pour les ouvrages d'occasion, que « le répertoire contenant ces
informations soit spécifique et comprenne un système d'identification des
pages par **chiffre de contrôle**, contenant un algorithme ou un système fondé
notamment sur la date de l'opération, **reporté en fin et en tête des pages
imprimées quotidiennement** » (CGI, ann. IV, art. 56 J sexdecies, 2° c).

Reporter le contrôle en fin d'une page *et* en tête de la suivante, c'est
chaîner : chaque page atteste de celle qui la précède. Retirer une ligne d'une
page ancienne ne casse pas seulement son propre contrôle, il casse tous les
suivants. La rédaction date de 1993 ; elle décrit exactement ce qu'on
appellerait aujourd'hui une chaîne d'empreintes.

L'empreinte est un SHA-256 du contrôle précédent suivi des mentions de la
page, sérialisées de façon stable. La date de la page y entre, comme le texte
le demande.

Deux règles en découlent, et elles sont dans le code plutôt que dans les
usages :

* une page se scelle **dans l'ordre** — sceller la page 12 avant la 11 ne
  produirait pas une chaîne mais deux morceaux ;
* une page scellée **ne se rouvre pas**. Une inscription qui arrive après la
  fermeture du jour va sur la page suivante, à sa date : c'est le propre d'un
  registre tenu au jour le jour.

Le même article demande que « l'opérateur [soit] en mesure d'apporter la
preuve de la fiabilité du système informatique utilisé et de la chronologie
des écritures », et que « les feuillets informatiques [soient] identifiés,
numérotés et datés sans possibilité de modifications ». C'est ce que porte ce
modèle : un numéro continu par société, une date, un scellement horodaté et
nominatif.
"""

import hashlib
import json

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LivrePolicePage(models.Model):
    _name = 'livre.police.page'
    _description = "Livre de police - page du registre"
    _order = 'company_id, numero'
    _rec_name = 'numero'

    numero = fields.Char(
        string="N° de page", required=True, index=True, readonly=True,
        help="Numéro continu par société. Une page manquante ne se justifie "
             "pas plus qu'une inscription manquante.",
    )
    date = fields.Date(
        string="Date", required=True, index=True, readonly=True,
        help="Jour des inscriptions portées sur cette page.",
    )
    company_id = fields.Many2one(
        'res.company', string="Société", required=True, index=True,
        readonly=True,
    )
    ligne_ids = fields.One2many(
        'livre.police.ligne', 'page_id', string="Inscriptions", readonly=True,
    )
    nombre_inscriptions = fields.Integer(
        string="Inscriptions", compute='_compute_totaux',
    )
    poids_total = fields.Float(
        string="Poids total (g)", digits=(12, 4), compute='_compute_totaux',
    )
    montant_total = fields.Monetary(
        string="Montant total", currency_field='currency_id',
        compute='_compute_totaux',
    )
    currency_id = fields.Many2one(
        related='company_id.currency_id', readonly=True,
    )

    page_precedente_id = fields.Many2one(
        'livre.police.page', string="Page précédente", readonly=True,
        ondelete='restrict', index='btree_not_null',
    )
    controle_precedent = fields.Char(
        string="Contrôle en tête", readonly=True,
        help="Chiffre de contrôle de la page précédente, reporté en tête de "
             "celle-ci. C'est lui qui fait la chaîne.",
    )
    controle = fields.Char(
        string="Chiffre de contrôle", readonly=True, index='btree_not_null',
        help="Empreinte de la page, calculée au scellement sur le contrôle "
             "précédent et sur les mentions inscrites. Se reporte en pied de "
             "cette page et en tête de la suivante.",
    )
    scellee_le = fields.Datetime(string="Scellée le", readonly=True)
    scellee_par_id = fields.Many2one(
        'res.users', string="Scellée par", readonly=True,
    )
    scellee = fields.Boolean(
        string="Scellée", compute='_compute_scellee', store=True,
    )

    _sql_constraints = [
        ('numero_unique', 'unique(company_id, numero)',
         "Deux pages du registre ne peuvent pas porter le même numéro dans "
         "la même société."),
    ]

    @api.depends('controle')
    def _compute_scellee(self):
        for page in self:
            page.scellee = bool(page.controle)

    @api.depends('ligne_ids.poids', 'ligne_ids.prix')
    def _compute_totaux(self):
        for page in self:
            page.nombre_inscriptions = len(page.ligne_ids)
            page.poids_total = sum(page.ligne_ids.mapped('poids'))
            page.montant_total = sum(page.ligne_ids.mapped('prix'))

    # ------------------------------------------------------------------
    # Ouvrir la page du jour
    # ------------------------------------------------------------------

    @api.model
    def _sequence(self, societe):
        Sequence = self.env['ir.sequence'].sudo()
        suite = Sequence.search([('code', '=', 'livre.police.page'),
                                 ('company_id', '=', societe.id)], limit=1)
        if not suite:
            suite = Sequence.create({
                'name': "Livre de police, pages - %s" % societe.name,
                'code': 'livre.police.page',
                'company_id': societe.id,
                'implementation': 'no_gap',
                'padding': 5,
                'number_next': 1,
            })
        return suite

    @api.model
    def _page_courante(self, societe):
        """Page ouverte du jour, créée au premier besoin.

        On cherche une page **non scellée** : si le jour a déjà été fermé et
        qu'un rachat arrive encore, il ne rouvre pas la page close, il en
        ouvre une autre à la même date. Le texte parle de pages imprimées
        quotidiennement, pas d'une page par jour — et rouvrir un sceau serait
        exactement ce qu'un registre ne doit pas permettre.
        """
        aujourdhui = fields.Date.context_today(self)
        page = self.sudo().search([
            ('company_id', '=', societe.id),
            ('date', '=', aujourdhui),
            ('controle', '=', False),
        ], order='numero desc', limit=1)
        if not page:
            page = self.sudo().create({
                'numero': self._sequence(societe).next_by_id(),
                'date': aujourdhui,
                'company_id': societe.id,
            })
        return page

    # ------------------------------------------------------------------
    # Sceller
    # ------------------------------------------------------------------

    def _empreinte(self, controle_precedent):
        """SHA-256 du contrôle précédent suivi des mentions de la page."""
        self.ensure_one()
        contenu = {
            'page': self.numero,
            'date': fields.Date.to_string(self.date),
            'societe': self.company_id.id,
            'lignes': [ligne._empreinte_donnees()
                       for ligne in self.ligne_ids.sorted('numero_ordre')],
        }
        serialise = json.dumps(contenu, sort_keys=True, ensure_ascii=True,
                               separators=(',', ':'))
        return hashlib.sha256(
            ((controle_precedent or '') + serialise).encode('utf-8')).hexdigest()

    def action_sceller(self):
        """Ferme la page et la relie à la précédente."""
        for page in self.sorted('numero'):
            if page.controle:
                raise UserError(_(
                    "La page %(numero)s est déjà scellée : un sceau ne se "
                    "refait pas.", numero=page.numero))
            precedente = self.sudo().search([
                ('company_id', '=', page.company_id.id),
                ('numero', '<', page.numero),
            ], order='numero desc', limit=1)
            if precedente and not precedente.controle:
                raise UserError(_(
                    "La page %(precedente)s n'est pas scellée : les pages se "
                    "scellent dans l'ordre.\n\n"
                    "Le chiffre de contrôle d'une page se reporte en tête de "
                    "la suivante (CGI, ann. IV, art. 56 J sexdecies, 2° c). "
                    "Sceller la %(numero)s d'abord ne produirait pas une "
                    "chaîne, mais deux morceaux.",
                    precedente=precedente.numero, numero=page.numero))
            page.sudo().write({
                'page_precedente_id': precedente.id,
                'controle_precedent': precedente.controle,
                'controle': page._empreinte(precedente.controle),
                'scellee_le': fields.Datetime.now(),
                'scellee_par_id': self.env.user.id,
            })
        return True

    @api.model
    def _cron_sceller_les_jours_clos(self):
        """Scelle chaque page dont le jour est passé.

        Un jour se ferme de lui-même : personne n'a à y penser, et une page
        oubliée resterait ouverte à des inscriptions qui ne lui appartiennent
        pas.
        """
        aujourdhui = fields.Date.context_today(self)
        a_sceller = self.sudo().search([
            ('controle', '=', False),
            ('date', '<', aujourdhui),
        ], order='company_id, numero')
        for _societe, pages in a_sceller.grouped('company_id').items():
            pages.action_sceller()
        return len(a_sceller)

    def write(self, vals):
        """Une page scellée ne se rouvre pas."""
        scellees = self.filtered('controle')
        if scellees:
            raise UserError(_(
                "La page %(numeros)s est scellée : son contenu et son chiffre "
                "de contrôle ne se modifient plus.",
                numeros=", ".join(scellees.mapped('numero'))))
        return super().write(vals)

    def unlink(self):
        if self.filtered('controle'):
            raise UserError(_(
                "Une page scellée ne se supprime pas : la chaîne des chiffres "
                "de contrôle serait rompue, et rien ne permettrait de le "
                "justifier."))
        return super().unlink()
