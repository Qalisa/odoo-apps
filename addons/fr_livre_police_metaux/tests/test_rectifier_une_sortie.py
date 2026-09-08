# -*- coding: utf-8 -*-
"""Rectifier une sortie, pour dire où le métal est allé.

Ce constat vient d'un cas rencontré en exploitation. Du métal était parti
d'un comptoir vers un autre par une livraison faite à la main : les sorties
s'étaient inscrites, muettes sur leur destination, et les arrivées ont été
régularisées ensuite. Restait à faire dire au registre de départ **où** le
métal était allé — ce qui se fait par une rectification, la seule correction
que le texte admette (CGI, ann. IV, art. 56 J sexdecies, 2° c).

Deux choses s'y opposaient, et aucune ne se voyait.

Le **sens** ne figure pas parmi les mentions rectifiables, et vaut « entrée »
par défaut : la correction d'un départ se serait inscrite comme une arrivée.
Un registre ne peut pas dire d'une sortie qu'elle est une entrée.

Et le **solde** aurait compté deux fois. L'entrée additionne ses sorties ;
l'originale et sa rectification portent le même départ, et le lot serait
sorti deux fois. C'est la règle déjà écrite pour les entrées — une
rectification ne détient rien — qui manquait de ce côté-là.

S'y ajoutait le **jour du mouvement**, qui ne figure pas davantage parmi les
mentions rectifiables : la sortie corrigée ne disait plus quand le métal
était parti, et l'entrée qu'elle soldait perdait sa date de sortie — que le
registre des métaux précieux réclame nommément (CGI, ann. IV,
art. 56 J quindecies).
"""

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRectifierUneSortie(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.depart = cls.env['res.company'].create({'name': "Comptoir d'essai"})
        cls.env.user.company_ids |= cls.depart
        correction = cls.env.ref(
            'fr_livre_police_metaux.group_livre_police_correction',
            raise_if_not_found=False)
        if correction:
            cls.env.user.groups_id |= correction

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

    def _sortir(self, quantite):
        """Un départ ordinaire, fait au comptoir."""
        entrepot = self.env['stock.warehouse'].search(
            [('company_id', '=', self.depart.id)], limit=1)
        clients = self.env.ref('stock.stock_location_customers')
        bon = self.env['stock.picking'].with_company(self.depart).create({
            'picking_type_id': entrepot.out_type_id.id,
            'location_id': entrepot.lot_stock_id.id,
            'location_dest_id': clients.id,
            'move_ids': [(0, 0, {
                'name': self.argent.name,
                'product_id': self.argent.id,
                'product_uom_qty': quantite,
                'location_id': entrepot.lot_stock_id.id,
                'location_dest_id': clients.id,
            })],
        })
        bon.action_confirm()
        bon.action_assign()
        bon.move_ids.move_line_ids.write({
            'lot_id': self.entree._lot_du_registre().id,
            'quantity': quantite,
        })
        bon.button_validate()
        return self.env['livre.police.ligne'].search([
            ('sens', '=', 'sortie'),
            ('mouvement_stock_id', 'in', bon.move_line_ids.ids),
        ])

    def test_une_sortie_rectifiee_reste_une_sortie_et_ne_sort_qu_une_fois(self):
        sortie = self._sortir(300.0)
        self.assertEqual(self.entree.poids_sorti, 300.0)

        mentions = {nom: (sortie[nom].id
                          if sortie._fields[nom].type == 'many2one'
                          else sortie[nom])
                    for nom in self.env['livre.police.rectification']._MENTIONS}
        mentions['transfert_etablissement'] = "Comptoir voisin"
        rectification = sortie._inscrire_rectification(
            mentions,
            "Le métal a été porté au comptoir voisin ; la sortie ne le disait "
            "pas.")

        # Une sortie corrigée reste une sortie.
        self.assertEqual(rectification.sens, 'sortie')
        self.assertEqual(rectification.entree_id, self.entree)
        self.assertEqual(rectification.numero_lot, sortie.numero_lot)
        self.assertEqual(rectification.transfert_etablissement,
                         "Comptoir voisin")
        self.assertEqual(rectification.rectifie_id, sortie)
        self.assertEqual(rectification.date_mouvement, sortie.date_mouvement)

        # Et le lot n'est sorti qu'une fois.
        self.entree.invalidate_recordset()
        self.assertEqual(
            self.entree.poids_sorti, 300.0,
            "L'originale et sa rectification portent le même départ : les "
            "additionner ferait sortir deux fois le même métal.")
        self.assertEqual(self.entree.poids_restant, 700.0)
        self.assertEqual(self.entree.etat_sortie, 'partiel')
