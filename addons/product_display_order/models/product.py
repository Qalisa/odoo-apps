# -*- coding: utf-8 -*-
from odoo import models


class ProductTemplate(models.Model):
    """Rendre son office au champ « séquence », qu'Odoo déclare sans l'utiliser.

    `product.template.sequence` existe dans le module `product` — colonne
    réelle, valeur 1 par défaut, et une aide qui annonce « donne l'ordre
    d'affichage dans une liste d'articles ». Aucun tri ne s'en sert pourtant :
    les articles sortent dans l'ordre `is_favorite desc, name`, c'est-à-dire
    par ordre alphabétique dès lors que les favoris ne départagent rien.

    Un ordre alphabétique ne dit rien d'un catalogue de métaux : il éparpille
    les lingots entre les pièces, place « 100 FRANCS OR » avant « 10 DOLLARS
    OR » — la collation ignore l'espace et compare `100FRANCSOR` à
    `10DOLLARSOR` — et ne connaît ni les tailles ni les familles. Le comptoir,
    lui, a un ordre en tête.

    On place donc la séquence en tête du tri. Les favoris et le nom demeurent
    derrière, comme départage : tant que personne n'a rien rangé, toutes les
    séquences valent 1 et l'ordre affiché ne change pas d'un iota. Il ne
    bouge qu'au premier glisser-déposer.
    """

    _inherit = "product.template"
    _order = "sequence, is_favorite desc, name"


class ProductProduct(models.Model):
    """Le même tri pour la variante, qui est l'écran de stock.

    La séquence appartient au modèle d'article, pas à la variante : ranger
    une variante range ses sœurs. Un catalogue sans variantes multiples ne
    voit jamais la différence ; un catalogue qui en aurait doit le savoir.
    """

    _inherit = "product.product"
    _order = "sequence, is_favorite desc, default_code, name, id"
