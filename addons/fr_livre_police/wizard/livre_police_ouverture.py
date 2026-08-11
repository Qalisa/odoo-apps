# -*- coding: utf-8 -*-
"""Inventaire d'ouverture : ce que le coffre contient au jour de la bascule.

R321-4 vise « chaque objet exposé à la vente ou **détenu en stock** ». Le
registre ne commence donc pas à zéro : ce que les agences détiennent à la
date de bascule doit y figurer, avec un numéro d'ordre.

Ces objets ont été acquis **avant**. Leur vendeur, leur prix et leur mode de
règlement sont consignés au registre papier tenu à l'époque — pas dans Odoo.
On ne les invente pas : ce serait corrompre le registre. La ligne d'ouverture
atteste une détention à une date, pas une acquisition, et le renvoi au
registre antérieur en tient lieu de provenance.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..models import stock_lot  # noqa: F401  (enregistre le modèle)


class LivrePoliceOuverture(models.TransientModel):
    _name = 'livre.police.ouverture'
    _description = "Inventaire d'ouverture du livre de police"

    company_id = fields.Many2one(
        'res.company', string="Établissement", required=True,
        default=lambda self: self.env.company)
    opening_date = fields.Date(
        string="Date de l'inventaire", required=True,
        compute='_compute_opening_date', store=True, readonly=False,
        # Requis et calculé : sans `precompute`, la colonne serait encore
        # nulle au moment de l'insertion.
        precompute=True,
        help="Date à laquelle le coffre a été compté. Par défaut, la date de "
             "début du registre de l'établissement.")
    origin = fields.Char(
        string="Provenance", required=True,
        default="Reprise du registre antérieur",
        help="Mention portée sur chaque ligne créée. Ces objets ayant été "
             "acquis avant la bascule, leur origine détaillée reste au "
             "registre tenu à l'époque.")
    line_ids = fields.One2many(
        'livre.police.ouverture.ligne', 'wizard_id', string="Objets comptés")
    already_done = fields.Boolean(
        string="Ouverture déjà effectuée", compute='_compute_already_done')
    previous_date = fields.Datetime(
        string="Ouverture précédente", compute='_compute_already_done')
    confirm_complement = fields.Boolean(
        string="Compléter une ouverture déjà effectuée",
        help="Un inventaire d'ouverture ne se rejoue pas : le relancer par "
             "mégarde doublerait le stock et le registre. Ne cocher que pour "
             "ajouter un comptage manquant.")

    @api.depends('company_id')
    def _compute_opening_date(self):
        """Le champ est requis en base : à défaut de date de bascule, la date
        du jour, et c'est `_verifier` qui refusera avec un motif lisible."""
        for wizard in self:
            wizard.opening_date = (wizard.company_id.police_start_date
                                   or fields.Date.context_today(wizard))

    @api.depends('company_id')
    def _compute_already_done(self):
        for wizard in self:
            wizard.previous_date = wizard.company_id.police_opening_date
            wizard.already_done = bool(wizard.company_id.police_opening_date)

    def _verifier(self):
        self.ensure_one()
        if not self.company_id.police_start_date:
            raise UserError(_(
                "Le livre de police de %s n'a pas de date de début : "
                "renseignez-la dans les paramètres avant l'inventaire "
                "d'ouverture.", self.company_id.name))
        if not self.line_ids:
            raise UserError(_("Aucun objet compté."))
        if self.already_done and not self.confirm_complement:
            raise UserError(_(
                "Un inventaire d'ouverture a déjà été effectué pour %s le %s. "
                "Le rejouer doublerait le stock et le registre. Cochez "
                "« Compléter une ouverture déjà effectuée » si vous ajoutez "
                "sciemment un comptage manquant.",
                self.company_id.name, self.previous_date))
        sans_poids = self.line_ids.filtered(lambda l: not l.weight)
        if sans_poids:
            raise UserError(_(
                "Le poids est une mention obligatoire du registre. Il manque "
                "sur : %s", ", ".join(sans_poids.mapped('product_id.name'))))

    def action_valider(self):
        """Crée les lignes de registre et pose le stock correspondant."""
        self.ensure_one()
        self._verifier()
        societe = self.company_id
        entrepot = self.env['stock.warehouse'].search(
            [('company_id', '=', societe.id)], limit=1)
        if not entrepot:
            raise UserError(_(
                "Aucun entrepôt n'est défini pour %s.", societe.name))
        emplacement = entrepot.lot_stock_id
        date = fields.Datetime.to_datetime(self.opening_date)
        Lot = self.env['stock.lot']
        Quant = self.env['stock.quant'].with_company(societe)

        lots = self.env['stock.lot']
        for ligne in self.line_ids:
            # `product_id` désigne ici l'article ; le stock et le lot
            # travaillent sur la variante.
            variante = ligne.product_id.product_variant_id
            lot = Lot._police_create_entry({
                'product_id': variante.id,
                'company_id': societe.id,
                'police_origin': self.origin,
                'police_weight': ligne.weight,
                'police_quantity': ligne.quantity,
                'police_fineness': ligne.fineness,
                'police_description': ligne.description,
                'police_opening': True,
                'police_entry_date': date,
            })
            quant = Quant.create({
                'product_id': variante.id,
                'location_id': emplacement.id,
                'lot_id': lot.id,
                'inventory_quantity': ligne.quantity,
            })
            quant.action_apply_inventory()
            lot._police_inscrire(
                'ouverture', date,
                description=_("Inventaire d'ouverture du %s",
                              self.opening_date))
            lots |= lot

        if not societe.police_opening_date:
            societe.sudo().police_opening_date = date

        return {
            'type': 'ir.actions.act_window',
            'name': _("Livre de police — ouverture"),
            'res_model': 'stock.lot',
            'view_mode': 'list,form',
            'domain': [('id', 'in', lots.ids)],
            'context': {'search_default_group_company': 0},
        }


class LivrePoliceOuvertureLigne(models.TransientModel):
    _name = 'livre.police.ouverture.ligne'
    _description = "Objet compté à l'ouverture du livre de police"

    wizard_id = fields.Many2one(
        'livre.police.ouverture', required=True, ondelete='cascade')
    product_id = fields.Many2one(
        'product.template', string="Objet", required=True,
        domain=[('metal_regulated', '=', True)])
    quantity = fields.Float(
        string="Nombre", required=True, default=1.0,
        digits='Product Unit of Measure')
    weight = fields.Float(
        string="Poids (g)", digits=(12, 4),
        compute='_compute_defauts', store=True, readonly=False,
        help="Déduit du régime de l'article quand c'est possible, à peser "
             "sinon — un lot hétérogène n'a pas de poids déductible.")
    fineness = fields.Float(
        string="Titre (millièmes)", digits=(5, 1),
        compute='_compute_defauts', store=True, readonly=False)
    quantity_mode = fields.Selection(
        related='product_id.metal_quantity_mode', string="Régime")
    description = fields.Text(
        string="Description des objets",
        help="Ce que contient le lot compté : caractéristiques, poinçons, "
             "numéros de série (art. R321-3). Un lot d'or 18 carats se décrit "
             "par ce qu'il renferme, pas par son poids.")

    @api.depends('product_id', 'quantity')
    def _compute_defauts(self):
        from odoo.addons.fr_numismatics_metals.tools import metals
        for ligne in self:
            article = ligne.product_id
            ligne.fineness = article.metal_fineness
            deduit = metals.derive_weight(
                article.metal_quantity_mode, article.metal_unit_weight,
                ligne.quantity)
            ligne.weight = deduit or 0.0
