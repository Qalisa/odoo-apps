# -*- coding: utf-8 -*-
"""Le rachat se saisit sur un devis, en quantité négative.

L'établissement n'y vend rien : il achète. C'est le signe de la quantité qui
dit le sens de l'opération, et donc si la ligne fait entrer un objet dans les
murs — le seul cas où le registre réclame une description.

La description n'a pas de champ à elle : elle se met là où le comptoir la met
déjà, dans le champ « Description » de la ligne, sous la désignation de
l'article. Voir ``tools/description.py`` pour ce qui compte comme description.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..tools.description import description_ajoutee


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    police_description_required = fields.Boolean(
        string="Description exigée",
        compute='_compute_police_description_required',
        help="Vrai lorsque la ligne fait entrer un objet à décrire.",
    )
    police_description_missing = fields.Boolean(
        string="Description manquante",
        compute='_compute_police_description_missing',
        help="Le libellé de la ligne n'ajoute rien à la désignation de "
             "l'article : les objets ne sont pas décrits.",
    )

    @api.depends('display_type', 'product_uom_qty',
                 'product_id.product_tmpl_id.police_description_required')
    def _compute_police_description_required(self):
        for ligne in self:
            ligne.police_description_required = bool(
                not ligne.display_type
                and ligne.product_uom_qty < 0
                and ligne.product_id.product_tmpl_id.police_description_required)

    def _police_description(self):
        """Description des objets lue sur le libellé de la ligne."""
        self.ensure_one()
        produit = self.product_id
        return description_ajoutee(
            self.name, produit.get_product_multiline_description_sale(),
            produit.description_sale)

    @api.depends('police_description_required', 'name')
    def _compute_police_description_missing(self):
        for ligne in self:
            ligne.police_description_missing = bool(
                ligne.police_description_required and not ligne._police_description())


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def _police_check_descriptions(self):
        """Refuse un rachat dont les objets ne sont pas décrits.

        Le contrôle est posé à la confirmation, tant que le vendeur est
        encore au comptoir : plus tard, personne ne saura dire si c'était une
        gourmette ou une chaîne.
        """
        for commande in self:
            muettes = commande.order_line.filtered('police_description_missing')
            if muettes:
                raise UserError(_(
                    "Les objets rachetés doivent être décrits (art. R321-3 3° "
                    "du code pénal). Complétez la description sous la "
                    "désignation, sur :\n  - %s",
                    "\n  - ".join(l.product_id.display_name for l in muettes)))

    def action_confirm(self):
        self._police_check_descriptions()
        return super().action_confirm()
