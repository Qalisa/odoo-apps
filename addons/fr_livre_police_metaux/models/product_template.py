# -*- coding: utf-8 -*-
"""Quels articles réclament une description au rachat.

Le registre veut « la nature, la provenance et la description des objets
acquis » (art. R321-3 3° du code pénal). Tous les articles du catalogue n'en
désignent pas : une remise, un acompte, un arrondi, une régularisation ne
sont pas des objets et n'ont rien à décrire.

Le tri ne se devine donc pas — il se déclare, article par article, dans la
fiche. Une case non cochée n'est pas un oubli du paramétrage : c'est
l'affirmation que cet article ne fait entrer aucun objet.
"""

from odoo import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    police_description_required = fields.Boolean(
        string="Description obligatoire au rachat",
        help="Coché, un rachat portant cet article ne peut être confirmé ni "
             "comptabilisé sans que les objets soient décrits, ligne par "
             "ligne.\n\n"
             "Le registre d'objets mobiliers exige de chaque objet acquis sa "
             "nature, sa provenance et sa description (art. R321-3 3° du code "
             "pénal). Le modèle officiel réclame en colonne 3 une "
             "« description précise de l'objet (nature, dimensions, style, "
             "signature et éventuellement signes distinctifs) » (arrêté du "
             "15 mai 2020, annexe I).\n\n"
             "À laisser décoché sur les articles de gestion — remise, "
             "acompte, arrondi, régularisation — qui ne désignent aucun objet "
             "acheté.",
    )
