from odoo import models, fields

class SaleConfirmWizard(models.TransientModel):
    _name = 'sale.confirm.wizard'
    _description = 'Sale Order Confirmation Info'

    sale_order_id = fields.Many2one(
        'sale.order',
        required=True,
        readonly=True
    )

    # Vrai quand le devis deviendra un avoir, c'est-a-dire quand son
    # montant est negatif : le comptoir rachete au client.
    will_be_refund = fields.Boolean(readonly=True)

    def action_confirm(self):
        return self.sale_order_id.with_context(
            bypass_confirm_popup=True
        ).action_confirm()
