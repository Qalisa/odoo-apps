from odoo import fields, models


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    est_journal_cheques = fields.Boolean(
        string="Journal de chèques",
        help="Un paiement saisi sur ce journal demande le numéro du chèque, "
             "qui s'imprime ensuite sur la facture soldée.")
