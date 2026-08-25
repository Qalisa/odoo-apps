# -*- coding: utf-8 -*-
"""Quels articles réclament une description au rachat.

Le registre veut « la nature, la provenance et la description des objets
acquis » (art. R321-3 3° du code pénal). Les deux dernières mentions tiennent
dans la même phrase, mais elles ne manquent pas de la même façon.

**La provenance** n'est jamais donnée par la désignation de l'article : elle
est déclarée par le vendeur, et rien d'autre ne la fournit. Elle est donc due
de tout article inscrit au registre, et suit « Soumis au livre de police »
(``metal_regulated``) — aucune case supplémentaire à cocher.

**La description** est déjà donnée par la désignation dès que l'article
désigne un type catalogué : « 20 FRANCS OR » dit la nature, le diamètre, le
millésime et l'effigie mieux qu'une phrase saisie au comptoir. Elle ne
manque que là où l'article ne dit rien de l'objet — un rachat d'or au
gramme, un lot de pièces, une ligne d'argent en vrac.

Ce tri-là ne se devine pas : il se déclare, article par article, par la case
ci-dessous. Une case non cochée n'est pas un oubli du paramétrage, c'est
l'affirmation que la désignation suffit à décrire ce qui entre.
"""

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Le nom du champ dit encore « required » seul : il précède la séparation
    # des deux exigences, et le renommer imposerait une migration de colonne
    # sur une base en production pour un gain de lecture.
    police_description_required = fields.Boolean(
        string="Description des objets obligatoire au rachat",
        help="Coché, un rachat portant cet article ne peut être confirmé ni "
             "comptabilisé sans que les objets soient décrits, ligne par "
             "ligne, sous la désignation de l'article.\n\n"
             "Le modèle officiel du registre réclame en colonne 3 une "
             "« description précise de l'objet (nature, dimensions, style, "
             "signature et éventuellement signes distinctifs) » (arrêté du "
             "15 mai 2020, annexe I). Sur un type catalogué — une pièce, un "
             "lingot d'un poids donné — la désignation de l'article la donne "
             "déjà. Cochez donc là où elle ne dit rien de l'objet : or au "
             "gramme, lot de pièces, argent en vrac.\n\n"
             "LA PROVENANCE NE DÉPEND PAS DE CETTE CASE. Elle est exigée de "
             "tout article coché « Soumis au livre de police » — le registre "
             "veut l'origine de chaque objet acquis (art. R321-3 3° du code "
             "pénal ; CGI, ann. IV, art. 56 J quindecies), et aucune "
             "désignation ne la fournit.",
    )
