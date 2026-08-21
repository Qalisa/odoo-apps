# -*- coding: utf-8 -*-
"""Poids métal d'une ligne d'avoir de rachat.

Le poids est la mention la plus fragile du livre de police : il n'existe
nulle part ailleurs sous forme exploitable. Ce champ le matérialise, en
grammes, déduit des caractéristiques de l'article quand elles le permettent,
saisi à la main pour les lots hétérogènes — seul cas irréductible.

Une ligne comptabilisée n'est jamais recalculée : le registre atteste ce qui a
été consigné, pas ce que le catalogue dirait aujourd'hui.
"""

from odoo import models, fields, api

from ..tools import metals


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    metal_weight = fields.Float(
        string="Poids (g)", digits=(12, 4),
        compute='_compute_metal_weight', store=True, readonly=False,
        help="Poids en grammes du métal acheté sur cette ligne, mention "
             "exigée au livre de police (art. R321-4 du code pénal). "
             "Déduit de l'article quand c'est possible, à saisir sinon.",
    )
    metal_weight_missing = fields.Boolean(
        string="Poids manquant", compute='_compute_metal_weight_missing',
        store=True, help="Ligne portant un objet en métal précieux dont le "
                         "poids n'est pas renseigné.",
    )
    metal_price_per_gram = fields.Float(
        string="Prix au gramme", digits=(12, 2),
        compute='_compute_metal_price_per_gram', store=True,
        help="Prix au gramme constaté sur la ligne : montant divisé par le "
             "poids. Rien à paramétrer — il découle de l'article et de la "
             "saisie. Trier dessus fait ressortir les lignes dont la "
             "quantité, le prix ou le poids est erroné.",
    )

    def _derive_metal_weight(self):
        """Poids déductible de l'article, ou ``None`` si rien de déductible."""
        self.ensure_one()
        product = self.product_id
        return metals.derive_weight(
            product.metal_quantity_mode, product.metal_unit_weight, self.quantity)

    def _stored_metal_weight(self):
        """Poids tel qu'il est consigné en base, sans repasser par le calcul.

        Relire ``metal_weight`` depuis l'ORM au sein de son propre calcul
        renverrait la valeur en cours de recalcul, c'est-à-dire zéro. Un lot
        n'a que sa valeur saisie : il faut aller la chercher.
        """
        ids = [line.id for line in self if isinstance(line.id, int)]
        if not ids:
            return {}
        self.env.cr.execute(
            "SELECT id, metal_weight FROM account_move_line WHERE id IN %s",
            (tuple(ids),))
        return {row[0]: row[1] or 0.0 for row in self.env.cr.fetchall()}

    # Volontairement indépendant des caractéristiques de l'article : corriger
    # le poids unitaire d'une pièce au catalogue ne doit jamais réécrire les
    # lignes déjà saisies. Le registre atteste ce qui a été consigné, pas ce
    # que le catalogue dirait aujourd'hui.
    @api.depends('product_id', 'quantity')
    def _compute_metal_weight(self):
        stored = self._stored_metal_weight()
        for line in self:
            derived = line._derive_metal_weight()
            # Un lot conserve le poids saisi : rien ne permet de le recalculer.
            line.metal_weight = stored.get(line.id, 0.0) if derived is None else derived

    @api.depends('metal_weight', 'product_id.metal_is_object')
    def _compute_metal_weight_missing(self):
        for line in self:
            line.metal_weight_missing = (
                bool(line.product_id.metal_is_object) and not line.metal_weight)

    @api.depends('metal_weight', 'quantity', 'price_unit')
    def _compute_metal_price_per_gram(self):
        for line in self:
            line.metal_price_per_gram = metals.price_per_gram(
                line.quantity * line.price_unit, line.metal_weight) or 0.0
