# -*- coding: utf-8 -*-
"""Qui a ouvert le registre, quand, et pourquoi.

« Les consultations du traitement automatisé font l'objet d'un enregistrement
comprenant l'identifiant du consultant, la date, l'heure et l'objet de la
consultation. Ces informations sont conservées pendant un délai d'un an »
(arrêté du 15 mai 2020, art. 3, 2°).

C'est la seule obligation du registre qui porte sur les **lectures**. Odoo
trace les écritures — le chatter, les journaux techniques — mais rien ne dit
qui a regardé quoi. Il fallait donc l'écrire.

L'objet ne se devine pas : un logiciel sait qu'on ouvre le registre, il ne
sait pas pourquoi. Il se déclare donc, avant d'entrer, dans une liste courte
qui couvre les raisons réelles d'ouvrir un registre d'objets mobiliers. C'est
une friction assumée : sans elle, la mention exigée n'existerait pas.

Trois portes mènent au registre, et les trois laissent trace : le menu, qui
passe par la déclaration ; l'édition quotidienne ; le contrôle d'intégrité.
Reste qu'une URL saisie à la main atteint la liste sans déclaration — c'est
pourquoi l'accès est réservé à un groupe nommé plutôt qu'ouvert au comptoir.

La déclaration est une page de l'application, et non une fenêtre modale : on
entre dans le livre de police, puis un bouton l'ouvre. Une modale s'ouvrait
par-dessus le module d'où l'on venait, et le registre héritait de son fil
d'Ariane — on le lisait depuis l'inventaire.

La conservation est d'un an. Au-delà, la trace est effacée : le texte fixe une
durée, et garder des données nominatives de lecture plus longtemps que ce
qu'il demande ne se justifierait devant personne.
"""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

OBJETS = [
    ('controle_administratif', "Contrôle administratif ou de police"),
    ('requisition', "Réquisition judiciaire"),
    ('verification_interne', "Vérification interne"),
    ('recherche_objet', "Recherche sur un objet ou un vendeur"),
    ('edition', "Édition du registre"),
    ('integrite', "Contrôle d'intégrité"),
    ('autre', "Autre motif"),
]


class LivrePoliceConsultation(models.Model):
    _name = 'livre.police.consultation'
    _description = "Livre de police - consultation du registre"
    _order = 'date desc, id desc'
    _rec_name = 'date'

    user_id = fields.Many2one(
        'res.users', string="Consultant", required=True, readonly=True,
        index=True,
        help="L'identifiant du consultant, que l'arrêté exige de "
             "l'enregistrement de chaque consultation.",
    )
    date = fields.Datetime(
        string="Date et heure", required=True, readonly=True, index=True,
    )
    objet = fields.Selection(
        OBJETS, string="Objet de la consultation", required=True, readonly=True,
    )
    precision = fields.Char(string="Précision", readonly=True)
    portee = fields.Char(
        string="Portée", readonly=True,
        help="Ce qui a été ouvert : le registre, une édition du jour, un "
             "contrôle d'intégrité.",
    )
    company_id = fields.Many2one(
        'res.company', string="Société", readonly=True, index=True,
    )

    @api.model
    def _tracer(self, objet, portee, precision=None, societe=None):
        """Enregistre une consultation. Jamais rien de plus que le texte."""
        return self.sudo().create({
            'user_id': self.env.user.id,
            'date': fields.Datetime.now(),
            'objet': objet,
            'precision': precision or False,
            'portee': portee,
            'company_id': (societe or self.env.company).id,
        })

    @api.model
    def _cron_purger(self):
        """Efface les traces de plus d'un an.

        Le texte fixe une durée de conservation, pas un minimum à dépasser :
        garder plus longtemps des données nominatives de lecture ne se
        justifierait devant personne.
        """
        limite = fields.Datetime.now() - relativedelta(years=1)
        anciennes = self.sudo().search([('date', '<', limite)])
        nombre = len(anciennes)
        anciennes.unlink()
        return nombre

    def write(self, vals):
        if self:
            raise UserError(_(
                "Une consultation enregistrée ne se modifie pas."))
        return super().write(vals)


class LivrePoliceAcces(models.TransientModel):
    _name = 'livre.police.acces'
    _description = "Livre de police - déclarer l'objet d'une consultation"

    objet = fields.Selection(
        [(cle, libelle) for cle, libelle in OBJETS
         if cle not in ('edition', 'integrite')],
        string="Objet de la consultation", required=True,
        default='verification_interne',
    )
    precision = fields.Char(
        string="Précision",
        help="Nom du service, numéro de réquisition, objet recherché… Ce qui "
             "permettra, plus tard, de savoir de quoi il s'agissait.",
    )

    def action_ouvrir(self):
        """Enregistre la consultation, puis ouvre le registre.

        Le registre s'ouvre en « main » : il remplace la déclaration au
        lieu de s'empiler dessus. Le fil d'Ariane commence donc au registre,
        et le retour arrière n'y ramène pas une page de formalité déjà
        remplie — pour reconsulter, on repasse par le menu, ce qui est
        précisément ce que l'arrêté veut voir tracé.
        """
        self.ensure_one()
        self.env['livre.police.consultation']._tracer(
            self.objet, "Registre", self.precision)
        action = self.env.ref(
            'fr_livre_police_metaux.livre_police_ligne_action').sudo().read()[0]
        action['target'] = 'main'
        return action


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    # Imprimer le registre est une consultation comme une autre — et c'est
    # même celle qui sort du logiciel. Les deux éditions se tracent seules :
    # leur objet, lui, ne fait aucun doute.
    _LIVRE_POLICE_RAPPORTS = {
        'fr_livre_police_metaux.rapport_page': (
            'edition', "Édition du registre du jour"),
        'fr_livre_police_metaux.rapport_controle': (
            'integrite', "Contrôle d'intégrité"),
    }

    def _render_qweb_pdf(self, report_ref, res_ids=None, data=None):
        trace = self._LIVRE_POLICE_RAPPORTS.get(report_ref)
        if trace:
            objet, portee = trace
            self.env['livre.police.consultation']._tracer(objet, portee)
        return super()._render_qweb_pdf(report_ref, res_ids=res_ids, data=data)
