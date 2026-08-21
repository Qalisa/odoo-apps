# -*- coding: utf-8 -*-
"""Caractéristiques métal d'un article du catalogue.

Ces champs conditionnent la mention « désignation de l'objet » du livre de
police (art. R321-4 du code pénal) : nature du métal, titre et poids. Sans eux,
le poids d'une ligne d'achat n'est pas calculable dès que la quantité compte
des pièces plutôt que des grammes.

Pourquoi ne pas réutiliser le champ standard ``weight`` (onglet Logistique) ?

* il est exprimé dans l'unité de ``product.weight_in_lbs``, soit **kg** ici,
  et arrondi à la précision décimale ``Stock Weight`` — **2 décimales** en
  production. Un 20 Francs Or (6,4516 g = 0,0064516 kg) y serait stocké à
  0,01 kg, soit **10 g** : 55 % d'erreur, et toutes les pièces d'argent
  légères tomberaient à zéro ;
* il ne porte qu'un poids : ni la nature, ni le titre, ni surtout le *régime*
  de saisie de la quantité, dont dépend tout le calcul du poids des lignes.

Le poids unitaire vit donc ici, en **grammes**, unité du métier et du registre.
"""

from odoo import models, fields, api

from ..tools import metals

MODE_SELECTION = [
    ('gram', "Au gramme (quantité = poids)"),
    ('unit', "À la pièce (poids unitaire fixe)"),
    ('lot', "Au lot (poids saisi à la ligne)"),
]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    metal_regulated = fields.Boolean(
        string="Soumis au livre de police",
        compute='_compute_metal_regulated', store=True, readonly=False,
        help="Coché d'office sur les biens : un objet acheté d'occasion doit "
             "figurer au registre, et sa désignation y est obligatoire "
             "(art. R321-4 du code pénal). Tant que la case est cochée, la "
             "nature du métal et le régime de quantité sont exigés à "
             "l'enregistrement. Décocher pour les articles de gestion — "
             "remise, acompte, arrondi, régularisation — qui n'ont rien à "
             "faire au registre.",
    )
    metal_nature = fields.Many2one(
        'metal.nature', string="Nature du métal", ondelete='restrict', index=True,
        help="Renseigné pour tout objet en métal précieux. Laissé vide sur les "
             "articles de gestion (remise, arrondi, acompte, régularisation), "
             "qui n'ont pas à figurer au livre de police. La liste des natures "
             "se complète librement.",
    )
    metal_fineness = fields.Float(
        string="Titre (millièmes)", digits=(5, 1),
        help="Titre légal du métal, en millièmes : 750 pour l'or 18 carats, "
             "900 pour les pièces de l'Union latine, 999 pour un lingot. "
             "Vide si l'article regroupe des titres hétérogènes.",
    )
    metal_quantity_mode = fields.Selection(
        MODE_SELECTION, string="Régime de quantité",
        help="Détermine comment le poids d'une ligne d'achat se déduit de sa "
             "quantité. Renseigner ce champ suffit à faire entrer l'article "
             "dans le périmètre du livre de police.",
    )
    metal_unit_weight = fields.Float(
        string="Poids unitaire (g)", digits=(12, 4),
        help="Poids d'une pièce ou d'un lingotin, en grammes. Requis pour le "
             "régime « à la pièce », sans objet pour les autres.",
    )
    metal_is_object = fields.Boolean(
        string="Objet soumis au livre de police", compute='_compute_metal_is_object',
        store=True,
        help="Vrai dès qu'un régime de quantité est renseigné.",
    )
    metal_weight_undetermined = fields.Boolean(
        string="Poids non déductible", compute='_compute_metal_is_object', store=True,
        help="Objet en métal dont le poids ne peut pas se déduire de la "
             "quantité : lot hétérogène, ou pièce dont le poids unitaire "
             "reste à renseigner. Le poids devra être saisi ligne à ligne.",
    )

    # Un bien est présumé soumis au registre ; un service ne l'est jamais.
    # `readonly=False` laisse le dernier mot à l'utilisateur : la case se
    # décoche à la main, et son choix survit à tout enregistrement ultérieur.
    @api.depends('type')
    def _compute_metal_regulated(self):
        for product in self:
            product.metal_regulated = product.type == 'consu'

    @api.depends('metal_quantity_mode', 'metal_unit_weight')
    def _compute_metal_is_object(self):
        for product in self:
            mode = product.metal_quantity_mode
            product.metal_is_object = bool(mode)
            product.metal_weight_undetermined = bool(mode) and metals.derive_weight(
                mode, product.metal_unit_weight, 1.0) is None
