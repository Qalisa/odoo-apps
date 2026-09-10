# -*- coding: utf-8 -*-
"""Transférer un lot quand le coffre en détient plusieurs du même article.

Ce constat vient d'un cas rencontré en exploitation : un transfert d'un seul
lot d'argent, prêt depuis la veille, refusait de partir. Le message parlait
de vente et de demande dépassée, ce qui ne décrivait rien de ce que le
comptoir faisait.

L'expédition désigne ses lots à la main — le registre ne transfère pas « 54 g
d'argent », il transfère le lot 000040 et lui seul. Mais Odoo a déjà réservé
à la confirmation, en prenant le lot qui lui tombait sous la main. Le ménage
qui écarte l'intrus se faisait **après** la saisie : le temps d'une écriture,
le mouvement portait les deux jeux de lignes, soit le double de ce que le bon
demandait, et le contrôle qui refuse de sortir plus que la demande y voyait
un dépassement.

Le cas ne se produit qu'avec plusieurs lots du même article : avec un seul,
Odoo réserve celui-là même que le transfert nomme, la ligne est reprise au
lieu d'être créée, et rien ne double. C'est pourquoi le test d'à côté, qui
n'en pose qu'un, ne l'a jamais vu.
"""

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTransfertUnLotParmiPlusieurs(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Societe = cls.env['res.company']
        cls.depart = Societe.create({'name': "Comptoir qui expédie"})
        cls.arrivee = Societe.create({'name': "Comptoir qui reçoit"})
        cls.env.user.company_ids |= cls.depart | cls.arrivee
        cls.env.ref('stock.stock_location_inter_company').sudo().active = True

        cls.argent = cls.env['product.template'].create({
            'name': "Argent d'essai (gr)",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': cls.env.ref(
                'fr_numismatics_metals.metal_nature_argent').id,
            'metal_fineness': 800.0, 'metal_quantity_mode': 'gram',
        }).product_variant_id

        # Deux lots du même article : c'est toute la condition du cas.
        reprise = cls.env['livre.police.reprise'].with_company(cls.depart).create({
            'company_id': cls.depart.id,
            'date_arrete': fields.Date.context_today(cls.env['res.company']),
            'libelle': "Reprise d'essai",
            'ligne_ids': [
                (0, 0, {'product_id': cls.argent.id, 'quantite': 900.0,
                        'description': "Voir livre de police manuscrit"}),
                (0, 0, {'product_id': cls.argent.id, 'quantite': 54.4,
                        'description': "Voir livre de police manuscrit"}),
            ],
        })
        reprise.action_inscrire()
        cls.gros, cls.petit = reprise.inscription_ids.sorted('numero_ordre')

    def test_un_seul_lot_part_quand_le_coffre_en_detient_deux(self):
        transfert = self.env['livre.police.transfert'].with_company(
            self.depart).create({
                'company_id': self.depart.id,
                'company_destination_id': self.arrivee.id,
                'motif': "Regroupement avant fonte.",
                'ligne_ids': [(0, 0, {'inscription_id': self.petit.id,
                                      'quantite': 54.4})],
            })

        transfert.action_expedier()
        self.assertEqual(transfert.state, 'expedie')

        # C'est bien le lot nommé qui est parti, et lui seul.
        lignes = transfert.picking_sortie_id.move_line_ids
        self.assertEqual(len(lignes), 1)
        self.assertEqual(lignes.quantity, 54.4)
        self.assertEqual(lignes.lot_id, self.petit._lot_du_registre())

        # L'autre lot n'a pas bougé du coffre — ni en quantité, ni en
        # réservation. Écarter la ligne posée d'office doit rendre le métal
        # libre : une réserve oubliée immobiliserait 54,4 g des 900 sans que
        # rien ne le dise, et le lot se refuserait à la vente suivante.
        quants = self.env['stock.quant'].sudo().search([
            ('lot_id', '=', self.gros._lot_du_registre().id),
            ('company_id', '=', self.depart.id),
            ('location_id.usage', '=', 'internal'),
        ])
        self.assertEqual(sum(quants.mapped('quantity')), 900.0)
        self.assertEqual(sum(quants.mapped('reserved_quantity')), 0.0)
