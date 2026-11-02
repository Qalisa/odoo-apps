from odoo import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    zero_total_document_type = fields.Selection(
        [('out_invoice', 'Facture'), ('out_refund', 'Avoir')],
        string="Document à 0 €", default='out_invoice', required=True,
        copy=False, readonly=True,
    )

    def _can_choose_zero_total_document(self):
        self.ensure_one()
        return self.currency_id.is_zero(self.amount_total) and any(
            line.product_uom_qty < 0
            for line in self.order_line if not line.display_type)

    def _prepare_invoice(self):
        values = super()._prepare_invoice()
        values['sale_zero_total_refund'] = (
            self._can_choose_zero_total_document()
            and self.zero_total_document_type == 'out_refund')
        return values

    def _get_invoice_grouping_keys(self):
        # Deux choix différents ne doivent pas se fondre en une seule pièce.
        return super()._get_invoice_grouping_keys() + ['sale_zero_total_refund']

    def _create_invoices(self, grouped=False, final=False, date=None):
        moves = super()._create_invoices(grouped=grouped, final=final, date=date)
        if final:
            for move in moves.filtered(lambda m: (
                    m.sale_zero_total_refund and m.move_type == 'out_invoice'
                    and m.currency_id.is_zero(m.amount_total))):
                quantities = {
                    line.id: -line.quantity for line in move.invoice_line_ids
                    if line.display_type == 'product'
                }
                move.action_switch_move_type()
                # À zéro, le changement de type natif ne retourne pas les
                # quantités. Il le faut pourtant pour conserver le sens des
                # lignes et le suivi des quantités facturées sur la commande.
                for line in move.invoice_line_ids:
                    if line.id in quantities:
                        line.quantity = quantities[line.id]
        return moves

    def action_confirm(self):
        self.ensure_one()

        if self.env.context.get('bypass_confirm_popup'):
            return super().action_confirm()

        # Hors du choix explicite à zéro, Odoo décide selon le signe du total.
        sera_un_avoir = self.amount_total < 0
        quantites_negatives = any(
            ligne.product_uom_qty < 0
            for ligne in self.order_line if not ligne.display_type)

        return {
            'type': 'ir.actions.act_window',
            'name': ("Confirmation - Document à 0 €"
                     if self._can_choose_zero_total_document()
                     else "Confirmation - Création d'un avoir" if sera_un_avoir
                     else "🚨 Confirmation - Création d'une facture"),
            'res_model': 'sale.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_will_be_refund': sera_un_avoir,
                'default_has_negative_lines': quantites_negatives,
                'default_zero_total_document_type': self.zero_total_document_type,
            },
        }
