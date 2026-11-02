from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    sale_zero_total_refund = fields.Boolean(
        string="Avoir à zéro choisi sur le devis", readonly=True, copy=False,
    )
