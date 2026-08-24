# -*- coding: utf-8 -*-
"""La qualité du vendeur, recueillie une fois sur sa fiche.

Elle se saisit avec l'état civil et la pièce d'identité — ce sont les mentions
que le registre réclame du vendeur, et le comptoir les recueille au même
moment, devant lui.

Sur la personne morale, le registre veut la qualité du **représentant**
(c. pén., art. R321-3 2°) : c'est donc la fiche de la personne physique qui la
porte, pas celle de la société. Le champ suit cette règle en ne s'affichant
que sur un contact qui n'est pas une société.
"""

from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    police_qualite_id = fields.Many2one(
        'livre.police.qualite', string="Qualité ou profession",
        ondelete='restrict', index='btree_not_null',
        help="Mention obligatoire du livre de police : le registre comporte "
             "« les nom, prénoms, qualité et domicile » de chaque vendeur "
             "(c. pén., art. R321-3 1°), et le modèle officiel intitule la "
             "colonne « qualité ou profession » (arrêté du 15 mai 2020, "
             "annexe I).\n\n"
             "Retraité(e), salarié(e), artisan, sans profession… Pour la "
             "personne qui vend au nom d'une société, indiquer la qualité "
             "par laquelle elle l'engage : gérant(e), mandataire.\n\n"
             "Odoo ne bloque rien si le champ reste vide — c'est le registre "
             "qui sera incomplet.",
    )
