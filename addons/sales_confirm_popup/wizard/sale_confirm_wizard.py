from odoo import api, models, fields

class SaleConfirmWizard(models.TransientModel):
    _name = 'sale.confirm.wizard'
    _description = 'Sale Order Confirmation Info'

    sale_order_id = fields.Many2one(
        'sale.order',
        required=True,
        readonly=True
    )

    # Vrai quand le devis deviendra un avoir, c'est-a-dire quand son montant
    # est negatif : le comptoir rachete au client.
    will_be_refund = fields.Boolean(readonly=True)

    # Avec un total positif, les lignes négatives ne suffisent pas à créer un avoir.
    has_negative_lines = fields.Boolean(readonly=True)

    can_choose_zero_total_document = fields.Boolean(
        compute='_compute_can_choose_zero_total_document')
    zero_total_document_type = fields.Selection(
        [('out_invoice', 'Facture'), ('out_refund', 'Avoir')],
        string="Document à créer", default='out_invoice', required=True,
    )

    @api.depends('sale_order_id.amount_total', 'sale_order_id.currency_id',
                 'sale_order_id.order_line.product_uom_qty',
                 'sale_order_id.order_line.display_type')
    def _compute_can_choose_zero_total_document(self):
        for wizard in self:
            wizard.can_choose_zero_total_document = bool(
                wizard.sale_order_id
                and wizard.sale_order_id._can_choose_zero_total_document())

    def action_confirm(self):
        self.ensure_one()
        if self.sale_order_id._can_choose_zero_total_document():
            self.sale_order_id.zero_total_document_type = self.zero_total_document_type
        return self.sale_order_id.with_context(
            bypass_confirm_popup=True
        ).action_confirm()
