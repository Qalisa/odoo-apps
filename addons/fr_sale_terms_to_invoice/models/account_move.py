from odoo import api, models
from odoo.tools import is_html_empty


class AccountMove(models.Model):
    _inherit = "account.move"

    def _sti_source_sale_note(self):
        """Retourne le `note` (CGV) du devis à l'origine de la facture/avoir.

        Priorité :
        1. lien natif ligne de facture -> ligne de devis (`sale_line_ids`) ;
        2. à défaut, `invoice_origin` (nom du/des devis).

        Renvoie le premier `note` non vide trouvé, sinon ``False``.
        """
        self.ensure_one()
        orders = self.line_ids.sale_line_ids.order_id
        if not orders and self.invoice_origin:
            names = [n.strip() for n in self.invoice_origin.split(",") if n.strip()]
            if names:
                orders = self.env["sale.order"].search([("name", "in", names)])
        for order in orders:
            if not is_html_empty(order.note):
                return order.note
        return False

    def _sti_carry_sale_terms(self):
        """Reporte les CGV du devis vers `narration` quand elle est vide.

        On ne renseigne que si `narration` est vide : une valeur déjà posée
        (recopie de reversal, saisie manuelle) n'est jamais écrasée, et les CGV
        société par défaut ne sont jamais utilisées.
        """
        for move in self.filtered(
            lambda m: m.move_type in ("out_invoice", "out_refund")
            and is_html_empty(m.narration)
        ):
            note = move._sti_source_sale_note()
            if note:
                move.narration = note

    @api.model_create_multi
    def create(self, vals_list):
        moves = super().create(vals_list)
        moves._sti_carry_sale_terms()
        return moves

    def _post(self, soft=True):
        # Filet de sécurité : certains flux (rachat/TPV, reversal) créent l'avoir
        # sans `narration` ; on garantit les CGV du devis avant comptabilisation.
        self._sti_carry_sale_terms()
        return super()._post(soft=soft)
