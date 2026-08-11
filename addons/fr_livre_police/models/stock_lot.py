# -*- coding: utf-8 -*-
"""La ligne du registre est le lot de stock.

L'art. 56 J quindecies veut « la nature, le nombre, le poids, le titre, la
date d'entrée et de sortie et l'origine [...] afin de permettre leur
identification individuelle ». Entrée et sortie sur la même ligne : le
registre est tenu par objet, non en journal. C'est exactement ce qu'est un
lot dans Odoo — un objet ou un lot d'objets, identifié, suivi de sa réception
à sa livraison.

Plutôt qu'un registre parallèle à réconcilier avec le stock, les mentions
obligatoires vivent donc sur le lot lui-même. Les dates se déduisent des
mouvements : elles ne peuvent pas mentir. Les mentions figées à l'entrée —
vendeur, provenance, prix, poids — sont écrites une fois et ne se recalculent
jamais : le registre atteste ce qui a été constaté au comptoir.
"""

import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools import format_date

from .livre_police_evenement import MENTIONS


class StockLot(models.Model):
    _inherit = 'stock.lot'

    police_registered = fields.Boolean(
        string="Au livre de police", default=False, copy=False,
        help="Lot inscrit au registre des métaux précieux.",
    )
    police_seller_id = fields.Many2one(
        'res.partner', string="Vendeur", copy=False,
        help="Personne qui a vendu ou apporté l'objet (art. R321-3 1°).",
    )
    police_origin = fields.Char(
        string="Provenance", copy=False,
        help="Origine déclarée par le vendeur : succession, achat antérieur, "
             "héritage… Mention obligatoire (art. R321-3 3°).",
    )
    police_weight = fields.Float(
        string="Poids (g)", digits=(12, 4), copy=False,
        help="Poids en grammes constaté à l'entrée. Figé : le registre "
             "atteste ce qui a été pesé, pas ce que le catalogue dirait.",
    )
    police_quantity = fields.Float(
        string="Nombre", digits='Product Unit of Measure', copy=False,
        aggregator=None,
        help="Nombre d'objets entrés (art. 56 J quindecies). Figé à l'entrée : "
             "à ne pas confondre avec le restant en stock.",
    )
    police_fineness = fields.Float(
        string="Titre (millièmes)", digits=(5, 1), copy=False, aggregator=None,
        help="Un titre ne s'additionne pas : la colonne n'est pas totalisée.",
    )
    police_purchase_price = fields.Monetary(
        string="Prix d'achat", currency_field='police_currency_id', copy=False,
        help="Prix payé au vendeur (art. R321-5 1°).",
    )
    police_currency_id = fields.Many2one(
        'res.currency', string="Devise", copy=False,
        default=lambda self: self.env.company.currency_id,
    )
    police_payment_mode = fields.Char(
        string="Mode de règlement", copy=False,
        help="Art. R321-5 1°. Le paiement en espèces est interdit pour les "
             "métaux précieux (art. L112-6 du code monétaire et financier).",
    )
    police_description = fields.Text(
        string="Description des objets",
        help="Ce que contient le lot : caractéristiques, poinçons, numéros de "
             "série, monogrammes — tout ce qui sert à reconnaître les objets "
             "(art. R321-3 du code pénal). Recopiée depuis les notes de "
             "l'avoir à la comptabilisation, puis scellée ici : effacer la "
             "note sur la pièce n'efface plus rien du registre.",
    )
    police_source_move_id = fields.Many2one(
        'account.move', string="Pièce d'entrée", copy=False, readonly=True,
        help="Avoir de rachat ayant fait entrer l'objet au registre.",
    )
    police_entry_date = fields.Datetime(
        string="Date d'entrée", copy=False,
        help="Date à laquelle l'objet est entré au registre. Inscrite lors du "
             "rachat, non déduite : le registre consigne une date, il ne la "
             "recalcule pas.",
    )
    police_exit_date = fields.Datetime(
        string="Date de sortie", copy=False,
        help="Inscrite lorsque l'objet quitte entièrement le stock. Vide tant "
             "qu'il en reste.",
    )
    police_exit_picking_id = fields.Many2one(
        'stock.picking', string="Bon de sortie", copy=False, readonly=True,
        help="Bon pour relève ayant fait sortir l'objet du registre. Un "
             "registre qui note une sortie sans dire vers qui ne trace rien.",
    )
    police_quantity_on_hand = fields.Float(
        string="Restant", compute='_compute_police_quantity_on_hand', store=True,
        digits='Product Unit of Measure', aggregator=None,
    )
    police_opening = fields.Boolean(
        string="Ligne d'ouverture", copy=False,
        help="Objet déjà détenu à la date de bascule. Son vendeur, son prix "
             "et son mode de règlement figurent au registre tenu avant la "
             "reprise : ils ne sont pas exigés ici.",
    )
    police_event_ids = fields.One2many(
        'livre.police.evenement', 'lot_id', string="Journal",
        help="Entrées, sorties et corrections inscrites pour cet objet.",
    )
    police_complete = fields.Boolean(
        string="Mentions complètes", compute='_compute_police_complete',
        store=True,
        help="Toutes les mentions exigées par le registre sont renseignées.",
    )

    @api.depends('quant_ids.quantity', 'quant_ids.location_id')
    def _compute_police_quantity_on_hand(self):
        for lot in self:
            lot.police_quantity_on_hand = sum(lot.quant_ids.filtered(
                lambda q: q.location_id.usage == 'internal').mapped('quantity'))

    @api.depends('police_registered', 'police_seller_id', 'police_origin',
                 'police_weight', 'police_purchase_price', 'police_payment_mode',
                 'police_entry_date', 'police_opening')
    def _compute_police_complete(self):
        """Une ligne d'ouverture atteste une détention, pas une acquisition.

        Lui réclamer un vendeur et un prix d'achat conduirait à en inventer :
        ces mentions appartiennent au registre tenu avant la bascule.
        """
        for lot in self:
            socle = bool(lot.police_registered and lot.police_origin
                         and lot.police_weight and lot.police_entry_date)
            if lot.police_opening:
                lot.police_complete = socle
            else:
                lot.police_complete = bool(
                    socle and lot.police_seller_id
                    and lot.police_purchase_price and lot.police_payment_mode)

    def unlink(self):
        """Un objet inscrit au registre ne s'efface pas.

        R321-6 : « sans blanc, rature ni abréviation ». R321-6-1 impose à un
        registre informatisé de garantir l'intangibilité des données.
        """
        inscrits = self.filtered('police_registered')
        if inscrits:
            raise UserError(_(
                "Ces lots sont inscrits au livre de police et ne peuvent pas "
                "être supprimés : %s",
                ", ".join(inscrits.mapped('name'))))
        return super().unlink()

    # ------------------------------------------------------------------
    # Journal chaîné (R321-6-1)
    # ------------------------------------------------------------------
    def _police_mentions_normalisees(self):
        """Mentions du registre sous une forme stable, pour l'empreinte.

        Normalisée — clés triées, flottants arrondis, dates en ISO — pour
        qu'une même réalité produise toujours la même empreinte, quelle que
        soit la locale ou l'ordre d'écriture.
        """
        self.ensure_one()

        def date(valeur):
            return valeur.isoformat() if valeur else None

        return json.dumps({
            'numero_ordre': self.name,
            'objet': self.product_id.display_name,
            'nature': self.product_id.product_tmpl_id.metal_nature.name or None,
            'nombre': round(self.police_quantity or 0.0, 4),
            'poids': round(self.police_weight or 0.0, 4),
            'titre': round(self.police_fineness or 0.0, 1),
            'vendeur': self.police_seller_id.display_name or None,
            'provenance': self.police_origin or None,
            'description': self.police_description or None,
            'prix': round(self.police_purchase_price or 0.0, 2),
            'devise': self.police_currency_id.name or None,
            'reglement': self.police_payment_mode or None,
            'entree': date(self.police_entry_date),
            'ouverture': bool(self.police_opening),
            'sortie': date(self.police_exit_date),
            'destinataire': (self.police_exit_picking_id.partner_id.display_name
                             or self.police_exit_picking_id.name or None),
            'piece': self.police_source_move_id.name or None,
        }, sort_keys=True, ensure_ascii=False, separators=(',', ':'))

    def _police_inscrire(self, event_type, event_date=False, description=False):
        self.ensure_one()
        return self.env['livre.police.evenement']._inscrire(
            self, event_type, event_date, description)

    def _police_journal_contient(self, event_type):
        self.ensure_one()
        return bool(self.env['livre.police.evenement'].sudo().search_count([
            ('lot_id', '=', self.id), ('event_type', '=', event_type)]))

    def write(self, values):
        """Toute retouche d'une mention déjà inscrite laisse une trace."""
        suivis = [champ for champ in MENTIONS if champ in values]
        avant = {}
        if suivis:
            for lot in self:
                if lot.police_registered and lot.police_event_ids:
                    avant[lot.id] = {c: lot[c] for c in suivis}
        resultat = super().write(values)
        for lot in self:
            ancien = avant.get(lot.id)
            if not ancien:
                continue
            changes = []
            for champ, valeur in ancien.items():
                if lot[champ] != valeur:
                    libelle = self._fields[champ].string
                    changes.append("%s : %s -> %s" % (
                        libelle, self._police_lisible(valeur),
                        self._police_lisible(lot[champ])))
            if changes:
                lot._police_inscrire('correction', description=" ; ".join(changes))
        return resultat

    @api.model
    def _police_lisible(self, valeur):
        if hasattr(valeur, 'display_name'):
            return valeur.display_name or "—"
        return "—" if valeur in (False, None, '') else str(valeur)

    def _police_vendeur(self):
        """Nom, prénoms et domicile du vendeur, tels que le registre les exige.

        L'art. R321-4 du code pénal veut « les nom, prénoms, qualité et
        domicile » ; l'art. 56 J quindecies de l'annexe IV au CGI, « les noms,
        prénoms et adresses ». Le seul nom d'usage ne suffit donc pas.
        Une ligne d'inventaire d'ouverture n'a pas de vendeur : ce qui
        précède la bascule est attesté par le registre antérieur.
        """
        self.ensure_one()
        partenaire = self.police_seller_id
        if not partenaire:
            return ""
        etat_civil = ' '.join(filter(None, [
            (partenaire.lastname or partenaire.name or '').upper(),
            partenaire.firstname or '']))
        domicile = ', '.join(filter(None, [
            partenaire.street, partenaire.street2,
            ' '.join(filter(None, [partenaire.zip, partenaire.city]))]))
        return '\n'.join(filter(None, [etat_civil, domicile]))

    def _police_piece_identite(self):
        """Nature, numéro, date et lieu de délivrance, autorité émettrice.

        Mentions imposées par l'art. R321-4 : « la nature, le numéro et la
        date de délivrance de la pièce d'identité produite […] avec
        l'indication de l'autorité qui l'a établie ».
        """
        self.ensure_one()
        partenaire = self.police_seller_id
        if not partenaire or not partenaire.id_doc_type:
            return ""
        natures = dict(partenaire._fields['id_doc_type']._description_selection(
            self.env))
        premiere = natures.get(partenaire.id_doc_type, partenaire.id_doc_type)
        if partenaire.id_doc_number:
            premiere += " n° %s" % partenaire.id_doc_number
        delivrance = []
        if partenaire.id_doc_issue_date:
            delivrance.append("délivrée le %s" % format_date(
                self.env, partenaire.id_doc_issue_date))
        if partenaire.id_doc_issue_place:
            delivrance.append("à %s" % partenaire.id_doc_issue_place)
        return '\n'.join(filter(None, [
            premiere, ' '.join(delivrance), partenaire.id_doc_authority or '']))

    @api.model
    def _police_create_entry(self, values):
        """Crée un lot inscrit au registre, avec son numéro d'ordre."""
        societe = self.env['res.company'].browse(values['company_id'])
        numero = self.env['res.company']._police_next_number(societe)
        return self.with_company(societe).create(dict(
            values, name=numero, police_registered=True))
