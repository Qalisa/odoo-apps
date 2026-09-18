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
        # Une fiche sans prénom ne se crée plus : `partner_firstname` l'interdit
        # depuis que les deux noms sont exigés. Elle existe pourtant — une
        # vingtaine de fiches antérieures au réglage, en production —, et c'est
        # précisément celles-là que ce contrôle doit arrêter au rachat. On les
        # reproduit donc comme elles sont : vidées en base, sans repasser par
        # la contrainte qui ne s'appliquait pas le jour de leur création.
        partner = self._person(**self.id_doc)
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE res_partner SET firstname = NULL WHERE id = %s",
            (partner.id,))
        partner.invalidate_recordset()
        self.assertFalse(partner.firstname)

        with self.assertRaises(UserError):
            self._move(partner)._dmet_check_vendor_completeness()

    def test_missing_birth_country_blocked(self):
        partner = self._person(birth_country_id=False, **self.id_doc)
        with self.assertRaises(UserError):
            self._move(partner)._dmet_check_vendor_completeness()

    def test_company_is_ignored(self):
        # `is_company`, et non `company_type` : c'est lui que
        # `partner_firstname` regarde pour dispenser une société des deux noms.
        company = self.env["res.partner"].create({
            "name": "Fondeur SARL", "is_company": True,
        })
        self._move(company)._dmet_check_vendor_completeness()  # ne lève pas

    def test_out_invoice_is_ignored(self):
        partner = self._person()  # incomplet, mais ce n'est pas un rachat
        move = self.env["account.move"].new({
            "move_type": "out_invoice",
            "partner_id": partner.id,
        })
        move._dmet_check_vendor_completeness()  # ne lève pas
