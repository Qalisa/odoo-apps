# -*- coding: utf-8 -*-
"""Ce qu'une part reclassée inscrit quand le stock arrondit son poids.

Ce constat vient d'un cas rencontré au premier essai de l'écran. Une pièce de
3,2258 g reclassée en or blanc cède ce poids-là ; le stock, lui, ne descend
pas sous le centième et en pose 3,23. L'inscription portait alors une
quantité de 3,2300 et un poids de 3,2258 — deux chiffres qui, au gramme,
désignent la même chose et ne s'accordaient pas.

Une inscription qui se contredit elle-même est pire qu'un arrondi : le poids
se déduit donc désormais de ce que le coffre détient réellement. Ce que
l'arrondi déplace reste sous la précision du stock ; ce que la ligne affirme
d'elle-même reste vrai.
"""

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRequalificationPoidsArrondi(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comptoir = cls.env['res.company'].create({'name': "Comptoir d'essai"})
        cls.env.user.company_ids |= cls.comptoir
        or_jaune = cls.env.ref('fr_numismatics_metals.metal_nature_or')
        # Une pièce dont le poids ne tombe pas rond : c'est tout l'objet du
        # test — 3,2258 g ne s'écrivent pas au centième.
        cls.piece = cls.env['product.template'].create({
            'name': "Pièce d'essai 3,2258 g",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': or_jaune.id,
            'metal_fineness': 900.0, 'metal_quantity_mode': 'unit',
            'metal_unit_weight': 3.2258,
        }).product_variant_id
        cls.or_blanc = cls.env['product.template'].create({
            'name': "Or blanc d'essai (gr)",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': or_jaune.id,
            'metal_fineness': 750.0, 'metal_quantity_mode': 'gram',
        }).product_variant_id
        reprise = cls.env['livre.police.reprise'].with_company(cls.comptoir).create({
            'company_id': cls.comptoir.id,
            'date_arrete': fields.Date.context_today(cls.env['res.company']),
            'libelle': "Reprise d'essai",
            'ligne_ids': [(0, 0, {
                'product_id': cls.piece.id, 'quantite': 2.0,
                'description': "Voir livre de police manuscrit"})],
        })
        reprise.action_inscrire()
        cls.entree = reprise.inscription_ids

    def _en_stock(self, inscription):
        lot = inscription._lot_du_registre()
        return sum(self.env['stock.quant'].sudo().search([
            ('lot_id', '=', lot.id),
            ('company_id', '=', self.comptoir.id),
            ('location_id.usage', '=', 'internal'),
        ]).mapped('quantity'))

    def test_la_quantite_et_le_poids_inscrits_s_accordent(self):
        assistant = self.env['livre.police.requalification'].with_company(
            self.comptoir).with_context(
                active_model='livre.police.ligne',
                active_ids=self.entree.ids).create({
                    'product_id': self.or_blanc.id,
                    'quantite': 0.0,
                    'description': "Débris blancs, non magnétiques.",
                    'motif': "Tri : cette pièce n'est pas de l'or jaune.",
                })
        assistant.ligne_ids.quantite_retiree = 1.0
        self.assertAlmostEqual(assistant.poids_retire_total, 3.2258, places=4)

        # Au gramme, l'écran propose le poids retiré comme quantité.
        assistant._onchange_article_au_gramme()
        self.assertAlmostEqual(assistant.quantite, 3.2258, places=4)

        action = assistant.action_requalifier()
        inscrites = self.env['livre.police.ligne'].browse(action['domain'][0][2])
        reclassee = inscrites.filtered(lambda l: not l.rectifie_id)

        # Ce que la ligne dit d'elle-même : au gramme, la quantité est le poids.
        self.assertEqual(reclassee.quantite, reclassee.poids)
        # Et ce qu'elle dit, le coffre le détient.
        self.assertEqual(self._en_stock(reclassee), reclassee.poids)
