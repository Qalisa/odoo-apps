from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleTermsToInvoice(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Vendeur Test"})
        cls.product = cls.env["product.product"].create({
            "name": "Rachat Or",
            "type": "consu",
        })
        cls.cgv = "<p>CGV du devis - conditions de rachat.</p>"

    def _confirmed_order(self, note):
        order = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "note": note,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 100.0,
            })],
        })
        order.action_confirm()
        return order

    def test_refill_from_order_when_empty(self):
        """narration vide -> reprise des CGV du devis via le lien sale_line_ids."""
        order = self._confirmed_order(self.cgv)
        invoice = order._create_invoices()
        # On vide la narration pour simuler un flux qui ne la renseigne pas.
        invoice.narration = False
        invoice._sti_carry_sale_terms()
        self.assertIn("CGV du devis", invoice.narration or "")

    def test_does_not_overwrite_existing_narration(self):
        """Une narration déjà posée n'est jamais écrasée."""
        order = self._confirmed_order(self.cgv)
        invoice = order._create_invoices()
        invoice.narration = "<p>Deja present</p>"
        invoice._sti_carry_sale_terms()
        self.assertIn("Deja present", invoice.narration)
        self.assertNotIn("CGV du devis", invoice.narration)

    def test_fallback_on_invoice_origin(self):
        """Sans lien de ligne, la source est retrouvée via invoice_origin."""
        order = self._confirmed_order(self.cgv)
        invoice = order._create_invoices()
        invoice.narration = False
        # Le helper de résolution doit retrouver le devis par son nom.
        self.assertEqual(invoice.invoice_origin, order.name)
        self.assertIn("CGV du devis", invoice._sti_source_sale_note() or "")

    def test_ignores_empty_order_note(self):
        """Un devis sans CGV ne pose pas de narration."""
        order = self._confirmed_order(False)
        invoice = order._create_invoices()
        invoice.narration = False
        invoice._sti_carry_sale_terms()
        self.assertFalse(invoice.narration)
