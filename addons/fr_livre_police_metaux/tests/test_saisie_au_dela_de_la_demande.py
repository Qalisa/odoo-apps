# -*- coding: utf-8 -*-
"""On ne fait pas sortir plus de métal que la vente n'en porte.

Constat d'exploitation, sur un bon de 177,50 g d'or 18k. Une ligne de plus
avait été ajoutée dans le détail des opérations, portant le total à 184,30 g.
Rien ne s'y opposait : le stock suffisait, le lot était bien détenu, et le
contrôle de stock laissait passer — il compare au coffre, pas à la vente.

Le dépassement n'est pas qu'une divergence de papier. Une fois la demande
dépassée, Odoo crée chaque ligne suivante à quantité nulle : `selectRecord`,
dans le composant du détail des opérations, calcule ce qui reste à servir et
tombe à zéro. Une ligne nulle ne consomme rien, le lot reste offert au choix,
et on l'ajoute indéfiniment — trois lignes fantômes sur un même lot en sont
sorties, toutes à 0,00.

Le test constate que la saisie est désormais refusée, et qu'elle l'est à la
saisie : le bon ne se remplit plus d'un excédent qu'il faudra défaire.
"""

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSaisieAuDelaDeLaDemande(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.societe = cls.env['res.company'].create({'name': "Comptoir d'essai"})
        cls.env.user.company_ids |= cls.societe

        cls.argent = cls.env['product.template'].create({
            'name': "Argent d'essai (gr)",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': cls.env.ref(
                'fr_numismatics_metals.metal_nature_argent').id,
            'metal_fineness': 800.0, 'metal_quantity_mode': 'gram',
        }).product_variant_id

        reprise = cls.env['livre.police.reprise'].with_company(
            cls.societe).create({
                'company_id': cls.societe.id,
                'date_arrete': fields.Date.context_today(cls.env['res.company']),
                'libelle': "Reprise d'essai",
                'ligne_ids': [(0, 0, {
                    'product_id': cls.argent.id, 'quantite': 1000.0,
                    'description': "Voir livre de police manuscrit"})],
            })
        reprise.action_inscrire()
        cls.entree = reprise.inscription_ids

    def _bon_de_sortie(self, demande):
        entrepot = self.env['stock.warehouse'].search(
            [('company_id', '=', self.societe.id)], limit=1)
        clients = self.env.ref('stock.stock_location_customers')
        bon = self.env['stock.picking'].with_company(self.societe).create({
            'picking_type_id': entrepot.out_type_id.id,
            'location_id': entrepot.lot_stock_id.id,
            'location_dest_id': clients.id,
            'move_ids': [(0, 0, {
                'name': self.argent.name, 'product_id': self.argent.id,
                'product_uom_qty': demande,
                'location_id': entrepot.lot_stock_id.id,
                'location_dest_id': clients.id})],
        })
        bon.action_confirm()
        bon.action_assign()
        return bon

    def test_saisir_plus_que_la_demande_est_refuse(self):
        bon = self._bon_de_sortie(100.0)
        lot = self.entree._lot_du_registre()

        # Le stock ne manque pas — le coffre en porte 1 000. Seule la vente
        # est dépassée : c'est bien elle que ce contrôle protège.
        with self.assertRaises(UserError), self.cr.savepoint():
            bon.move_ids.move_line_ids.write(
                {'lot_id': lot.id, 'quantity': 200.0})

    def test_saisir_la_demande_passe(self):
        """Le contrôle ne gêne pas la sortie ordinaire."""
        bon = self._bon_de_sortie(100.0)
        lot = self.entree._lot_du_registre()
        bon.move_ids.move_line_ids.write({'lot_id': lot.id, 'quantity': 100.0})
        self.assertEqual(bon.move_ids.quantity, 100.0)
