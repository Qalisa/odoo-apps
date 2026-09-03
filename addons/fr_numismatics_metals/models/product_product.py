# -*- coding: utf-8 -*-
"""Poids du métal réellement détenu, article par article.

Le poids d'un objet vit sur l'article — au gramme, la quantité *est* le
poids ; à la pièce, il se déduit du poids unitaire. La même règle appliquée
à ce qui est en stock répond à une question que le comptoir se pose tous les
jours et qu'aucun écran d'Odoo ne sait poser : combien de grammes d'or y
a-t-il dans le coffre ?

Rien de neuf n'est décidé ici. C'est ``metals.derive_weight``, celle qui
donne son poids à une ligne d'achat, appliquée à la quantité en stock. Une
seule règle, deux emplois.
"""

from odoo import models, fields, api

from ..tools import metals


class ProductProduct(models.Model):
    _inherit = 'product.product'

    metal_stock_weight = fields.Float(
        string="Poids en stock (g)", digits=(12, 4),
        compute='_compute_metal_stock_weight',
        help="Poids en grammes du métal actuellement détenu pour cet "
             "article, déduit de la quantité en stock comme le poids d'une "
             "ligne d'achat se déduit de sa quantité : au gramme, la "
             "quantité vaut le poids ; à la pièce, elle est multipliée par "
             "le poids unitaire.\n\n"
             "Suit les établissements cochés en haut de l'écran : trois "
             "comptoirs cochés donnent le poids détenu par les trois.\n\n"
             "Reste à zéro pour un article dont le poids ne se déduit pas — "
             "objet à la pièce sans poids unitaire, cas que la contrainte de "
             "saisie interdit désormais.",
    )

    # `qty_available` se calcule à la volée, à partir du contexte : sociétés
    # cochées, entrepôt, date, lot. Ce poids en hérite — il ne peut donc être
    # ni stocké ni trié, et c'est la même raison qui interdit de trier sur la
    # quantité elle-même.
    #
    # Les clefs de contexte se redéclarent ici, à l'identique de
    # `_compute_quantities` : Odoo ne les collecte que sur la fonction de
    # calcul, jamais sur les champs dont elle dépend. Sans elles, le poids
    # serait mis en cache une fois et resservi tel quel en changeant
    # d'établissement — celui de Metz s'afficherait pour Nancy.
    @api.depends('qty_available', 'metal_quantity_mode', 'metal_unit_weight')
    @api.depends_context(
        'lot_id', 'owner_id', 'package_id', 'from_date', 'to_date',
        'location', 'warehouse_id', 'allowed_company_ids', 'is_storable',
    )
    def _compute_metal_stock_weight(self):
        for product in self:
            product.metal_stock_weight = metals.derive_weight(
                product.metal_quantity_mode, product.metal_unit_weight,
                product.qty_available) or 0.0
