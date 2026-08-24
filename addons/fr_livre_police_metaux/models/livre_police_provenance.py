# -*- coding: utf-8 -*-
"""D'où vient l'objet — vocabulaire du registre.

L'art. R321-3 3° du code pénal veut de chaque objet acquis « la nature, la
provenance et la description ». La provenance ne se déduit d'aucune donnée
d'Odoo : elle est déclarée par le vendeur, au comptoir, et elle disparaît avec
lui.

Le mécanisme de la liste — ordre, archivage, refus des variantes d'écriture —
est celui de ``livre.police.referentiel`` ; ce fichier ne dit que ce qui
est propre à la provenance : une valeur est employée dès qu'une **pièce
comptabilisée** la porte. Un devis se corrige, une écriture posée ne se
corrige plus (c. pén., art. R321-6 et R321-6-1).
"""

from odoo import models, fields


class LivrePoliceProvenance(models.Model):
    _name = 'livre.police.provenance'
    _inherit = 'livre.police.referentiel'
    _description = "Provenance déclarée au livre de police"

    _police_usage_noms = ("ligne comptabilisée", "lignes comptabilisées")
    _police_effet_renommage = "réécrirait ces lignes du registre"

    usage_count = fields.Integer(
        string="Lignes comptabilisées",
        help="Nombre de lignes de pièces comptabilisées portant cette "
             "provenance. Au-delà de zéro, le libellé est figé.",
    )

    def _police_usage_domain(self):
        return 'account.move.line', [
            ('parent_state', '=', 'posted'),
            ('police_origin_id', 'in', self.ids),
        ]
