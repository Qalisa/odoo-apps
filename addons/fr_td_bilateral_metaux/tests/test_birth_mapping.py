# -*- coding: utf-8 -*-

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBirthMapping(TransactionCase):
    """Zone lieu de naissance : le « 99 » (né à l'étranger) se déduit du pays
    de NAISSANCE, pas du pays de l'adresse."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.be = cls.env.ref("base.be")  # Belgique (étranger)

    def _vendor(self, **vals):
        vals.setdefault("name", "Vendeur")
        vals.setdefault("company_type", "person")
        return self.env["res.partner"].create(vals)

    def test_foreign_birth_defaults_dept_99(self):
        # Né à l'étranger, département non saisi -> 99 automatique.
        partner = self._vendor(birth_country_id=self.be.id)
        self.assertEqual(partner._dmet_vendor_dict(100.0)["dept_naiss"], "99")

    def test_foreign_address_does_not_force_99(self):
        # Réside à l'étranger mais né en France (défaut) -> pas de 99.
        partner = self._vendor(country_id=self.be.id)
        self.assertEqual(partner._dmet_vendor_dict(100.0)["dept_naiss"], "")

    def test_explicit_department_wins(self):
        # Un département explicitement saisi prime toujours.
        partner = self._vendor(birth_department="57", birth_country_id=self.be.id)
        self.assertEqual(partner._dmet_vendor_dict(100.0)["dept_naiss"], "57")
