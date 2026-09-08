# -*- coding: utf-8 -*-
"""La sortie d'un lot que le stock a déjà renommé.

Ce constat vient d'un cas rencontré en exploitation. Un lot d'argent avait
d'abord été transféré vers un autre établissement, ce qui l'avait qualifié :
« 000001 » était devenu « MONDE/000001 ». Le reste du lot est ensuite reparti
du comptoir de rachat par une livraison ordinaire — et **rien ne s'est
inscrit**. 634,90 g avaient quitté le stock sans quitter le registre.

La sortie retrouve son entrée par le nom du lot. Ce nom avait changé ; celui
que l'inscription porte, figé, ne changeait pas. La recherche ne trouvait
rien, et le code passait à la ligne suivante — ce qu'il fait à bon droit pour
un lot que le registre ne connaît pas, et à tort pour celui-ci.

Le test constate qu'un départ de ce genre s'inscrit désormais, et qu'il se
rattache bien à l'inscription d'origine.
"""

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestSortieLotQualifie(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Societe = cls.env['res.company']
        cls.depart = Societe.create({'name': "Comptoir de rachat"})
        cls.arrivee = Societe.create({'name': "Comptoir voisin"})
        cls.env.user.company_ids |= cls.depart | cls.arrivee
        cls.arrivee.police_responsable_id = cls.env.user
        # Le bon fabriqué à la main plus bas n'est justifié par aucun
        # document : c'est précisément le cas d'exploitation. Seul le droit
        # de correction le laisse passer.
        correction = cls.env.ref(
            'fr_livre_police_metaux.group_livre_police_correction',
            raise_if_not_found=False)
        if correction:
            cls.env.user.groups_id |= correction

        cls.env.ref('stock.stock_location_inter_company').sudo().active = True

        cls.argent = cls.env['product.template'].create({
            'name': "Argent d'essai (gr)",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': cls.env.ref(
                'fr_numismatics_metals.metal_nature_argent').id,
            'metal_fineness': 800.0, 'metal_quantity_mode': 'gram',
        }).product_variant_id

        reprise = cls.env['livre.police.reprise'].with_company(
            cls.depart).create({
                'company_id': cls.depart.id,
                'date_arrete': fields.Date.context_today(cls.env['res.company']),
                'libelle': "Reprise d'essai",
                'ligne_ids': [(0, 0, {
                    'product_id': cls.argent.id, 'quantite': 1000.0,
                    'description': "Voir livre de police manuscrit"})],
            })
        reprise.action_inscrire()
        cls.entree = reprise.inscription_ids

    def test_un_lot_qualifie_qui_repart_s_inscrit_encore(self):
        # Un premier transfert qualifie le lot : « 000001 » devient
        # « COMPT/000001 », et l'inscription garde « 000001 ».
        transfert = self.env['livre.police.transfert'].with_company(
            self.depart).create({
                'company_id': self.depart.id,
                'company_destination_id': self.arrivee.id,
                'motif': "Premier départ, qui renomme le lot.",
                'ligne_ids': [(0, 0, {'inscription_id': self.entree.id,
                                      'quantite': 300.0})],
            })
        transfert.action_expedier()
        transfert.action_receptionner()

        lot = self.entree._lot_du_registre()
        self.assertIn('/', lot.name)
        self.assertEqual(self.entree.numero_lot, '000001')

        # Puis le reste repart par un bon fait à la main, comme au comptoir.
        entrepot = self.env['stock.warehouse'].search(
            [('company_id', '=', self.depart.id)], limit=1)
        bon = self.env['stock.picking'].with_company(self.depart).create({
            'picking_type_id': entrepot.out_type_id.id,
            'location_id': entrepot.lot_stock_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'move_ids': [(0, 0, {
                'name': self.argent.name,
                'product_id': self.argent.id,
                'product_uom_qty': 200.0,
                'location_id': entrepot.lot_stock_id.id,
                'location_dest_id': self.env.ref(
                    'stock.stock_location_customers').id,
            })],
        })
        bon.action_confirm()
        bon.action_assign()
        bon.move_ids.move_line_ids.write({'lot_id': lot.id, 'quantity': 200.0})
        bon.button_validate()

        sortie = self.env['livre.police.ligne'].search([
            ('company_id', '=', self.depart.id),
            ('sens', '=', 'sortie'),
            ('mouvement_stock_id', 'in', bon.move_line_ids.ids),
        ])
        self.assertTrue(
            sortie,
            "Le départ n'a rien inscrit : 200 g ont quitté le stock sans "
            "quitter le registre.")
        self.assertEqual(sortie.entree_id, self.entree)
        self.assertEqual(sortie.quantite, 200.0)
        self.assertEqual(sortie.numero_lot, lot.name)
