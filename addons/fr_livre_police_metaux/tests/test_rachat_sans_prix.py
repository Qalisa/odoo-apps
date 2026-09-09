# -*- coding: utf-8 -*-
"""Ce qu'un rachat inscrit quand son montant n'est pas négatif.

Ce constat vient d'un cas rencontré sur un rachat d'or blanc saisi sans
prix. Odoo ne bascule un devis en avoir que si son montant total est négatif
(`sale.order._create_invoices`) : à 0 €, la pièce reste une facture, et sa
ligne y garde le signe moins.

Le module connaît cette pièce-là — `_police_entree` compte comme une entrée
la facture à quantité négative autant que l'avoir à quantité positive. Mais
le registre recopiait la quantité telle quelle : il inscrivait une entrée de
−115,50 g, quand le stock en détenait bien 115,50.

Un registre ne porte pas de signe. Ses colonnes disent une quantité et un
poids acquis, et le sens de l'opération se lit dans la colonne « sens ».
"""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRachatSansPrix(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.vendeur = cls.env['res.partner'].create(
            {'name': "Vendeur de test", 'is_company': False})
        cls.provenance = cls.env['livre.police.provenance'].search([], limit=1)
        cls.or_blanc = cls.env['product.template'].create({
            'name': "Or blanc de test (gr)",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': cls.env.ref('fr_numismatics_metals.metal_nature_or').id,
            'metal_fineness': 750.0, 'metal_quantity_mode': 'gram',
        }).product_variant_id

    def test_le_registre_inscrit_ce_qui_entre_sans_signe(self):
        devis = self.env['sale.order'].create({
            'partner_id': self.vendeur.id,
            'police_reglement': 'virement',
            'order_line': [(0, 0, {
                'product_id': self.or_blanc.id,
                'product_uom_qty': -115.50,
                'price_unit': 0.0,
                'police_origin_id': self.provenance.id,
            })],
        })
        # Le libellé se recalcule à la pose de l'article : la description des
        # objets s'ajoute donc après, comme au comptoir.
        ligne = devis.order_line
        ligne.name = (ligne.name or '') + "\nDébris blancs, non magnétiques."
        devis.with_context(bypass_confirm_popup=True).action_confirm()

        piece = devis._create_invoices(final=True)
        # Le montant n'étant pas négatif, Odoo n'en fait pas un avoir.
        self.assertEqual(piece.move_type, 'out_invoice')
        self.assertEqual(piece.invoice_line_ids.quantity, -115.50)
        # Le module y voit pourtant une entrée, et il a raison.
        self.assertTrue(piece.invoice_line_ids._police_entree())

        piece.action_post()
        inscription = self.env['livre.police.ligne'].search(
            [('move_line_id', '=', piece.invoice_line_ids.id)])

        self.assertEqual(len(inscription), 1)
        self.assertEqual(inscription.sens, 'entree')
        self.assertEqual(inscription.quantite, 115.50)
        self.assertEqual(inscription.poids, 115.50)
