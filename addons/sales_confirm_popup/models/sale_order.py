from odoo import models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        self.ensure_one()

        if self.env.context.get('bypass_confirm_popup'):
            return super().action_confirm()

        # C'est le montant, et lui seul, qui decide du document : Odoo ne
        # bascule une facture en avoir que sur un total negatif (voir
        # `sale.order._create_invoices`). La fenetre annonce donc ce qui va
        # reellement se creer, et non ce que la saisie laisse croire.
        sera_un_avoir = self.amount_total < 0
        # D'ou un troisieme cas, qui surprend : des quantites negatives sur un
        # devis dont le total ne l'est pas — un rachat sans prix, ou mele a
        # des lignes vendues. Il deviendra une facture, et il vaut mieux le
        # dire avant que de le decouvrir apres.
        quantites_negatives = any(
            ligne.product_uom_qty < 0
            for ligne in self.order_line if not ligne.display_type)

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
                'default_has_negative_lines': quantites_negatives,
            },
        }
