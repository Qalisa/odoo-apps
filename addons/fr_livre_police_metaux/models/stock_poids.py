# -*- coding: utf-8 -*-
"""Le poids, partout où le stock montre une quantité.

Une quantité ne dit pas un poids, et l'écran ne laisse pas deviner lequel.
Sur un article au gramme les deux nombres coïncident, mais l'unité de mesure
affichée reste « Unité(s) » : « 40,00 Unité(s) » désigne quarante grammes
sans le dire. Sur une pièce, les deux nombres diffèrent franchement — quatre
« 100 FRANCS OR » font 129,0320 g.

Or c'est le poids, et non la quantité, que le registre des métaux précieux
réclame (CGI, ann. IV, art. 56 J quindecies). Autant le lire sur le
transfert, avant de valider, plutôt que de le découvrir inscrit.

Le calcul est celui de `fr_numismatics_metals` — le même qui alimente le
poids des lignes d'avoir. En écrire un second ici garantirait qu'un jour les
deux divergent, et c'est l'écran qui aurait tort contre le registre.
"""

from odoo import api, fields, models

from odoo.addons.fr_numismatics_metals.tools import metals


def _poids(produit, quantite):
    """Poids en grammes déductible de l'article, 0 s'il n'y a pas de métal."""
    modele = produit.product_tmpl_id
    return metals.derive_weight(
        modele.metal_quantity_mode, modele.metal_unit_weight, quantite) or 0.0


class StockMove(models.Model):
    _inherit = 'stock.move'

    police_poids_demande = fields.Float(
        string="Poids demandé (g)", digits=(12, 4),
        compute='_compute_police_poids',
        help="Ce que la demande représente en grammes.",
    )
    police_poids = fields.Float(
        string="Poids (g)", digits=(12, 4), compute='_compute_police_poids',
        help="Ce qui part réellement, en grammes. Vide sur un article hors "
             "métaux précieux — un port, un arrondi.",
    )

    @api.depends('product_id', 'product_uom_qty', 'quantity')
    def _compute_police_poids(self):
        for mouvement in self:
            mouvement.police_poids_demande = _poids(
                mouvement.product_id, mouvement.product_uom_qty)
            mouvement.police_poids = _poids(
                mouvement.product_id, mouvement.quantity)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    police_poids = fields.Float(
        string="Poids (g)", digits=(12, 4), compute='_compute_police_poids',
        help="Poids en grammes de ce départ, déduit de l'article : au gramme "
             "la quantité est le poids, à la pièce elle se multiplie par le "
             "poids unitaire. Vide sur un article hors métaux précieux.",
    )

    @api.depends('product_id', 'quantity')
    def _compute_police_poids(self):
        for mouvement in self:
            mouvement.police_poids = _poids(
                mouvement.product_id, mouvement.quantity)
