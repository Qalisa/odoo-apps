# -*- coding: utf-8 -*-
"""Un article soumis au registre doit être suivi en stock, et par lot.

Le registre est tenu par objet identifié : sans suivi de stock il n'y a ni
entrée ni sortie, et sans lot il n'y a pas de numéro d'ordre. Ces deux
réglages accompagnent donc la case « Soumis au livre de police ».

Posés à la création et lorsque la case est cochée, pas par un champ calculé :
un calcul devrait réaffirmer une valeur à chaque passage, et « laisser en
l'état » n'existe pas dans un calcul — relire le champ depuis son propre
calcul renvoie la valeur en cours d'établissement, c'est-à-dire rien. Une
pose explicite laisse le dernier mot à l'utilisateur, qui peut décocher
ensuite sans que rien ne le contredise.
"""

from odoo import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def _police_apply_stock_defaults(self):
        """Met en stock, avec suivi par lot, les articles soumis au registre."""
        a_regler = self.filtered(
            lambda p: p.metal_regulated
            and (not p.is_storable or p.tracking != 'lot'))
        if a_regler:
            # N'écrit pas `metal_regulated` : pas de récursion.
            a_regler.write({'is_storable': True, 'tracking': 'lot'})

    @api.model_create_multi
    def create(self, vals_list):
        produits = super().create(vals_list)
        produits._police_apply_stock_defaults()
        return produits

    def write(self, values):
        resultat = super().write(values)
        if values.get('metal_regulated'):
            self._police_apply_stock_defaults()
        return resultat
