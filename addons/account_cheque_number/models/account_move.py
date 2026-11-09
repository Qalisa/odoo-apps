from odoo import models


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _compute_payments_widget_reconciled_info(self):
        super()._compute_payments_widget_reconciled_info()
        Paiement = self.env['account.payment'].sudo()
        for move in self:
            widget = move.invoice_payments_widget
            if not widget:
                continue
            for vals in widget['content']:
                vals['numero_cheque'] = Paiement.browse(vals['account_payment_id']).numero_cheque or False
            move.invoice_payments_widget = widget
