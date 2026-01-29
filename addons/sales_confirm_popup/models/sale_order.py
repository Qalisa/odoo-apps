from odoo import models

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        self.ensure_one()

        if not self.env.context.get('bypass_confirm_popup'):
            will_be_refund = self.amount_total < 0

            return {
                'type': 'ir.actions.act_window',
                'name': "Confirmation - Création d'un avoir" if will_be_refund else "🚨 Confirmation - Création d'une facture",
                'res_model': 'sale.confirm.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_sale_order_id': self.id,
                    'default_will_be_refund': not will_be_refund,
                    'default_info_message': (
                        "Ce devis va être transformé en avoir; vous effectuez ici un rachat au client."
                        if not will_be_refund
                        else "🚨 Ce devis va être transformé en FACTURE; vous allez ici vendre de la marchandise au client."
                    ),
                }
            }

        return super().action_confirm()