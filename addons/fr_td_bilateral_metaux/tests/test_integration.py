# -*- coding: utf-8 -*-
"""Tests d'intégration Odoo : mapping partenaire et construction de bout en bout.

Contrairement aux tests de ``tools`` (purs, hors Odoo), ceux-ci exercent la
couche ORM : projection ``res.partner`` -> dict vendeur, helpers de la
déclaration, et assemblage d'un fichier réel via ces données.
"""

from odoo import fields
from odoo.exceptions import UserError
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
        # Sur une base issue de la production, la société ambiante porte déjà un
        # numéro de TVA dérivé de son SIREN réel ; `l10n_fr_siret` contrôle la
        # cohérence TVA/SIREN et refuserait le SIRET de test. La TVA (inutile au
        # DMET, qui n'exploite que le SIRET) est donc retirée au préalable, en
        # une écriture distincte : `siret` est un champ calculé dont l'inverse
        # alimente `siren`/`nic`, et l'écrire dans la même passe que `vat`
        # évaluerait la contrainte avant la mise à jour du SIREN.
        company.partner_id.vat = False
        company.partner_id.write({
            'street': '1 rue de la Gare', 'zip': '57070', 'city': 'Metz',
            'siret': '12345678200028',
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
            'remettant_siren': '123456782',
        })

        header = decl._header()
        declarant = decl._declarant_dict()
        total = decl._totalisation_dict()
        self.assertEqual(header['siret'], '12345678200028')
        self.assertEqual(header['annee'], '2025')
        self.assertEqual(total['siren_remettant'], '123456782')

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
        self.assertEqual(records[0][4:18], '12345678200028')
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


@tagged('post_install', '-at_install')
class TestVendeurEntiteCommerciale(TransactionCase):
    """Le vendeur déclaré est la société, jamais celui qui vend pour elle.

    Quand une personne morale vend, la personne physique qui s'est présentée
    la représente (livre de police, art. R321-3 2°). La déclarer comme
    vendeuse personne physique serait doublement faux : elle n'a rien vendu
    pour son compte, et le montant échapperait à la société.
    """

    def _avoir(self, partenaire, montant):
        move = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': partenaire.id,
            'invoice_date': fields.Date.to_date('2025-06-15'),
            'date': fields.Date.to_date('2025-06-15'),
            'invoice_line_ids': [(0, 0, {
                'name': "Rachat métal", 'quantity': 1,
                'price_unit': montant, 'tax_ids': [(5, 0, 0)],
            })],
        })
        move.action_post()
        return move

    def setUp(self):
        super().setUp()
        self.societe = self.env['res.partner'].create({
            'name': "Joaillerie Test", 'is_company': True,
            'street': "3 rue Serpenoise", 'zip': '57000', 'city': "Metz",
            'siret': '12345678200028',
        })
        self.gerant = self.env['res.partner'].create({
            'lastname': "Weber", 'firstname': "Paul", 'is_company': False,
            'parent_id': self.societe.id,
        })
        self.vendeuse = self.env['res.partner'].create({
            'lastname': "Muller", 'firstname': "Anne", 'is_company': False,
            'parent_id': self.societe.id,
        })

    def test_contact_de_societe_ne_bloque_pas_la_validation(self):
        """Sans ce correctif, le contrôle « rachat à un particulier »
        réclamait à un salarié sa date et son pays de naissance."""
        move = self._avoir(self.gerant, 1000.0)
        self.assertEqual(move.state, 'posted')

    def test_particulier_reste_controle(self):
        seul = self.env['res.partner'].create({
            'lastname': "Dupont", 'firstname': "Jean", 'is_company': False})
        with self.assertRaises(UserError):
            self._avoir(seul, 1000.0)

    def test_les_ventes_des_contacts_reviennent_a_la_societe(self):
        self._avoir(self.gerant, 1000.0)
        self._avoir(self.vendeuse, 500.0)
        decl = self.env['fr.dmet.declaration'].create({
            'millesime': 2025,
            'company_id': self.env.company.id,
            'company_ids': [(6, 0, [self.env.company.id])],
        })
        vendeurs = [v for v in decl._collect_vendors()
                    if v['_partner_id'] == self.societe.id]
        self.assertEqual(len(vendeurs), 1, "les deux contacts font un vendeur")
        vendeur = vendeurs[0]
        self.assertTrue(vendeur['is_company'])
        self.assertEqual(vendeur['raison_sociale'], "Joaillerie Test")
        self.assertEqual(vendeur['siret_vendeur'], '12345678200028')
        self.assertAlmostEqual(vendeur['montant'], 1500.0)
        self.assertFalse(
            [v for v in decl._collect_vendors()
             if v['_partner_id'] in (self.gerant.id, self.vendeuse.id)],
            "aucun contact ne doit apparaître comme vendeur")
