# -*- coding: utf-8 -*-
"""Qualité du vendeur — mention obligatoire du registre.

L'art. R321-3 1° du code pénal veut « les nom, prénoms, **qualité** et
domicile » de chaque personne qui a vendu. Le modèle officiel de registre
(arrêté du 15 mai 2020, annexe I) intitule la colonne « NOM, PRÉNOM […],
**qualité ou profession**, domicile ou siège social » : les deux mots y sont
donnés pour équivalents.

Le champ vit sur le contact, où il se saisit une fois, mais le registre en
garde une copie à la date de l'opération (`stock.lot.police_seller_qualite_id`)
— un vendeur change de métier, une ligne de registre déjà inscrite ne change
pas.
"""

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    police_qualite_id = fields.Many2one(
        'livre.police.qualite', string="Qualité ou profession",
        ondelete='restrict', index='btree_not_null',
        help="Livre de police (art. R321-3 1°) : qualité ou profession du "
             "vendeur — retraité, salarié, artisan, sans profession… Pour la "
             "personne physique qui vend au nom d'une société, indiquer la "
             "qualité par laquelle elle l'engage : gérant, mandataire.\n\n"
             "Obligatoire pour toute personne physique : sans elle, un rachat "
             "ne peut pas être inscrit au registre.",
    )
