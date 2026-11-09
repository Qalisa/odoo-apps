from odoo import fields, models


class AccountPaymentRegister(models.TransientModel):
    _inherit = 'account.payment.register'

    numero_cheque = fields.Char(string="N° de chèque")
    est_journal_cheques = fields.Boolean(related='journal_id.est_journal_cheques')

    def _create_payment_vals_from_wizard(self, batch_result):
        vals = super()._create_payment_vals_from_wizard(batch_result)
        if self.est_journal_cheques and self.numero_cheque:
            vals['numero_cheque'] = self.numero_cheque
            # Dans le mémo aussi : c'est lui qu'on lit dans la liste des
            # paiements et au rapprochement bancaire.
            vals['memo'] = f"{vals['memo']} - chèque n° {self.numero_cheque}" if vals.get('memo') \
                else f"Chèque n° {self.numero_cheque}"
        return vals
