# -*- coding: utf-8 -*-
"""Quantité proposée à l'ajout d'une ligne.

Le défaut voyage par le contexte du champ ``order_line``, que la vue
réévalue à chaque changement du devis : changer de modèle change le défaut,
sans rien enregistrer.

Ce champ ne se stocke pas — il ne décrit pas le devis, il décrit ce qu'on
proposera à la prochaine ligne.
"""

from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    new_line_qty = fields.Float(
        string="Quantité proposée", compute='_compute_new_line_qty',
        help="Quantité proposée à l'ajout d'une ligne, selon le modèle de "
             "devis employé.",
    )

    @api.depends('sale_order_template_id.negative_qty_default')
    def _compute_new_line_qty(self):
        for devis in self:
            devis.new_line_qty = (
                -1.0 if devis.sale_order_template_id.negative_qty_default
                else 1.0)
