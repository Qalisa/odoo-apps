# -*- coding: utf-8 -*-
"""Le poids métal d'une ligne, une fois la pièce comptabilisée.

Ces deux constats appartiennent à `fr_numismatics_metals`, qui calcule le
poids. Ils vivent ici parce qu'ils exigent une pièce **comptabilisée**, et
qu'un rachat ne se comptabilise plus sans les mentions que ce module impose :
la provenance de chaque objet (art. R321-3 3° du code pénal), et le
représentant lorsque le vendeur est une personne morale (2°).

Les laisser chez `fr_numismatics_metals` supposerait de l'y faire dépendre de
son propre dépendant. Odoo le refuse — « Recursion error in modules
dependencies! » — et il aurait raison : c'est bien le registre qui connaît le
catalogue, pas l'inverse.

Le vendeur est ici une personne morale, et non un particulier. Ce n'est pas un
détail de commodité : un rachat à un particulier réclame en plus les mentions
du Cerfa 2093-SD posées par `fr_td_bilateral_metaux`, qui n'est pas une
dépendance de ce module. La personne morale en est dispensée — elle se déclare
par son SIRET — et ce qui reste dû, le représentant et son poste, ce module
sait précisément le fournir.
"""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestPoidsApresComptabilisation(TransactionCase):

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
        argent = cls.env.ref('fr_numismatics_metals.metal_nature_argent')
        Tmpl = cls.env['product.template']
        cls.a_la_piece = Tmpl.create({
            'name': "20 Francs Or", 'metal_nature': or_.id, 'metal_fineness': 900,
            'metal_quantity_mode': 'unit', 'metal_unit_weight': 6.4516,
        }).product_variant_id
        cls.au_lot = Tmpl.create({
            'name': "Lot de pièces Argent", 'metal_nature': argent.id,
            'metal_quantity_mode': 'gram', 'metal_mixed_fineness': True,
        }).product_variant_id

    def _avoir_comptabilise(self, product, qty, price):
        move = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.societe.id,
            'police_representant_id': self.representant.id,
            'police_reglement': 'virement',
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id, 'quantity': qty, 'price_unit': price,
                'police_origin_id': self.provenance.id, 'tax_ids': [(5, 0, 0)]})],
        })
        move.action_post()
        return move

    def test_ligne_comptabilisee_figee(self):
        """Le registre atteste ce qui a été consigné, pas le catalogue du jour."""
        move = self._avoir_comptabilise(self.a_la_piece, 5, 600.0)
        line = move.invoice_line_ids
        self.assertAlmostEqual(line.metal_weight, 32.258, places=3)
        self.a_la_piece.product_tmpl_id.metal_unit_weight = 99.0
        line.invalidate_recordset(['metal_weight'])
        self.assertAlmostEqual(line.metal_weight, 32.258, places=3)

    def test_poids_corrigeable_sur_une_ecriture_comptabilisee(self):
        """Le poids n'est pas comptable : il reste saisissable après validation."""
        move = self._avoir_comptabilise(self.au_lot, 240.0, 1.25)
        line = move.invoice_line_ids
        line.metal_weight = 238.6
        self.assertAlmostEqual(line.metal_weight, 238.6)
        self.assertFalse(line.metal_weight_missing)
        self.assertEqual(move.state, 'posted')
