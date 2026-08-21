# -*- coding: utf-8 -*-
"""Tests d'intégration : natures, caractéristiques de l'article, poids.

Les caractéristiques métal se saisissent article par article — le module
n'en impose aucune. Ces tests les posent à la main, comme le ferait un
utilisateur depuis l'onglet « Métal précieux ».
"""

from psycopg2 import IntegrityError

from odoo.tests import TransactionCase, tagged
from odoo.tools import mute_logger


@tagged('post_install', '-at_install')
class TestMetalNature(TransactionCase):
    """Le référentiel des natures appartient au client."""

    USUELLES = ['or', 'argent', 'platine', 'palladium', 'rhodium']

    def test_natures_usuelles_creees_a_l_installation(self):
        noms = []
        for cle in self.USUELLES:
            nature = self.env.ref('fr_numismatics_metals.metal_nature_%s' % cle)
            self.assertTrue(nature.active)
            noms.append(nature.name)
        self.assertEqual(noms, ["Or", "Argent", "Platine", "Palladium", "Rhodium"])

    def test_natures_modifiables_et_creables(self):
        """Le client renomme et ajoute ce qui lui manque."""
        or_ = self.env.ref('fr_numismatics_metals.metal_nature_or')
        or_.name = "Or fin"
        self.assertEqual(or_.name, "Or fin")
        vermeil = self.env['metal.nature'].create({'name': "Vermeil"})
        self.assertTrue(vermeil.id)

    def test_nom_unique(self):
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.cr.savepoint():
                self.env['metal.nature'].create({'name': "Or"})

    def test_nature_utilisee_non_supprimable(self):
        """`ondelete='restrict'` protège le registre d'un référentiel troué."""
        nature = self.env['metal.nature'].create({'name': "Vermeil"})
        self.env['product.template'].create(
            {'name': "Broche vermeil", 'metal_nature': nature.id})
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.cr.savepoint():
                nature.unlink()

    def test_nature_archivable(self):
        """Archiver retire des listes sans toucher aux articles."""
        nature = self.env['metal.nature'].create({'name': "Vermeil"})
        produit = self.env['product.template'].create(
            {'name': "Broche vermeil", 'metal_nature': nature.id})
        nature.active = False
        self.assertEqual(produit.metal_nature, nature)

    def test_comptage_des_articles_archives_compris(self):
        nature = self.env['metal.nature'].create({'name': "Vermeil"})
        self.assertEqual(nature.product_count, 0)
        produits = self.env['product.template'].create([
            {'name': "Broche vermeil", 'metal_nature': nature.id},
            {'name': "Chaîne vermeil", 'metal_nature': nature.id},
        ])
        nature.invalidate_recordset(['product_count'])
        self.assertEqual(nature.product_count, 2)
        produits[0].active = False
        nature.invalidate_recordset(['product_count'])
        self.assertEqual(nature.product_count, 2)


@tagged('post_install', '-at_install')
class TestMetalProduct(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.or_ = cls.env.ref('fr_numismatics_metals.metal_nature_or')
        cls.argent = cls.env.ref('fr_numismatics_metals.metal_nature_argent')

    def _product(self, **values):
        return self.env['product.template'].create(dict({'name': "Article"}, **values))

    def test_article_sans_caracteristique_hors_perimetre(self):
        """Par défaut, un article n'entre pas dans le périmètre du registre."""
        product = self._product(name="Remise")
        self.assertFalse(product.metal_nature)
        self.assertFalse(product.metal_quantity_mode)
        self.assertFalse(product.metal_is_object)

    def test_bien_presume_soumis_au_registre(self):
        """Coche automatique à la création d'un bien."""
        self.assertTrue(self._product(name="Chevalière or", type='consu').metal_regulated)

    def test_service_jamais_soumis(self):
        self.assertFalse(self._product(name="Frais de dossier", type='service')
                         .metal_regulated)

    def test_decochage_manuel_persiste(self):
        """Le dernier mot revient à l'utilisateur, y compris après réécriture."""
        product = self._product(name="Remise", type='consu')
        self.assertTrue(product.metal_regulated)
        product.metal_regulated = False
        product.write({'list_price': 12.0})
        self.assertFalse(product.metal_regulated)

    def test_passage_en_bien_recoche(self):
        """Requalifier un service en bien le remet dans le périmètre."""
        product = self._product(name="Reprise", type='service')
        self.assertFalse(product.metal_regulated)
        product.type = 'consu'
        self.assertTrue(product.metal_regulated)

    def test_ecran_a_caracteriser_ignore_les_articles_hors_registre(self):
        """Un article décoché ne réclame plus de caractéristiques."""
        domaine = [('metal_regulated', '=', True),
                   '|', ('metal_quantity_mode', '=', False),
                        ('metal_weight_undetermined', '=', True)]
        remise = self._product(name="Remise commerciale", type='consu')
        Tmpl = self.env['product.template']
        self.assertIn(remise, Tmpl.search(domaine))
        remise.metal_regulated = False
        self.assertNotIn(remise, Tmpl.search(domaine))

    def test_regime_renseigne_fait_entrer_dans_le_perimetre(self):
        product = self._product(name="Argent (g)", metal_nature=self.argent.id,
                                metal_quantity_mode='gram')
        self.assertTrue(product.metal_is_object)
        self.assertFalse(product.metal_weight_undetermined)

    def test_piece_sans_poids_unitaire_signalee(self):
        """Régime « à la pièce » sans poids : le poids ne sera pas déductible."""
        product = self._product(name="Pièce inconnue", metal_nature=self.or_.id,
                                metal_quantity_mode='unit')
        self.assertTrue(product.metal_is_object)
        self.assertTrue(product.metal_weight_undetermined)
        product.metal_unit_weight = 6.4516
        self.assertFalse(product.metal_weight_undetermined)

    def test_lot_toujours_sans_poids_deductible(self):
        product = self._product(name="Lot de pièces Argent",
                                metal_nature=self.argent.id,
                                metal_quantity_mode='lot')
        self.assertTrue(product.metal_weight_undetermined)

    def test_caracteristiques_modifiables_a_tout_moment(self):
        """Aucun calcul ne verrouille ces champs : ils restent éditables."""
        product = self._product(name="20 Francs Or", metal_nature=self.or_.id,
                                metal_fineness=900, metal_quantity_mode='unit',
                                metal_unit_weight=6.4516)
        product.write({'metal_nature': self.argent.id, 'metal_fineness': 917,
                       'metal_unit_weight': 7.9881})
        self.assertEqual(product.metal_nature, self.argent)
        self.assertEqual(product.metal_fineness, 917)
        self.assertAlmostEqual(product.metal_unit_weight, 7.9881, places=4)

    def test_precision_du_poids_unitaire(self):
        """Le poids unitaire est stocké au dixième de milligramme."""
        product = self._product(name="1/2 Souverain Or", metal_nature=self.or_.id,
                                metal_quantity_mode='unit',
                                metal_unit_weight=3.99402)
        self.assertAlmostEqual(product.metal_unit_weight, 3.9940, places=4)


@tagged('post_install', '-at_install')
class TestMetalWeightOnLines(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.or_ = cls.env.ref('fr_numismatics_metals.metal_nature_or')
        cls.argent = cls.env.ref('fr_numismatics_metals.metal_nature_argent')
        # Personne morale : hors du contrôle de complétude vendeur R321-3 posé
        # par `fr_td_bilateral_metaux`, sans rapport avec le poids testé ici.
        cls.partner = cls.env['res.partner'].create(
            {'name': "Fondeur de test", 'is_company': True})
        Tmpl = cls.env['product.template']
        cls.au_gramme = Tmpl.create({
            'name': "18 carats (18k) Or 750 \u2030 (g)", 'metal_nature': cls.or_.id,
            'metal_fineness': 750, 'metal_quantity_mode': 'gram',
        }).product_variant_id
        cls.a_la_piece = Tmpl.create({
            'name': "20 Francs Or", 'metal_nature': cls.or_.id, 'metal_fineness': 900,
            'metal_quantity_mode': 'unit', 'metal_unit_weight': 6.4516,
        }).product_variant_id
        cls.au_lot = Tmpl.create({
            'name': "Lot de pièces Argent", 'metal_nature': cls.argent.id,
            'metal_quantity_mode': 'lot',
        }).product_variant_id
        cls.hors_metal = Tmpl.create({'name': "Remise"}).product_variant_id

    def _refund(self, product, qty, price):
        return self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id, 'quantity': qty,
                'price_unit': price, 'tax_ids': [(5, 0, 0)]})],
        })

    def test_poids_au_gramme_suit_la_quantite(self):
        move = self._refund(self.au_gramme, 18.4, 70.0)
        self.assertAlmostEqual(move.invoice_line_ids.metal_weight, 18.4)

    def test_poids_a_la_piece_multiplie_le_poids_unitaire(self):
        move = self._refund(self.a_la_piece, 5, 600.0)
        self.assertAlmostEqual(move.invoice_line_ids.metal_weight, 32.258, places=3)

    def test_poids_recalcule_tant_que_le_brouillon_vit(self):
        move = self._refund(self.a_la_piece, 5, 600.0)
        move.invoice_line_ids.quantity = 2
        self.assertAlmostEqual(move.invoice_line_ids.metal_weight, 12.9032, places=4)

    def test_article_hors_metal_sans_poids_ni_anomalie(self):
        move = self._refund(self.hors_metal, 1, -50.0)
        line = move.invoice_line_ids
        self.assertFalse(line.metal_weight)
        self.assertFalse(line.metal_weight_missing)
        self.assertFalse(line.metal_price_per_gram)

    def test_lot_sans_poids_est_signale(self):
        move = self._refund(self.au_lot, 1, 300.0)
        line = move.invoice_line_ids
        self.assertFalse(line.metal_weight)
        self.assertTrue(line.metal_weight_missing)

    def test_poids_saisi_sur_un_lot_est_conserve(self):
        move = self._refund(self.au_lot, 1, 300.0)
        line = move.invoice_line_ids
        line.metal_weight = 238.6
        line.price_unit = 310.0  # une modification quelconque ne doit rien effacer
        self.assertAlmostEqual(line.metal_weight, 238.6)
        self.assertFalse(line.metal_weight_missing)

    def test_ligne_comptabilisee_figee(self):
        """Le registre atteste ce qui a été consigné, pas le catalogue du jour."""
        move = self._refund(self.a_la_piece, 5, 600.0)
        move.action_post()
        line = move.invoice_line_ids
        self.assertAlmostEqual(line.metal_weight, 32.258, places=3)
        self.a_la_piece.product_tmpl_id.metal_unit_weight = 99.0
        line.invalidate_recordset(['metal_weight'])
        self.assertAlmostEqual(line.metal_weight, 32.258, places=3)

    def test_poids_corrigeable_sur_une_ecriture_comptabilisee(self):
        """Le poids n'est pas comptable : il reste saisissable après validation."""
        move = self._refund(self.au_lot, 1, 300.0)
        move.action_post()
        line = move.invoice_line_ids
        line.metal_weight = 238.6
        self.assertAlmostEqual(line.metal_weight, 238.6)
        self.assertFalse(line.metal_weight_missing)
        self.assertEqual(move.state, 'posted')


@tagged('post_install', '-at_install')
class TestMetalPricePerGram(TransactionCase):
    """Le prix au gramme n'est pas paramétré : il découle de la saisie."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.argent = cls.env.ref('fr_numismatics_metals.metal_nature_argent')
        cls.partner = cls.env['res.partner'].create(
            {'name': "Fondeur de test", 'is_company': True})
        cls.au_gramme = cls.env['product.template'].create({
            'name': "Argent (g)", 'metal_nature': cls.argent.id,
            'metal_quantity_mode': 'gram',
        }).product_variant_id

    def _line(self, qty, price):
        return self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': self.au_gramme.id, 'quantity': qty,
                'price_unit': price, 'tax_ids': [(5, 0, 0)]})],
        }).invoice_line_ids

    def test_prix_au_gramme_constate(self):
        line = self._line(2123.0, 0.5)
        self.assertAlmostEqual(line.metal_price_per_gram, 0.5, places=2)

    def test_forfait_saisi_au_gramme_ressort_par_son_prix(self):
        """« Argent (g) » quantité 1 à 3 500 € donne 3 500 €/g : ça se voit."""
        line = self._line(1.0, 3500.0)
        self.assertAlmostEqual(line.metal_price_per_gram, 3500.0, places=2)

    def test_suit_la_correction_du_poids(self):
        line = self._line(1.0, 3500.0)
        line.metal_weight = 2612.0
        self.assertAlmostEqual(line.metal_price_per_gram, 1.34, places=2)

    def test_sans_poids_pas_de_prix_au_gramme(self):
        lot = self.env['product.template'].create({
            'name': "Lot de pièces Argent", 'metal_nature': self.argent.id,
            'metal_quantity_mode': 'lot',
        }).product_variant_id
        line = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.partner.id,
            'invoice_line_ids': [(0, 0, {
                'product_id': lot.id, 'quantity': 1,
                'price_unit': 300.0, 'tax_ids': [(5, 0, 0)]})],
        }).invoice_line_ids
        self.assertFalse(line.metal_price_per_gram)
