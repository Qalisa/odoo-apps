# -*- coding: utf-8 -*-
"""Une pièce comptable sait dire si elle relève du registre.

`police_registre_concerne` commande l'affichage de la colonne « Provenance ».
Son calcul a été supprimé par mégarde, en même temps qu'un bloc voisin. Le
champ n'étant pas stocké, rien ne s'en est aperçu : ni l'installation, ni la
mise à jour, ni la suite de tests, dont aucun ne lisait ce champ sur une pièce
comptable. Le manque n'est apparu qu'à la première lecture par l'interface —
l'onglet « Facturation » d'un contact —, sous la forme ::

    AttributeError: 'account.move' object has no attribute
    '_compute_police_registre_concerne'

Un champ calculé dont la méthode n'existe pas ne se signale qu'à la lecture.
Celui-ci se lit donc ici, dans les deux sens qu'il distingue.
"""

from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRegistreConcerne(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = cls.env['res.partner'].create(
            {'name': "Fondeur de test", 'is_company': True})
        cls.piece_or = cls.env['product.template'].create({
            'name': "20 Francs Or",
            'metal_nature': cls.env.ref('fr_numismatics_metals.metal_nature_or').id,
            'metal_fineness': 900, 'metal_quantity_mode': 'unit',
            'metal_unit_weight': 6.4516,
        }).product_variant_id

    def _piece(self, move_type, qty):
        return self.env['account.move'].create({
            'move_type': move_type,
            'partner_id': self.client.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.piece_or.id, 'quantity': qty,
                'price_unit': 600.0, 'tax_ids': [(5, 0, 0)]})],
        })

    def test_avoir_de_rachat_releve_du_registre(self):
        self.assertTrue(self._piece('out_refund', 5).police_registre_concerne)

    def test_facture_de_vente_n_en_releve_pas(self):
        """Une colonne vide et non modifiable se lirait comme un oubli."""
        self.assertFalse(self._piece('out_invoice', 5).police_registre_concerne)
