# -*- coding: utf-8 -*-
"""Dupliquer un transfert déjà reçu.

Un transfert parti vers le mauvais comptoir a été dupliqué pour être refait.
La copie, au brouillon, se disait expédiée et reçue, par qui et quand, et
pointait vers les bons de stock de l'original.
"""

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTransfertDuplique(TransactionCase):

    def test_la_copie_n_est_ni_partie_ni_recue(self):
        Societe = self.env['res.company']
        depart = Societe.create({'name': "Comptoir qui expédie"})
        arrivee = Societe.create({'name': "Comptoir qui reçoit"})
        self.env.user.company_ids |= depart | arrivee
        arrivee.police_responsable_id = self.env.user
        self.env.ref('stock.stock_location_inter_company').sudo().active = True
        argent = self.env['product.template'].create({
            'name': "Argent d'essai (gr)",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': self.env.ref(
                'fr_numismatics_metals.metal_nature_argent').id,
            'metal_fineness': 800.0, 'metal_quantity_mode': 'gram',
        }).product_variant_id
        reprise = self.env['livre.police.reprise'].with_company(depart).create({
            'company_id': depart.id,
            'date_arrete': fields.Date.context_today(self.env['res.company']),
            'libelle': "Reprise d'essai",
            'ligne_ids': [(0, 0, {'product_id': argent.id, 'quantite': 900.0,
                                  'description': "Voir livre de police manuscrit"})],
        })
        reprise.action_inscrire()
        transfert = self.env['livre.police.transfert'].with_company(depart).create({
            'company_id': depart.id,
            'company_destination_id': arrivee.id,
            'motif': "Réassort du comptoir.",
            'ligne_ids': [(0, 0, {'inscription_id': reprise.inscription_ids.id,
                                  'quantite': 100.0})],
        })
        transfert.action_expedier()
        transfert.action_receptionner()
        self.assertEqual(transfert.state, 'recu')

        copie = transfert.copy()
        self.assertEqual(copie.state, 'brouillon')
        for champ in ('picking_sortie_id', 'picking_entree_id', 'date_expedition',
                      'expedie_par_id', 'date_reception', 'recu_par_id'):
            self.assertFalse(copie[champ], champ)
