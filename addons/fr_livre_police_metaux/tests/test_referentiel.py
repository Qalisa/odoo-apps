# -*- coding: utf-8 -*-
"""L'écriture inclusive ne crée pas une deuxième profession.

Sans dépendance Odoo, et exécutable seul — le runner d'Odoo ne ramasse que
les classes qu'il a taguées lui-même, celles-ci lui sont invisibles ::

    cd addons && python3 -m unittest \
        fr_livre_police_metaux.tests.test_referentiel

Le garde-fou des doublons a été écrit pour les provenances, dont aucune ne
porte de parenthèse. Ouvert aux qualités, il a laissé créer « retraite » à
côté de « Retraité(e) » : la terminaison entre parenthèses laissait un jeton
« e » qui suffisait à distinguer les deux clés. Les cas ci-dessous sont ceux
qui ont dû être corrigés.
"""

import unittest

try:  # sous Odoo
    from odoo.addons.fr_livre_police_metaux.tools import referentiel
except ImportError:  # exécution isolée (addons/ sur le PYTHONPATH)
    from fr_livre_police_metaux.tools import referentiel


class TestCleDeComparaison(unittest.TestCase):
    def assertMemeCle(self, *libelles):
        cles = {referentiel.cle_de_comparaison(l) for l in libelles}
        self.assertEqual(len(cles), 1, "clés distinctes : %s" % sorted(cles))

    def test_accord_entre_parentheses(self):
        """« Salarié(e) » est la même profession que « Salarié »."""
        self.assertMemeCle("Retraité(e)", "retraite", "RETRAITÉ (E)",
                           "Retraité")

    def test_accord_suffixe(self):
        """Le point médian et le trait d'union laissent une lettre isolée."""
        self.assertMemeCle("Salarié(e)", "salarié-e", "salarié·e", "SALARIE")

    def test_accord_long(self):
        """Ce que la parenthèse contient ne désigne jamais."""
        self.assertMemeCle("Vendeur(euse)", "vendeur")

    def test_qualites_distinctes_le_restent(self):
        """Corriger l'accord ne devait pas confondre deux vraies qualités."""
        distinctes = ["Salarié(e)", "Salarié(e) habilité(e)", "Étudiant(e)",
                      "Gérant(e)", "Président(e)", "Sans profession",
                      "Profession libérale"]
        cles = [referentiel.cle_de_comparaison(l) for l in distinctes]
        self.assertEqual(len(set(cles)), len(distinctes))


if __name__ == '__main__':  # pragma: no cover
    unittest.main()
