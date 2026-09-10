# -*- coding: utf-8 -*-
"""Rectifier la quantité d'une sortie rend le métal au coffre.

Ce constat vient d'un cas rencontré : du métal facturé et sorti n'avait pas
été expédié en totalité, et il fallait le dire au registre. La rectification
est la seule correction que le texte admette (CGI, ann. IV,
art. 56 J sexdecies, 2° c) — mais elle retirait le métal une seconde fois au
lieu de le rendre.

`_ajuster_le_stock` recevait l'écart porté à l'inscription et le passait tel
quel au stock. L'équivalence vaut pour une entrée : le coffre détient ce
qu'elle annonce. Sur une sortie, elle dit ce que le coffre a **perdu**, et
les deux sens s'opposent. Une sortie ramenée de 300 à 250 déclare que 50 g
sont restés ; le stock en perdait 50 de plus, et l'erreur comptait double.

S'y ajoutait le lot soldé. Une sortie qui vide son lot n'y laisse rien, et
Odoo supprime le quant tombé à zéro : le métal déclaré resté n'avait plus
d'emplacement où revenir, et l'ajustement refusait sur un message qui parlait
d'un lot « réparti sur 0 emplacements ». Il revient là d'où il est parti, que
la ligne de mouvement porte encore.
"""

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRectifierLaQuantiteDUneSortie(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comptoir = cls.env['res.company'].create({'name': "Comptoir d'essai"})
        cls.env.user.company_ids |= cls.comptoir
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
            cls.comptoir).create({
                'company_id': cls.comptoir.id,
                'date_arrete': fields.Date.context_today(cls.env['res.company']),
                'libelle': "Reprise d'essai",
                'ligne_ids': [(0, 0, {
                    'product_id': cls.argent.id, 'quantite': 1000.0,
                    'description': "Voir livre de police manuscrit"})],
            })
        reprise.action_inscrire()
        cls.entree = reprise.inscription_ids

    def _sortir(self, quantite):
        entrepot = self.env['stock.warehouse'].search(
            [('company_id', '=', self.comptoir.id)], limit=1)
        clients = self.env.ref('stock.stock_location_customers')
        bon = self.env['stock.picking'].with_company(self.comptoir).create({
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

    def _en_stock(self):
        return sum(self.env['stock.quant'].sudo().search([
            ('lot_id', '=', self.entree._lot_du_registre().id),
            ('company_id', '=', self.comptoir.id),
            ('location_id.usage', '=', 'internal'),
        ]).mapped('quantity'))

    def _assistant(self, sortie, quantite):
        assistant = self.env['livre.police.rectification'].with_company(
            self.comptoir).with_context(default_ligne_id=sortie.id).create({
                'ligne_id': sortie.id,
                'motif': "Ce métal n'a pas été expédié.",
            })
        for nom in self.env['livre.police.rectification']._MENTIONS:
            champ = sortie._fields[nom]
            assistant[nom] = (sortie[nom].id if champ.type == 'many2one'
                              else sortie[nom])
        assistant.quantite = quantite
        # Ce que le client déclencherait en quittant le champ.
        assistant._onchange_quantite()
        return assistant

    def _rectifier(self, sortie, quantite):
        self._assistant(sortie, quantite).action_rectifier()

    def test_le_metal_declare_reste_revient_au_coffre(self):
        sortie = self._sortir(300.0)
        self.assertEqual(self._en_stock(), 700.0)

        self._rectifier(sortie, 250.0)

        # 50 g n'étaient pas partis : le coffre les retrouve.
        self.assertEqual(self._en_stock(), 750.0)
        self.entree.invalidate_recordset()
        self.assertEqual(self.entree.poids_sorti, 250.0)
        self.assertEqual(self.entree.poids_restant, 750.0)

    def test_un_lot_solde_retrouve_son_emplacement(self):
        sortie = self._sortir(1000.0)
        self.assertEqual(self._en_stock(), 0.0)
        # Odoo supprime les quants tombés à zéro par une tâche planifiée, qui
        # ne tourne pas sous les tests : on la joue, sans quoi le lot garderait
        # ici un emplacement qu'il n'a plus en exploitation.
        self.env['stock.quant'].sudo()._unlink_zero_quants()
        self.assertFalse(self.env['stock.quant'].sudo().search([
            ('lot_id', '=', self.entree._lot_du_registre().id),
            ('location_id.usage', '=', 'internal'),
        ]))

        self._rectifier(sortie, 900.0)

        self.assertEqual(self._en_stock(), 100.0)

    def test_le_poids_suit_la_quantite_et_ne_peut_la_contredire(self):
        sortie = self._sortir(300.0)

        # Au gramme, la quantité est le poids : l'écran le propose seul.
        assistant = self._assistant(sortie, 250.0)
        self.assertEqual(assistant.poids, 250.0)

        # Et il refuse qu'on les fasse diverger à la main.
        assistant.poids = 300.0
        with self.assertRaises(UserError), self.cr.savepoint():
            assistant.action_rectifier()
