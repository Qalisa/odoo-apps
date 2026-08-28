# -*- coding: utf-8 -*-
"""Le prix qu'un rachat inscrit au registre.

Ce constat vient d'un cas rencontré, pas d'une intention. Le registre
inscrivait `price_subtotal`, ce qui semblait juste et l'est sur la plupart des
lignes. La taxe sur les métaux précieux est pourtant une taxe **négative**,
**incluse dans le prix** et calculée en mode **division** : le sous-total
reconstitue alors le montant d'avant retenue, que personne n'a versé. Un
lingot payé 6 480 € s'inscrivait pour 7 225,20 €.

Le modèle officiel du registre veut le prix d'achat ; c'est ce que le vendeur
a reçu. Le constat tient donc sur une ligne taxée, seule à distinguer les deux
montants.
"""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPrixInscrit(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.societe = cls.env['res.partner'].create(
            {'name': "Fondeur de test", 'is_company': True})
        cls.representant = cls.env['res.partner'].create({
            'name': "Mandataire de test", 'parent_id': cls.societe.id,
            'is_company': False, 'function': "Gérant",
        })
        cls.provenance = cls.env['livre.police.provenance'].search([], limit=1)
        or_ = cls.env.ref('fr_numismatics_metals.metal_nature_or')
        cls.lingot = cls.env['product.template'].create({
            'name': "Lingot de test", 'metal_nature': or_.id,
            'metal_fineness': 999, 'metal_quantity_mode': 'unit',
            'metal_unit_weight': 50.0,
        }).product_variant_id
        # Reproduit la taxe metier : negative, incluse au prix, en division.
        cls.taxe = cls.env['account.tax'].create({
            'name': "TMP de test (11,5 %)",
            'type_tax_use': 'sale',
            'amount_type': 'division',
            'amount': -11.5,
            'price_include_override': 'tax_included',
        })

    def test_le_registre_porte_ce_que_le_vendeur_a_recu(self):
        piece = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.societe.id,
            'police_representant_id': self.representant.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.lingot.id,
                'quantity': 1,
                'price_unit': 6480.0,
                'police_origin_id': self.provenance.id,
                'tax_ids': [(6, 0, self.taxe.ids)],
            })],
        })
        piece.action_post()
        ligne = piece.invoice_line_ids

        # Le piege : les deux montants different, et le plus visible est faux.
        self.assertNotEqual(ligne.price_subtotal, ligne.price_total)

        inscription = self.env['livre.police.ligne'].search(
            [('move_line_id', '=', ligne.id)])
        self.assertEqual(len(inscription), 1)
        self.assertAlmostEqual(inscription.prix, 6480.0, places=2)
