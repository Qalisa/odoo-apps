# -*- coding: utf-8 -*-
"""Ce qu'une quantité rectifiée change au registre et au stock.

Ce constat vient d'un cas rencontré : l'état de stock qui a nourri une
reprise d'ouverture surévaluait les quantités d'un comptoir. La rectification
existait — le texte ne connaît qu'elle pour corriger (CGI, ann. IV,
art. 56 J sexdecies, 2° c) — mais elle ne corrigeait que la mention.

Deux choses manquaient, et le registre annonçait 520 g de lingots là où 60 g
restaient : la rectification comptait comme une seconde entrée, et
l'inscription rectifiée continuait de compter pour ce qu'elle avait dit. Le
stock, lui, ne bougeait pas du tout.

Le test lit donc les deux : ce que le registre affirme détenir, et ce que le
stock détient.
"""

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRectificationQuantite(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comptoir = cls.env['res.company'].create({'name': "Comptoir d'essai"})
        cls.env.user.company_ids |= cls.comptoir
        cls.lingot = cls.env['product.template'].create({
            'name': "Lingot d'essai 20 g",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': cls.env.ref('fr_numismatics_metals.metal_nature_or').id,
            'metal_fineness': 999.0, 'metal_quantity_mode': 'unit',
            'metal_unit_weight': 20.0,
        }).product_variant_id
        reprise = cls.env['livre.police.reprise'].with_company(cls.comptoir).create({
            'company_id': cls.comptoir.id,
            'date_arrete': fields.Date.context_today(cls.env['res.company']),
            'libelle': "Reprise d'essai",
            'ligne_ids': [(0, 0, {
                'product_id': cls.lingot.id, 'quantite': 10.0,
                'description': "Voir livre de police manuscrit"})],
        })
        reprise.action_inscrire()
        cls.entree = reprise.inscription_ids

    def _rectifier(self, quantite):
        assistant = self.env['livre.police.rectification.quantite'].with_context(
            active_ids=self.entree.ids,
            active_model='livre.police.ligne').create({
                'motif': "Recomptage : ces lingots n'ont jamais été détenus.",
            })
        assistant.ligne_ids.quantite = quantite
        assistant.action_rectifier()
        self.entree.invalidate_recordset()
        return self.entree.rectifiee_par_ids.sorted('id')[-1]

    def _en_stock(self):
        lot = self.entree._lot_du_registre()
        return sum(self.env['stock.quant'].sudo().search([
            ('lot_id', '=', lot.id),
            ('company_id', '=', self.comptoir.id),
            ('location_id.usage', '=', 'internal'),
        ]).mapped('quantity'))

    def test_le_registre_et_le_stock_suivent_la_rectification(self):
        self.assertEqual(self.entree.poids, 200.0)
        self.assertEqual(self._en_stock(), 10.0)

        rectification = self._rectifier(6.0)

        # Le poids se déduit de la quantité, à la proportion de l'inscrit.
        self.assertEqual(rectification.quantite, 6.0)
        self.assertEqual(rectification.poids, 120.0)
        # L'originale demeure écrite telle quelle...
        self.assertEqual(self.entree.poids, 200.0)
        # ... mais ce qu'elle détient se mesure sur la rectification.
        self.assertEqual(self.entree.poids_restant, 120.0)
        self.assertEqual(self.entree.etat_sortie, 'en_stock')
        # Et la rectification ne détient rien : elle amende, elle ne double pas.
        self.assertEqual(rectification.poids_restant, 0.0)
        self.assertFalse(rectification.etat_sortie)
        # Le stock a suivi du même geste.
        self.assertEqual(self._en_stock(), 6.0)

    def test_rectifiee_a_zero_n_est_plus_en_stock(self):
        self._rectifier(0.0)
        self.assertEqual(self.entree.poids_restant, 0.0)
        self.assertEqual(self._en_stock(), 0.0)
        # Ni en stock, ni sortie : ce métal n'a jamais été détenu.
        self.assertFalse(self.entree.etat_sortie)
        self.assertNotIn(self.entree, self.env['livre.police.ligne'].search(
            [('etat_sortie', '=', 'en_stock')]))
