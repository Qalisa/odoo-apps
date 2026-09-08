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
from odoo.exceptions import UserError
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

    def _transferer(self, quantite):
        """Un premier départ vers l'autre comptoir, qui qualifie le lot."""
        transfert = self.env['livre.police.transfert'].with_company(
            self.depart).create({
                'company_id': self.depart.id,
                'company_destination_id': self.arrivee.id,
                'motif': "Premier départ, qui renomme le lot.",
                'ligne_ids': [(0, 0, {'inscription_id': self.entree.id,
                                      'quantite': quantite})],
            })
        transfert.action_expedier()
        transfert.action_receptionner()
        return transfert

    def _sortir_a_la_main(self, lot, quantite):
        """Un bon fabriqué au comptoir, sans devis ni transfert."""
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
        return self.env['livre.police.ligne'].search([
            ('company_id', '=', self.depart.id),
            ('sens', '=', 'sortie'),
            ('mouvement_stock_id', 'in', bon.move_line_ids.ids),
        ])

    def test_un_lot_qualifie_qui_repart_s_inscrit_encore(self):
        self._transferer(300.0)

        lot = self.entree._lot_du_registre()
        self.assertIn('/', lot.name)
        self.assertEqual(self.entree.numero_lot, '000001')

        sortie = self._sortir_a_la_main(lot, 200.0)
        self.assertTrue(
            sortie,
            "Le départ n'a rien inscrit : 200 g ont quitté le stock sans "
            "quitter le registre.")
        self.assertEqual(sortie.entree_id, self.entree)
        self.assertEqual(sortie.quantite, 200.0)
        self.assertEqual(sortie.numero_lot, lot.name)

    def test_une_seconde_arrivee_du_meme_lot_se_regularise(self):
        """L'autre moitié du même défaut, constatée sur les mêmes 634,90 g.

        Le comptoir voisin avait déjà reçu une part de ce lot par transfert.
        La régularisation refusait alors la suivante — elle cherchait « une
        entrée de cette origine », et il y en avait une. Mais un lot arrive
        en plusieurs fois, et le registre le dit déjà : deux transferts
        successifs font deux entrées. Ce n'est pas l'origine qui fait
        doublon, c'est la sortie.
        """
        self._transferer(300.0)
        lot = self.entree._lot_du_registre()
        sortie = self._sortir_a_la_main(lot, 200.0)

        Regularisation = self.env['livre.police.regularisation']
        entree = Regularisation.create({
            'sortie_id': sortie.id,
            'company_id': self.arrivee.id,
            'quantite': 200.0,
            'motif': "Porté à la main, sans document de transfert.",
        }).action_inscrire()
        inscription = self.env['livre.police.ligne'].browse(entree['res_id'])
        self.assertEqual(inscription.company_id, self.arrivee)
        self.assertEqual(inscription.quantite, 200.0)
        self.assertEqual(inscription.regularise_id, sortie)

        # Et le stock s'ajoute à ce qui était déjà là. `inventory_quantity`
        # est un comptage : déclarer les seuls 200 g régularisés aurait
        # retranché les 300 g reçus par le transfert au lieu de s'y ajouter.
        entrepot = self.env['stock.warehouse'].search(
            [('company_id', '=', self.arrivee.id)], limit=1)
        detenu = sum(self.env['stock.quant'].sudo().search([
            ('lot_id', '=', lot.id),
            ('location_id', '=', entrepot.lot_stock_id.id),
            ('company_id', '=', self.arrivee.id),
        ]).mapped('quantity'))
        self.assertEqual(detenu, 500.0)

        # La même sortie ne se régularise pas deux fois.
        with self.assertRaises(UserError):
            Regularisation.create({
                'sortie_id': sortie.id,
                'company_id': self.arrivee.id,
                'quantite': 200.0,
                'motif': "Deuxième fois, qui doit être refusée.",
            }).action_inscrire()

    def test_le_repli_sur_le_numero_nu_ne_prend_pas_une_homonyme(self):
        """L'autre comptoir tient lui aussi une inscription « 000001 ».

        Le repli sur le numéro d'ordre nu, introduit pour retrouver
        l'inscription d'un lot qualifié, cherchait les deux noms d'un seul
        coup. Le comptoir qui reçoit tenant sa propre « 000001 » — un tout
        autre métal — c'est elle que la recherche ramenait, et la sortie
        s'inscrivait sous la désignation, le titre et le poids d'un lot
        étranger.
        """
        # Chez celui qui reçoit, une inscription porte le même numéro nu que
        # celle du comptoir de départ — sur un article qui n'a rien à voir.
        # Elle s'inscrit avant le transfert pour prendre le numéro 000001,
        # comme celle du départ.
        nu = self.entree.numero_ordre
        piece = self.env['product.template'].create({
            'name': "Piece d'essai",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': self.env.ref(
                'fr_numismatics_metals.metal_nature_or').id,
            'metal_fineness': 900.0, 'metal_quantity_mode': 'unit',
            'metal_unit_weight': 6.4516,
        }).product_variant_id
        leurre = self.env['livre.police.reprise'].with_company(
            self.arrivee).create({
                'company_id': self.arrivee.id,
                'date_arrete': fields.Date.context_today(self.env['res.company']),
                'libelle': "Reprise du comptoir voisin",
                'ligne_ids': [(0, 0, {
                    'product_id': piece.id, 'quantite': 5.0,
                    'description': "Voir livre de police manuscrit"})],
            })
        leurre.action_inscrire()
        self.assertEqual(leurre.inscription_ids.numero_lot, nu)

        self._transferer(300.0)
        lot = self.entree._lot_du_registre()
        self.assertIn('/', lot.name)
        self.assertEqual(lot.name.rsplit('/', 1)[-1], nu)

        arrivee = self.env['livre.police.ligne'].search([
            ('company_id', '=', self.arrivee.id),
            ('sens', '=', 'entree'),
            ('numero_lot', '=', lot.name)])
        self.assertTrue(arrivee)

        # Le comptoir qui reçoit renvoie sa part : la sortie doit se
        # rattacher au lot qualifié, pas à son homonyme.
        entrepot = self.env['stock.warehouse'].search(
            [('company_id', '=', self.arrivee.id)], limit=1)
        clients = self.env.ref('stock.stock_location_customers')
        bon = self.env['stock.picking'].with_company(self.arrivee).create({
            'picking_type_id': entrepot.out_type_id.id,
            'location_id': entrepot.lot_stock_id.id,
            'location_dest_id': clients.id,
            'move_ids': [(0, 0, {
                'name': self.argent.name, 'product_id': self.argent.id,
                'product_uom_qty': 100.0,
                'location_id': entrepot.lot_stock_id.id,
                'location_dest_id': clients.id})],
        })
        bon.action_confirm()
        bon.action_assign()
        bon.move_ids.move_line_ids.write({'lot_id': lot.id, 'quantity': 100.0})
        bon.button_validate()

        sortie = self.env['livre.police.ligne'].search([
            ('company_id', '=', self.arrivee.id), ('sens', '=', 'sortie'),
            ('mouvement_stock_id', 'in', bon.move_line_ids.ids)])
        self.assertEqual(
            sortie.entree_id, arrivee,
            "La sortie s'est rattachée à l'homonyme du comptoir qui reçoit.")
        self.assertEqual(sortie.designation, arrivee.designation)

    def test_un_lot_ne_sort_pas_plus_qu_il_n_en_contient(self):
        """Constaté sur une copie : 60 000,80 g saisis sur un lot de 6,80 g.

        Odoo laisse le stock passer en négatif, et la sortie s'inscrivait
        sans broncher — l'entrée dont elle se réclamait en annonçait 6,80.
        Une inscription ne se retire pas : le refus vient avant.

        Il vient désormais dès la saisie, et non plus à la validation. Refuser
        au bout laissait le bon se remplir : la réservation dépassait le
        détenu et immobilisait du métal qui n'existe pas, sur un écran qui
        annonçait « Disponible ».
        """
        lot = self.entree._lot_du_registre()
        entrepot = self.env['stock.warehouse'].search(
            [('company_id', '=', self.depart.id)], limit=1)
        clients = self.env.ref('stock.stock_location_customers')
        bon = self.env['stock.picking'].with_company(self.depart).create({
            'picking_type_id': entrepot.out_type_id.id,
            'location_id': entrepot.lot_stock_id.id,
            'location_dest_id': clients.id,
            'move_ids': [(0, 0, {
                'name': self.argent.name, 'product_id': self.argent.id,
                'product_uom_qty': 200.0,
                'location_id': entrepot.lot_stock_id.id,
                'location_dest_id': clients.id})],
        })
        bon.action_confirm()
        bon.action_assign()
        # 5 000 g saisis sur un lot qui en porte 1 000 : la ligne elle-même
        # est refusée. Le savepoint n'est pas de la coquetterie — la contrainte
        # remonte du flush, et sans lui la transaction reste inutilisable :
        # la vérification qui suit ne voudrait plus rien dire.
        with self.assertRaises(UserError), self.cr.savepoint():
            bon.move_ids.move_line_ids.write(
                {'lot_id': lot.id, 'quantity': 5000.0})

        self.assertFalse(self.env['livre.police.ligne'].search([
            ('mouvement_stock_id', 'in', bon.move_line_ids.ids)]),
            "Une sortie impossible s'est tout de même inscrite.")
