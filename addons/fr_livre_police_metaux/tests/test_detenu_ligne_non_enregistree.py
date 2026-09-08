# -*- coding: utf-8 -*-
"""Ce que le lot détient, affiché avant que la ligne soit enregistrée.

Constat d'exploitation. Dans « Détail des opérations », « Ajouter une ligne »
n'ouvre pas une ligne vierge : elle fait choisir un quant dans « Enlever
parmi ». Odoo n'en tire le lot, l'emplacement et la société qu'au serveur, à
l'écriture — `_copy_quant_info`, appelée depuis `create` et `write`. Tant que
la ligne n'est pas enregistrée, elle n'a donc rien de tout cela.

La colonne « Détenu » se calculait sur ces trois champs. Elle annonçait zéro
sur chaque ligne qu'on venait d'ajouter, c'est-à-dire au moment précis où
l'opérateur choisit sa quantité — et un zéro se lit comme « il n'y a rien »,
non comme « je ne sais pas encore ».

Le test constate que la colonne lit désormais le quant choisi à défaut de la
ligne, et annonce le vrai détenu avant tout enregistrement.
"""

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDetenuLigneNonEnregistree(TransactionCase):

    def test_ligne_non_enregistree_annonce_le_detenu(self):
        societe = self.env['res.company'].create({'name': "Comptoir d'essai"})
        self.env.user.company_ids |= societe

        argent = self.env['product.template'].create({
            'name': "Argent d'essai (gr)",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': self.env.ref(
                'fr_numismatics_metals.metal_nature_argent').id,
            'metal_fineness': 800.0, 'metal_quantity_mode': 'gram',
        }).product_variant_id

        reprise = self.env['livre.police.reprise'].with_company(societe).create({
            'company_id': societe.id,
            'date_arrete': fields.Date.context_today(self.env['res.company']),
            'libelle': "Reprise d'essai",
            'ligne_ids': [(0, 0, {
                'product_id': argent.id, 'quantite': 1000.0,
                'description': "Voir livre de police manuscrit"})],
        })
        reprise.action_inscrire()

        quant = self.env['stock.quant'].sudo().search([
            ('company_id', '=', societe.id),
            ('product_id', '=', argent.id),
            ('location_id.usage', '=', 'internal'),
        ], limit=1)
        self.assertTrue(quant.lot_id, "la reprise doit avoir créé un lot")

        # Ce que le client web construit au clic sur « Ajouter une ligne » :
        # le quant est renseigné, rien d'autre ne l'est encore.
        ligne = self.env['stock.move.line'].sudo().new({'quant_id': quant.id})
        self.assertFalse(ligne.lot_id, "le lot n'arrive qu'à l'écriture")
        self.assertEqual(ligne.police_quant_detenu, quant.quantity)
