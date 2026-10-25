# -*- coding: utf-8 -*-
"""Transférer un lot acheté par un troisième comptoir.

Un lot racheté à Nancy, passé à Metz, devait partir de Metz vers
Mondelange. L'expédition s'est refusée sur une erreur d'accès : elle ne voit
que les deux comptoirs du transfert, et nommer le lot exige de lire son
inscription d'origine, tenue à Nancy. Le refus n'apparaît que sous une
identité réelle — le super-utilisateur ignore les règles d'accès.
"""

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestTransfertLotDUnTroisiemeComptoir(TransactionCase):

    def test_le_lot_part_d_un_comptoir_qui_ne_l_a_pas_achete(self):
        Societe = self.env['res.company']
        achat, passage, arrivee = Societe.create([
            {'name': "Comptoir de rachat"}, {'name': "Comptoir de passage"},
            {'name': "Comptoir d'arrivée"}])
        self.env.ref('stock.stock_location_inter_company').sudo().active = True
        agent = self.env.ref('base.user_admin')
        agent.company_ids |= achat | passage | arrivee
        agent.groups_id |= self.env.ref(
            'fr_livre_police_metaux.group_livre_police_responsable')
        argent = self.env['product.template'].create({
            'name': "Argent d'essai (gr)",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': self.env.ref(
                'fr_numismatics_metals.metal_nature_argent').id,
            'metal_fineness': 800.0, 'metal_quantity_mode': 'gram',
        }).product_variant_id
        reprise = self.env['livre.police.reprise'].with_company(achat).create({
            'company_id': achat.id,
            'date_arrete': fields.Date.context_today(self.env['res.company']),
            'libelle': "Reprise d'essai",
            'ligne_ids': [(0, 0, {'product_id': argent.id, 'quantite': 900.0,
                                  'description': "Voir livre de police manuscrit"})],
        })
        reprise.action_inscrire()

        def transferer(inscription, depart, vers):
            transfert = self.env['livre.police.transfert'].with_user(
                agent).with_company(depart).create({
                    'company_id': depart.id,
                    'company_destination_id': vers.id,
                    'motif': "Réassort du comptoir.",
                    'ligne_ids': [(0, 0, {'inscription_id': inscription.id,
                                          'quantite': 100.0})],
                })
            # Expédier est une autre requête que créer : rien de
            # l'inscription d'origine n'est plus en cache.
            self.env.invalidate_all()
            transfert.action_expedier()
            transfert.action_receptionner()
            return transfert.sudo().inscription_ids.filtered(
                lambda l: l.company_id == vers)

        au_passage = transferer(reprise.inscription_ids, achat, passage)
        a_l_arrivee = transferer(au_passage, passage, arrivee)
        self.assertEqual(a_l_arrivee.quantite, 100.0)
