# -*- coding: utf-8 -*-
"""Tests unitaires du noyau réglementaire (sous-paquet ``tools``).

Volontairement sans dépendance Odoo : ces tests s'exécutent aussi bien sous le
runner Odoo (``--test-enable``) qu'en isolation ::

    cd addons && python3 -m unittest fr_td_bilateral_metaux.tests.test_dmet_tools
"""

import unittest

try:  # sous Odoo
    from odoo.addons.fr_td_bilateral_metaux.tools import dmet, address, fantoir
    from odoo.addons.fr_td_bilateral_metaux.tools.ascii_tools import (
        to_ascii, is_within_charset,
    )
except ImportError:  # exécution isolée (addons/ sur le PYTHONPATH)
    from fr_td_bilateral_metaux.tools import dmet, address, fantoir
    from fr_td_bilateral_metaux.tools.ascii_tools import to_ascii, is_within_charset


HEADER = {"annee": "2025", "siret": "12345678200028", "type_decl": "1"}
DECLARANT = {"nom": "AGENCE MOSELLANE DE L'OR", "code_activite": "4778C",
             "code_postal": "57070", "bureau": "METZ", "date_emission": "20260909"}
TOTAL = {"responsable": "DUPONT MARIE", "tel": "0387000000",
         "email": "x@example.fr", "siren_remettant": "123456782"}


class TestAsciiTools(unittest.TestCase):
    def test_translitteration(self):
        self.assertEqual(to_ascii("Vandœuvre-lès-Nancy"), "VANDOEUVRE-LES-NANCY")
        self.assertEqual(to_ascii("RENÉ FRANÇOIS"), "RENE FRANCOIS")
        self.assertEqual(to_ascii("Curaçao 5€"), "CURACAO 5E")

    def test_charset_strict(self):
        self.assertTrue(is_within_charset(to_ascii("Œuf à la crème — 5€")))


class TestFixedWidth(unittest.TestCase):
    def _file_records(self, vendors):
        content = dmet.build_file(HEADER, DECLARANT, vendors, TOTAL)
        return [r for r in content.split("\n") if r]

    def test_records_are_550(self):
        recs = self._file_records([{"nom": "DURAND", "prenoms": "JEAN",
                                    "titre": "M", "montant": 2500}])
        self.assertEqual([len(r) for r in recs], [550, 550, 550])

    def test_charset_ok(self):
        recs = self._file_records([{"nom": "RENÉ", "voie": "RUE DE L'ÉGLISE",
                                    "titre": "M", "montant": 10}])
        self.assertTrue(all(is_within_charset(r) for r in recs))

    def test_indicatif_1_19_identical(self):
        recs = self._file_records([{"nom": "A", "montant": 1},
                                   {"nom": "B", "montant": 2}])
        self.assertEqual(len({r[:19] for r in recs}), 1)  # pos 20 = type E/Q/T

    def test_newline_at_551(self):
        raw = dmet.encode_utf8(dmet.build_file(HEADER, DECLARANT,
                                               [{"nom": "A", "montant": 1}], TOTAL))
        self.assertEqual(raw[550:551], b"\n")

    def test_type_markers(self):
        recs = self._file_records([{"nom": "A", "montant": 1}])
        self.assertEqual((recs[0][19], recs[1][19], recs[2][19]), ("E", "Q", "T"))

    def test_amount_zero_padded_and_positioned(self):
        recs = self._file_records([{"nom": "A", "montant": 2500}])
        self.assertEqual(recs[1][335:345], "0000002500")  # Q030, pos 336-345

    def test_count_in_t(self):
        recs = self._file_records([{"nom": "A", "montant": 1},
                                   {"nom": "B", "montant": 2}])
        self.assertEqual(recs[-1][20:30], "0000000002")  # T005, pos 21-30


class TestRoundEuro(unittest.TestCase):
    def test_half_up(self):
        # Arrondi demi-supérieur (et non l'arrondi au pair de round()).
        self.assertEqual(dmet.round_euro(1092.49), 1092)
        self.assertEqual(dmet.round_euro(1092.50), 1093)
        self.assertEqual(dmet.round_euro(1093.50), 1094)
        self.assertEqual(dmet.round_euro(0.5), 1)


class TestAddress(unittest.TestCase):
    def _zone(self, raw):
        return address.parse_street(raw)["voie_zone"].rstrip()

    def test_cdc_voie_examples(self):
        self.assertEqual(self._zone("route nationale 13"), "N    13")
        self.assertEqual(self._zone("avenue des Tilleuls"), "AV   DES TILLEULS")
        self.assertEqual(self._zone("allée du canal"), "ALL  DU CANAL")
        self.assertEqual(self._zone("promenade Beauséjour"), "PROM BEAUSEJOUR")

    def test_number_and_repetition_index(self):
        r = address.parse_street("25 bis rue des Acacias")
        self.assertEqual((r["num_voie"], r["indice_rep"]), ("0025", "B"))
        r = address.parse_street("5-1 rue Traversière")
        self.assertEqual((r["num_voie"], r["indice_rep"]), ("0005", "1"))

    def test_longest_type_match(self):
        self.assertEqual(address.parse_street("chemin rural du Bois")["voie_code"], "CR")
        self.assertEqual(address.parse_street("route departementale 9")["voie_code"], "D")

    def test_unknown_type_blank_code(self):
        r = address.parse_street("Cavée St-Martin")
        self.assertEqual(r["voie_code"], "")
        self.assertEqual(r["voie_zone"][:4], "    ")
        self.assertEqual(r["voie_zone"].strip(), "CAVEE ST-MARTIN")

    def test_left_truncation_keeps_last_word(self):
        z = address.parse_street(
            "rue du Reverend Pere Jean-Charles de la Morinerie")["voie_zone"]
        self.assertEqual(len(z), 26)
        self.assertTrue(z.rstrip().endswith("MORINERIE"))

    def test_postal_code_department_default(self):
        self.assertEqual(address.normalize_cp("54"), "54000")
        self.assertEqual(address.normalize_cp("57000"), "57000")


if __name__ == "__main__":
    unittest.main(verbosity=2)
