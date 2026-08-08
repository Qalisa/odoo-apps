# -*- coding: utf-8 -*-

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestVendorCompletenessGate(TransactionCase):
    """Blocage au rachat : un avoir (out_refund) à un particulier ne peut être
    validé que si nom, prénom, adresse (rue/CP/ville) et pièce d'identité
    (R321-3) du vendeur sont complets."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.id_doc = {
            "id_doc_type": "cni",
            "id_doc_number": "123456789",
            "id_doc_issue_date": "2020-01-15",
            "id_doc_issue_place": "Metz",
            "id_doc_authority": "Préfecture de la Moselle",
        }

    def _person(self, **extra):
        vals = {
            "company_type": "person",
            "firstname": "Jean", "lastname": "Durand",
            "birth_country_id": self.env.ref("base.fr").id,
            "street": "5 rue des Jardins", "zip": "57000", "city": "Metz",
        }
        vals.update(extra)
        return self.env["res.partner"].create(vals)

    def _move(self, partner):
        return self.env["account.move"].new({
            "move_type": "out_refund",
            "partner_id": partner.id,
        })

    def test_complete_vendor_passes(self):
        partner = self._person(**self.id_doc)
        self.assertTrue(partner.id_doc_complete)
        self._move(partner)._dmet_check_vendor_completeness()  # ne lève pas

    def test_missing_id_document_blocked(self):
        partner = self._person()  # nom/prénom/adresse OK mais pas de pièce
        with self.assertRaises(UserError):
            self._move(partner)._dmet_check_vendor_completeness()

    def test_missing_address_blocked(self):
        partner = self._person(zip=False, **self.id_doc)
        with self.assertRaises(UserError):
            self._move(partner)._dmet_check_vendor_completeness()

    def test_missing_firstname_blocked(self):
        partner = self._person(firstname=False, **self.id_doc)
        with self.assertRaises(UserError):
            self._move(partner)._dmet_check_vendor_completeness()

    def test_missing_birth_country_blocked(self):
        partner = self._person(birth_country_id=False, **self.id_doc)
        with self.assertRaises(UserError):
            self._move(partner)._dmet_check_vendor_completeness()

    def test_company_is_ignored(self):
        company = self.env["res.partner"].create({
            "name": "Fondeur SARL", "company_type": "company",
        })
        self._move(company)._dmet_check_vendor_completeness()  # ne lève pas

    def test_out_invoice_is_ignored(self):
        partner = self._person()  # incomplet, mais ce n'est pas un rachat
        move = self.env["account.move"].new({
            "move_type": "out_invoice",
            "partner_id": partner.id,
        })
        move._dmet_check_vendor_completeness()  # ne lève pas
