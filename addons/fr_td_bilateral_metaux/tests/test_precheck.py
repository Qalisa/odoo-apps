# -*- coding: utf-8 -*-
"""Tests du moteur de pré-contrôle (anomalies §8 du CDC + seuils)."""

import unittest

try:
    from odoo.addons.fr_td_bilateral_metaux.tools import precheck
except ImportError:
    from fr_td_bilateral_metaux.tools import precheck


HEADER = {"annee": "2025", "siret": "12345678900014", "type_decl": "1"}
DECLARANT = {"nom": "AGENCE MOSELLANE DE L'OR", "code_activite": "4778C",
             "code_postal": "57070", "bureau": "METZ", "libelle_commune": "METZ",
             "date_emission": "20260909"}


def _pp(**kw):
    """Vendeur personne physique valide, surchargeable."""
    base = {"nom": "DURAND", "prenoms": "JEAN", "titre": "M",
            "jour_naiss": "12", "mois_naiss": "03", "annee_naiss": "1955",
            "commune_naiss": "METZ", "code_postal": "57000", "bureau": "METZ",
            "montant": 2500}
    base.update(kw)
    return base


class TestValidVendor(unittest.TestCase):
    def test_clean_file_ok(self):
        rep = precheck.check_file(HEADER, DECLARANT, [_pp(), _pp(nom="MARTIN")])
        self.assertEqual(rep["verdict"], "OK")
        self.assertEqual(rep["bloquantes"], [])


class TestBlocking(unittest.TestCase):
    def test_missing_name_is_blocking(self):
        rep = precheck.check_file(HEADER, DECLARANT, [_pp(nom="", prenoms="")])
        self.assertEqual(rep["verdict"], "REJET")
        zones = {f.zone for f in rep["bloquantes"]}
        self.assertIn("Q006/Q014/Q016", zones)

    def test_amount_below_one_is_blocking(self):
        rep = precheck.check_file(HEADER, DECLARANT, [_pp(montant=0.4)])
        self.assertEqual(rep["verdict"], "REJET")

    def test_declarant_bad_siret_blocks(self):
        bad = dict(HEADER, siret="123456789")  # 9 chiffres, siège non corrigé
        rep = precheck.check_file(bad, DECLARANT, [_pp()])
        self.assertEqual(rep["verdict"], "REJET")
        self.assertIn("E002", {f.zone for f in rep["bloquantes"]})


class TestThresholds(unittest.TestCase):
    def test_single_bad_cp_under_5pct_not_rejected(self):
        vendors = [_pp() for _ in range(99)] + [_pp(code_postal="")]
        rep = precheck.check_file(HEADER, DECLARANT, vendors)
        cp = next(s for s in rep["seuils"] if s["zone"] == "Q027")
        self.assertFalse(cp["exceeded"])              # 1 % < 5 %
        self.assertEqual(rep["verdict"], "OK")

    def test_many_bad_cp_over_5pct_rejected(self):
        vendors = [_pp() for _ in range(90)] + [_pp(code_postal="") for _ in range(10)]
        rep = precheck.check_file(HEADER, DECLARANT, vendors)
        cp = next(s for s in rep["seuils"] if s["zone"] == "Q027")
        self.assertTrue(cp["exceeded"])               # 10 % > 5 %
        self.assertEqual(rep["verdict"], "REJET")

    def test_company_without_siret_threshold_1pct(self):
        pm = {"is_company": True, "raison_sociale": "SARL EXEMPLE",
              "code_postal": "54000", "bureau": "NANCY", "montant": 5000}
        vendors = [_pp() for _ in range(99)] + [pm]      # 1 PM sans SIRET sur 100
        rep = precheck.check_file(HEADER, DECLARANT, vendors)
        q005 = next(s for s in rep["seuils"] if s["zone"] == "Q005")
        self.assertEqual(q005["threshold"], 1.0)
        self.assertFalse(q005["exceeded"])              # 1 % n'est pas > 1 %

    def test_foreign_vendor_cp_not_blocking(self):
        etr = _pp(nom="GARCIA", code_postal="99999", bureau="ESPAGNE",
                  foreign=True, commune_naiss="ESPAGNE")
        rep = precheck.check_file(HEADER, DECLARANT, [etr])
        self.assertEqual(rep["verdict"], "OK")


class TestNonBlocking(unittest.TestCase):
    def test_missing_title_is_non_blocking(self):
        rep = precheck.check_file(HEADER, DECLARANT, [_pp(titre="")])
        self.assertEqual(rep["verdict"], "OK")
        self.assertIn("Q013", {f.zone for f in rep["non_bloquantes"]})


class TestPartnerMapping(unittest.TestCase):
    def test_findings_carry_partner_id_for_homonyms(self):
        # Deux homonymes (même nom de famille) -> chacun rattaché à SA fiche.
        didier = _pp(nom="THIERION", prenoms="DIDIER", code_postal="", _partner_id=11)
        sylvie = _pp(nom="THIERION", prenoms="SYLVIE", _partner_id=22)
        rep = precheck.check_file(HEADER, DECLARANT, [didier, sylvie])
        cp = [f for f in rep["findings"] if f.zone == "Q027"]
        self.assertEqual(len(cp), 1)                 # seul Didier a un CP vide
        self.assertEqual(cp[0].partner_id, 11)       # rattaché à Didier, pas Sylvie
        refs = {f.partner_id: f.ref for f in rep["findings"] if f.partner_id}
        self.assertEqual(refs.get(11), "THIERION DIDIER")

if __name__ == "__main__":
    unittest.main(verbosity=2)
