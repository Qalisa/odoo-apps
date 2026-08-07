# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestIdDocumentGate(TransactionCase):
    """Blocage R321-3 : un rachat (out_refund) à un particulier ne peut être
    validé que si la pièce d'identité du vendeur est complète."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.complete = {
            "id_doc_type": "cni",
            "id_doc_number": "123456789",
            "id_doc_issue_date": "2020-01-15",
            "id_doc_issue_place": "Metz",
            "id_doc_authority": "Préfecture de la Moselle",
        }

    def _move(self, partner):
        return self.env["account.move"].new({
            "move_type": "out_refund",
            "partner_id": partner.id,
        })

    def test_incomplete_individual_is_blocked(self):
        partner = self.env["res.partner"].create({
            "name": "Vendeur Particulier",
            "company_type": "person",
        })
        self.assertFalse(partner.id_doc_complete)
        with self.assertRaises(UserError):
            self._move(partner)._dmet_check_vendor_id_document()

    def test_complete_individual_passes(self):
        partner = self.env["res.partner"].create(dict(
            self.complete, name="Vendeur OK", company_type="person",
        ))
        self.assertTrue(partner.id_doc_complete)
        # Ne doit pas lever.
        self._move(partner)._dmet_check_vendor_id_document()

    def test_company_is_ignored(self):
        company = self.env["res.partner"].create({
            "name": "Fondeur SARL",
            "company_type": "company",
        })
        # Personne morale : pas de pièce d'identité requise.
        self._move(company)._dmet_check_vendor_id_document()

    def test_out_invoice_is_ignored(self):
        partner = self.env["res.partner"].create({
            "name": "Client Particulier",
            "company_type": "person",
        })
        move = self.env["account.move"].new({
            "move_type": "out_invoice",
            "partner_id": partner.id,
        })
        # Une vente (facture) n'est pas un rachat -> non concernée.
        move._dmet_check_vendor_id_document()
