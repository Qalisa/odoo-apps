from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        self.ensure_one()

        if self.env.context.get('bypass_confirm_popup'):
            return super().action_confirm()

        # Un devis negatif devient un avoir — c'est un rachat au client ; un
        # devis positif devient une facture. Le sens se lit ici une fois, et
        # la fenetre s'y fie : le champ porte ce qu'il dit.
        sera_un_avoir = self.amount_total < 0

        return {
            'type': 'ir.actions.act_window',
            'name': ("Confirmation - Création d'un avoir" if sera_un_avoir
                     else "🚨 Confirmation - Création d'une facture"),
            'res_model': 'sale.confirm.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_sale_order_id': self.id,
                'default_will_be_refund': sera_un_avoir,
            },
        }
