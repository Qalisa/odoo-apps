from odoo import fields, models


class AccountPayment(models.Model):
    _inherit = 'account.payment'

    numero_cheque = fields.Char(string="N° de chèque", copy=False)
    est_journal_cheques = fields.Boolean(related='journal_id.est_journal_cheques')
