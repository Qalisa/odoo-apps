# -*- coding: utf-8 -*-
"""Un avoir n'est pas toujours un rachat.

Constaté en exploitation : trois avoirs qui annulaient des ventes
(« Annulation commande ») entraient au cumul de leur client comme s'il avait
vendu ce métal au comptoir. Et un rachat annulé par sa contre-pièce y
restait. Pour la même raison, annuler la vente d'un particulier exigeait sa
pièce d'identité, comme s'il avait vendu. La déclaration porte le cumul annuel des achats auprès de chaque
vendeur (CGI, art. 1649 bis) : ni l'un ni l'autre n'est un achat.
"""

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAvoirExtourne(TransactionCase):

    def setUp(self):
        super().setUp()
        self.societe = self.env['res.partner'].create({
            'name': "Joaillerie Test", 'is_company': True,
            'street': "3 rue Serpenoise", 'zip': '57000', 'city': "Metz",
            'siret': '12345678200028',
        })
        self.declaration = self.env['fr.dmet.declaration'].create({
            'millesime': 2025,
            'company_id': self.env.company.id,
            'company_ids': [(6, 0, [self.env.company.id])],
        })

    def _piece(self, type_piece, montant):
        piece = self.env['account.move'].create({
            'move_type': type_piece,
            'partner_id': self.societe.id,
            'invoice_date': fields.Date.to_date('2025-06-15'),
            'date': fields.Date.to_date('2025-06-15'),
            'invoice_line_ids': [(0, 0, {
                'name': "Métal", 'quantity': 1,
                'price_unit': montant, 'tax_ids': [(5, 0, 0)],
            })],
        })
        piece.action_post()
        return piece

    def _extourner(self, piece):
        piece._reverse_moves([{
            'invoice_date': fields.Date.to_date('2025-06-20'),
            'date': fields.Date.to_date('2025-06-20'),
        }], cancel=True)

    def _cumul(self):
        return sum(v['montant'] for v in self.declaration._collect_vendors()
                   if v['_partner_id'] == self.societe.id)

    def test_l_avoir_qui_annule_une_vente_n_est_pas_un_rachat(self):
        self._extourner(self._piece('out_invoice', 800.0))
        self._piece('out_refund', 1000.0)
        self.assertAlmostEqual(self._cumul(), 1000.0)

    def test_un_rachat_extourne_n_est_plus_declare(self):
        self._piece('out_refund', 1000.0)
        self._extourner(self._piece('out_refund', 400.0))
        self.assertAlmostEqual(self._cumul(), 1000.0)

    def test_annuler_la_vente_d_un_particulier(self):
        client = self.env['res.partner'].create(
            {'lastname': "Essai", 'firstname': "Client"})
        vente = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': client.id,
            'invoice_line_ids': [(0, 0, {
                'name': "Métal", 'quantity': 1,
                'price_unit': 500.0, 'tax_ids': [(5, 0, 0)],
            })],
        })
        vente.action_post()
        self._extourner(vente)
        self.assertEqual(vente.reversal_move_ids.state, 'posted')
