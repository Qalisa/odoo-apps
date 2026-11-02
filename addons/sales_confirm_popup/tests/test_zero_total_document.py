"""Rachat compensé à zéro : le comptoir peut choisir la nature de la pièce."""

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import Form, tagged


@tagged('post_install', '-at_install')
class TestZeroTotalDocument(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.product = cls.env['product.product'].create({
            'name': 'Article de rachat de test', 'type': 'service',
            'invoice_policy': 'order', 'taxes_id': [Command.clear()],
            'property_account_income_id': cls.company_data['default_account_revenue'].id,
        })

    def _order(self, offset=6):
        return self.env['sale.order'].create({
            'partner_id': self.partner_a.id,
            'order_line': [Command.create({
                'product_id': self.product.id,
                'product_uom_qty': quantity, 'price_unit': price,
                'tax_id': [Command.clear()],
            }) for quantity, price in [(-4, 1), (-1, 1), (-1, 1), (1, offset)]],
        })

    def _confirm(self, order, document_type):
        action = order.action_confirm()
        form = Form(self.env['sale.confirm.wizard'].with_context(action['context']))
        self.assertTrue(form.can_choose_zero_total_document)
        form.zero_total_document_type = document_type
        form.save().action_confirm()

    def _check_document(self, document_type):
        order = self._order()
        self._confirm(order, document_type)
        move = order._create_invoices(final=True)
        self.assertEqual(move.move_type, document_type)
        self.assertEqual(move.amount_total, 0)
        quantities = move.invoice_line_ids.sorted('sequence').mapped('quantity')
        self.assertEqual(quantities, [4, 1, 1, -1] if document_type == 'out_refund'
                         else [-4, -1, -1, 1])
        self.assertEqual(order.order_line.mapped('qty_invoiced'), [-4, -1, -1, 1])
        self.assertEqual(order.invoice_status, 'invoiced')
        move.action_post()
        self.assertEqual(move.state, 'posted')
        self.assertEqual(move.amount_total, 0)

    def test_rachat_compense_en_avoir(self):
        self._check_document('out_refund')

    def test_rachat_compense_en_facture(self):
        self._check_document('out_invoice')

    def test_choix_distincts_non_regroupes(self):
        invoice_order, refund_order = self._order(), self._order()
        self._confirm(invoice_order, 'out_invoice')
        self._confirm(refund_order, 'out_refund')
        moves = (invoice_order | refund_order)._create_invoices(final=True)
        self.assertEqual(len(moves), 2)
        self.assertEqual(set(moves.mapped('move_type')), {'out_invoice', 'out_refund'})

    def test_prix_modifie_apres_choix(self):
        order = self._order()
        self._confirm(order, 'out_refund')
        order.order_line[-1].price_unit = 7
        move = order._create_invoices(final=True)
        self.assertEqual(move.move_type, 'out_invoice')
        self.assertEqual(move.amount_total, 1)
