# -*- coding: utf-8 -*-
"""Tests d'intégration Odoo : mapping partenaire et construction de bout en bout.

Contrairement aux tests de ``tools`` (purs, hors Odoo), ceux-ci exercent la
couche ORM : projection ``res.partner`` -> dict vendeur, helpers de la
déclaration, et assemblage d'un fichier réel via ces données.
"""

from odoo.tests import TransactionCase, tagged
from odoo.addons.fr_td_bilateral_metaux.tools import dmet as dmet_tools


@tagged('post_install', '-at_install')
class TestDmetIntegration(TransactionCase):

    def test_partner_vendor_mapping(self):
        title_m = self.env.ref('base.res_partner_title_mister',
                               raise_if_not_found=False)
        partner = self.env['res.partner'].create({
            'firstname': 'Jean', 'lastname': 'Durand',
            'is_company': False,
            'title': title_m.id if title_m else False,
            'birthdate': '1955-03-12',
            'street': '5 rue des Jardins', 'zip': '57000', 'city': 'Metz',
            'birth_department': '57', 'birth_city': 'METZ',
        })
        v = partner._dmet_vendor_dict(2500)
        self.assertEqual(v['nom'], 'Durand')
        self.assertEqual(v['prenoms'], 'Jean')
        self.assertEqual(v['montant'], 2500)
        self.assertEqual(v['code_postal'], '57000')
        self.assertEqual(v['jour_naiss'], '12')
        self.assertEqual(v['annee_naiss'], '1955')
        self.assertTrue(v['voie'].startswith('RUE'))
        self.assertFalse(v['is_company'])
        if title_m:
            self.assertEqual(v['titre'], 'M')

    def test_postal_code_department_default_via_partner(self):
        partner = self.env['res.partner'].create({
            'firstname': 'Sophie', 'lastname': 'Martin', 'is_company': False,
            'street': '12 rue Gambetta', 'zip': '54', 'city': 'Nancy',
        })
        v = partner._dmet_vendor_dict(1000)
        self.assertEqual(v['code_postal'], '54000')   # département seul -> +000

    def test_declaration_build_end_to_end(self):
        company = self.env.company
        company.partner_id.write({
            'street': '1 rue de la Gare', 'zip': '57070', 'city': 'Metz',
            'siret': '12345678900014',
        })
        if 'ape' in company._fields:
            company.ape = '4778C'

        decl = self.env['fr.dmet.declaration'].create({
            'millesime': 2025,
            'company_id': company.id,
            'company_ids': [(6, 0, [company.id])],
            'responsable_name': 'DUPONT MARIE, GERANTE',
            'responsable_phone': '0387000000',
            'responsable_email': 'contact@example.fr',
            'remettant_siren': '123456789',
        })

        header = decl._header()
        declarant = decl._declarant_dict()
        total = decl._totalisation_dict()
        self.assertEqual(header['siret'], '12345678900014')
        self.assertEqual(header['annee'], '2025')
        self.assertEqual(total['siren_remettant'], '123456789')

        partner = self.env['res.partner'].create({
            'firstname': 'Sophie', 'lastname': 'Martin', 'is_company': False,
            'street': '12 rue Gambetta', 'zip': '54000', 'city': 'Nancy',
        })
        vendors = [partner._dmet_vendor_dict(1093.5)]

        content = dmet_tools.build_file(header, declarant, vendors, total)
        records = [r for r in content.split('\n') if r]
        self.assertEqual([len(r) for r in records], [550, 550, 550])
        self.assertEqual((records[0][19], records[1][19], records[2][19]),
                         ('E', 'Q', 'T'))
        self.assertEqual(records[0][4:18], '12345678900014')
        # Montant arrondi demi-supérieur : 1093,50 -> 1094, cadré à droite (Q030).
        self.assertEqual(records[1][335:345], '0000001094')

    def test_declaration_precheck_smoke(self):
        """action_precheck ne doit pas planter, même sans aucun avoir (0 vendeur)."""
        decl = self.env['fr.dmet.declaration'].create({
            'millesime': 2025,
            'company_id': self.env.company.id,
            'company_ids': [(6, 0, [self.env.company.id])],
        })
        decl.action_precheck()
        self.assertEqual(decl.state, 'checked')
