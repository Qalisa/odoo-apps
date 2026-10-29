# -*- coding: utf-8 -*-
"""Annuler une pièce inscrite depuis « Corriger cette pièce ».

Constaté en parcourant l'écran, avant sa mise en service :

- la case « Annuler aussi le règlement » était toujours refusée. Les
  comptoirs passent leurs règlements directement au compte de banque, et
  Odoo tient un tel règlement pour rapproché dès sa saisie ;
- la contre-pièce d'une vente, rattachée à la commande, retrouvait la sortie
  de la vente et proposait à son tour « Corriger cette pièce ».
"""

from odoo import fields
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestAnnulerUnePiece(TransactionCase):

    def setUp(self):
        super().setUp()
        self.env.user.groups_id |= self.env.ref(
            'fr_livre_police_metaux.group_livre_police_responsable')
        self.argent = self.env['product.template'].create({
            'name': "Argent d'essai (gr)",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': self.env.ref(
                'fr_numismatics_metals.metal_nature_argent').id,
            'metal_fineness': 800.0, 'metal_quantity_mode': 'gram',
        }).product_variant_id

    def _annuler(self, piece, **valeurs):
        f = Form(self.env['livre.police.correction.piece'].with_context(
            default_move_id=piece.id))
        f.nature = 'annulation'
        f.motif = "Erreur de saisie"
        for champ, valeur in valeurs.items():
            setattr(f, champ, valeur)
        f.save().action_continuer()

    def test_annuler_le_reglement_passe_au_compte_de_banque(self):
        societe = self.env['res.partner'].create(
            {'name': "Fondeur d'essai", 'is_company': True})
        rachat = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': societe.id,
            'police_representant_id': self.env['res.partner'].create({
                'name': "Mandataire d'essai", 'parent_id': societe.id,
                'is_company': False, 'function': "Gérant"}).id,
            'police_reglement': 'virement',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.argent.id, 'quantity': 100,
                'price_unit': 1.0, 'tax_ids': [(5, 0, 0)],
                'police_origin_id': self.env[
                    'livre.police.provenance'].search([], limit=1).id})],
        })
        rachat.action_post()
        banque = self.env['account.journal'].search([
            ('type', '=', 'bank'),
            ('company_id', '=', self.env.company.id)], limit=1)
        (banque.inbound_payment_method_line_ids
         | banque.outbound_payment_method_line_ids
         ).payment_account_id = banque.default_account_id
        self.env['account.payment.register'].with_context(
            active_model='account.move', active_ids=rachat.ids,
        ).create({'journal_id': banque.id})._create_payments()
        reglement = rachat._get_reconciled_payments()
        self.assertTrue(reglement.is_matched)

        self._annuler(rachat, annuler_reglement=True)

        self.assertEqual(reglement.state, 'canceled')

    def test_une_vente_annulee_ne_se_corrige_plus(self):
        reprise = self.env['livre.police.reprise'].create({
            'company_id': self.env.company.id,
            'date_arrete': fields.Date.context_today(self.env['res.company']),
            'libelle': "Reprise d'essai",
            'ligne_ids': [(0, 0, {
                'product_id': self.argent.id, 'quantite': 1000.0,
                'description': "Voir livre de police manuscrit"})],
        })
        reprise.action_inscrire()
        vente = self.env['sale.order'].create({
            'partner_id': self.env['res.partner'].create(
                {'name': "Client d'essai", 'is_company': True}).id,
            'order_line': [(0, 0, {'product_id': self.argent.id,
                                   'product_uom_qty': 300, 'price_unit': 1.0,
                                   'tax_id': [(5, 0, 0)]})],
        })
        vente.with_context(bypass_confirm_popup=True).action_confirm()
        bon = vente.picking_ids
        bon.move_ids.move_line_ids.unlink()
        self.env['stock.move.line'].create({
            'move_id': bon.move_ids.id, 'picking_id': bon.id,
            'product_id': self.argent.id, 'quantity': 300,
            'lot_id': reprise.inscription_ids._lot_du_registre().id,
            'location_id': bon.location_id.id,
            'location_dest_id': bon.location_dest_id.id,
        })
        bon.move_ids.picked = True
        bon.button_validate()
        facture = vente._create_invoices()
        facture.action_post()

        self._annuler(facture)

        contre = facture.reversal_move_ids
        self.assertEqual(contre.state, 'posted')
        self.assertFalse(contre.police_corrigeable)
        self.assertFalse(facture.police_corrigeable)
