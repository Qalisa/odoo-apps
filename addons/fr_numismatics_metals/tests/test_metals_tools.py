# -*- coding: utf-8 -*-
"""Tests unitaires de la dérivation du poids (sous-paquet ``tools``).

Sans dépendance Odoo : exécutables sous le runner Odoo (``--test-enable``)
comme en isolation ::

    cd addons && python3 -m unittest fr_numismatics_metals.tests.test_metals_tools
"""

import unittest

try:  # sous Odoo
    from odoo.addons.fr_numismatics_metals.tools import metals
except ImportError:  # exécution isolée (addons/ sur le PYTHONPATH)
    from fr_numismatics_metals.tools import metals


class TestDeriveWeight(unittest.TestCase):
    def test_regime_gramme(self):
        """La quantité *est* le poids."""
        self.assertEqual(metals.derive_weight('gram', None, 18.4), 18.4)

    def test_regime_unitaire(self):
        self.assertAlmostEqual(metals.derive_weight('unit', 6.4516, 5), 32.258)

    def test_poids_non_deductible(self):
        """Lot, article hors métal ou poids unitaire manquant : rien à déduire."""
        self.assertIsNone(metals.derive_weight('lot', None, 1))
        self.assertIsNone(metals.derive_weight(None, None, 1))
        self.assertIsNone(metals.derive_weight('unit', None, 3))
        self.assertIsNone(metals.derive_weight('unit', 0.0, 3))

    def test_quantite_negative(self):
        """Une ligne d'annulation garde un poids de signe cohérent."""
        self.assertAlmostEqual(metals.derive_weight('unit', 6.4516, -2), -12.9032)


class TestPricePerGram(unittest.TestCase):
    """Un simple quotient : aucun seuil, aucune fourchette à tenir à jour."""

    def test_prix_courants(self):
        cases = [
            (18.4 * 70, 18.4, 70.0),        # or 18 carats au gramme
            (600, 6.4516, 93.0),            # 20 Francs Or
            (116840, 1000.0, 116.84),       # lingot d'un kilo
            (2123 * 0.5, 2123.0, 0.5),      # argent en vrac
        ]
        for amount, weight, attendu in cases:
            self.assertAlmostEqual(metals.price_per_gram(amount, weight), attendu,
                                   places=2, msg="%s € / %s g" % (amount, weight))

    def test_saisie_aberrante_saute_aux_yeux(self):
        """Le forfait saisi en quantité 1 se dénonce par son prix au gramme."""
        self.assertAlmostEqual(metals.price_per_gram(3500.0, 1.0), 3500.0)
        self.assertAlmostEqual(metals.price_per_gram(5.0, 123.0), 0.0407, places=4)

    def test_indeterminable(self):
        """Sans poids ou sans montant, il n'y a pas de prix au gramme."""
        self.assertIsNone(metals.price_per_gram(1775.0, 0.0))
        self.assertIsNone(metals.price_per_gram(0.0, 10.0))
        self.assertIsNone(metals.price_per_gram(None, None))

    def test_signe_indifferent(self):
        """Un avoir porte des montants négatifs : le prix reste positif."""
        self.assertAlmostEqual(metals.price_per_gram(-1288.0, -18.4), 70.0)
        self.assertAlmostEqual(metals.price_per_gram(-1288.0, 18.4), 70.0)


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
