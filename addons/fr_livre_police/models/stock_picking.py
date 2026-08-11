# -*- coding: utf-8 -*-
"""La validation d'un transfert inscrit la sortie au journal.

La date de sortie se déduit des mouvements, elle ne se saisit pas. Reste à
l'inscrire au journal chaîné, une fois, au moment où l'objet quitte
réellement le stock — c'est-à-dire à la validation du bon pour relève.
"""

from odoo import models, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        resultat = super().button_validate()
        sortie = self.date_done or fields.Datetime.now()
        for lot in self.move_line_ids.lot_id.filtered('police_registered'):
            # Un objet n'est sorti que lorsqu'il ne reste rien : une relève
            # partielle laisse la ligne du registre ouverte.
            if lot.police_quantity_on_hand or lot.police_exit_date:
                continue
            # Entrée par rachat ou par inventaire d'ouverture : dans les deux
            # cas l'objet est au registre et peut en sortir.
            if not lot.police_event_ids:
                continue
            lot.police_exit_date = sortie
            lot.police_exit_picking_id = self
            lot._police_inscrire('sortie', sortie, description=self.display_name)
        return resultat
