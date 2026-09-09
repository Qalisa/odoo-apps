# -*- coding: utf-8 -*-
"""Un rachat se confirme, et sa réception se crée.

Ce constat vient d'un cas rencontré : le contrôle qui refuse à un bon de
sortir plus de métal que la vente n'en porte bloquait tout rachat, dès la
confirmation du devis.

Un rachat se saisit en quantité négative. La règle de flux crée d'abord le
mouvement tel que le devis le dit — demande à −1, source encore le coffre —
puis le retourne en une entrée du client vers le coffre. Le contrôle lisait
cet état intermédiaire et y voyait un dépassement : « 0 saisi pour −1
demandé » est arithmétiquement vrai et ne décrit rien. Aucun métal ne sort
d'un rachat.

Le test s'arrête à la réception créée. Ce qu'elle devient ensuite — le
numéro d'ordre posé à la comptabilisation de l'avoir — se joue ailleurs.
"""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRachatConfirme(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendeur = cls.env['res.partner'].create(
            {'name': "Vendeur de test", 'is_company': False})
        cls.provenance = cls.env['livre.police.provenance'].search([], limit=1)
        cls.lingot = cls.env['product.template'].create({
            'name': "Lingot repris de test",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': cls.env.ref('fr_numismatics_metals.metal_nature_or').id,
            'metal_fineness': 999.0, 'metal_quantity_mode': 'unit',
            'metal_unit_weight': 20.0,
        }).product_variant_id

    def test_le_devis_de_rachat_cree_sa_reception(self):
        devis = self.env['sale.order'].create({
            'partner_id': self.vendeur.id,
            'police_reglement': 'virement',
            'order_line': [(0, 0, {
                'product_id': self.lingot.id,
                'product_uom_qty': -1.0,
                'price_unit': 1000.0,
                'name': "Lingot 20 g repris au comptoir, poinçon lisible.",
                'police_origin_id': self.provenance.id,
            })],
        })
        # Le module de confirmation intercale une fenêtre ; le contexte la
        # saute, comme le fait son propre assistant.
        devis.with_context(bypass_confirm_popup=True).action_confirm()

        self.assertEqual(devis.state, 'sale')
        reception = devis.picking_ids
        self.assertEqual(len(reception), 1)
        self.assertEqual(reception.picking_type_id.code, 'incoming')
        # Le mouvement a été retourné : il entre au coffre, il n'en sort pas.
        mouvement = reception.move_ids
        self.assertEqual(mouvement.product_uom_qty, 1.0)
        self.assertEqual(mouvement.location_dest_id.usage, 'internal')
        self.assertNotEqual(mouvement.location_id.usage, 'internal')
