# -*- coding: utf-8 -*-
"""Tests d'intégration : natures, caractéristiques de l'article, poids.

Depuis la 1.1.0, un bien est présumé soumis au registre et ses mentions
(nature, régime de quantité, titre, poids unitaire) sont **exigées à
l'enregistrement** : le registre les veut sur chaque objet (CGI, ann. IV,
art. 56 J quindecies). Les articles qui ne désignent aucun objet acheté —
remise, acompte, arrondi — se déclarent hors registre en décochant la case.

Ces tests posent donc soit un article complet, soit un article explicitement
hors registre, comme le ferait un utilisateur.
"""

from psycopg2 import IntegrityError

from odoo.exceptions import ValidationError
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
            {'name': "Broche vermeil", 'metal_nature': nature.id,
             'metal_quantity_mode': 'gram', 'metal_fineness': 800})
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            with self.cr.savepoint():
                nature.unlink()

    def test_nature_archivable(self):
        """Archiver retire des listes sans toucher aux articles."""
        nature = self.env['metal.nature'].create({'name': "Vermeil"})
        produit = self.env['product.template'].create(
            {'name': "Broche vermeil", 'metal_nature': nature.id,
             'metal_quantity_mode': 'gram', 'metal_fineness': 800})
        nature.active = False
        self.assertEqual(produit.metal_nature, nature)

    def test_comptage_des_articles_archives_compris(self):
        nature = self.env['metal.nature'].create({'name': "Vermeil"})
        self.assertEqual(nature.product_count, 0)
        complet = {'metal_quantity_mode': 'gram', 'metal_fineness': 800}
        produits = self.env['product.template'].create([
            dict(complet, name="Broche vermeil", metal_nature=nature.id),
            dict(complet, name="Chaîne vermeil", metal_nature=nature.id),
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
        # La contrainte ne juge que la saisie : sous `cls.env`, qui est en
        # super-utilisateur, elle se tait volontairement.
        cls.env_utilisateur = cls.env(user=cls.env.ref('base.user_admin'))

    def _product(self, **values):
        return self.env_utilisateur['product.template'].create(
            dict({'name': "Article"}, **values))

    def test_article_declare_hors_registre_reste_sans_caracteristique(self):
        """Décocher la case est la seule façon de garder un bien sans
        caractéristiques : sinon le registre les exige."""
        product = self._product(name="Remise", metal_regulated=False)
        self.assertFalse(product.metal_nature)
        self.assertFalse(product.metal_quantity_mode)
        self.assertFalse(product.metal_is_object)

    def test_bien_incomplet_refuse(self):
        """La vue exige déjà ces champs ; la contrainte les exige aussi
        d'un import ou d'une duplication."""
        with self.assertRaises(ValidationError):
            self._product(name="Chevalière or", type='consu')

    def test_bien_presume_soumis_au_registre(self):
        """Coche automatique à la création d'un bien."""
        product = self._product(
            name="Chevalière or", type='consu', metal_nature=self.or_.id,
            metal_quantity_mode='gram', metal_fineness=750)
        self.assertTrue(product.metal_regulated)

    def test_service_jamais_soumis(self):
        self.assertFalse(self._product(name="Frais de dossier", type='service')
                         .metal_regulated)

    def test_decochage_manuel_persiste(self):
        """Le dernier mot revient à l'utilisateur, y compris après réécriture."""
        product = self._product(name="Remise", type='consu',
                                metal_regulated=False)
        self.assertFalse(product.metal_regulated)
        product.write({'list_price': 12.0})
        self.assertFalse(product.metal_regulated)

    def test_passage_en_bien_recoche(self):
        """Requalifier un service en bien le remet dans le périmètre — et lui
        réclame donc les mentions du registre."""
        product = self._product(name="Reprise", type='service')
        self.assertFalse(product.metal_regulated)
        with self.assertRaises(ValidationError):
            product.type = 'consu'
            # `metal_regulated` est recalculé au vidage du cache : c'est là
            # que la contrainte se prononce, comme à l'enregistrement d'une
            # fiche. Sans ce vidage explicite, le test sortirait du bloc
            # avant que le recalcul ait eu lieu.
            product.flush_recordset()
        product.write({'type': 'consu', 'metal_nature': self.or_.id,
                       'metal_quantity_mode': 'gram', 'metal_fineness': 750})
        self.assertTrue(product.metal_regulated)

    def test_ecran_a_caracteriser_ignore_les_articles_hors_registre(self):
        """Un article décoché ne réclame plus de caractéristiques."""
        domaine = [('metal_regulated', '=', True),
                   '|', ('metal_quantity_mode', '=', False),
                        ('metal_weight_undetermined', '=', True)]
        # Un régime « au lot » laisse le poids à saisir ligne à ligne : c'est
        # désormais le seul cas que cet écran a encore à signaler, la mention
        # manquante étant refusée à l'enregistrement.
        lot = self._product(name="Lot d'argenterie", type='consu',
                            metal_nature=self.argent.id,
                            metal_quantity_mode='lot')
        Tmpl = self.env['product.template']
        self.assertIn(lot, Tmpl.search(domaine))
        lot.metal_regulated = False
        self.assertNotIn(lot, Tmpl.search(domaine))

    def test_regime_renseigne_fait_entrer_dans_le_perimetre(self):
        product = self._product(name="Argent (g)", metal_nature=self.argent.id,
                                metal_quantity_mode='gram', metal_fineness=800)
        self.assertTrue(product.metal_is_object)
        self.assertFalse(product.metal_weight_undetermined)

    def test_piece_sans_poids_unitaire_refusee(self):
        """Régime « à la pièce » sans poids : le poids ne serait pas
        déductible, et le registre l'exige. L'article est refusé tant qu'il
        reste soumis au registre."""
        with self.assertRaises(ValidationError):
            self._product(name="Pièce inconnue", metal_nature=self.or_.id,
                          metal_fineness=900, metal_quantity_mode='unit')
        hors_registre = self._product(
            name="Pièce inconnue", metal_regulated=False,
            metal_nature=self.or_.id, metal_quantity_mode='unit')
        self.assertTrue(hors_registre.metal_weight_undetermined)
        hors_registre.metal_unit_weight = 6.4516
        self.assertFalse(hors_registre.metal_weight_undetermined)

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
                                metal_fineness=916.7, metal_quantity_mode='unit',
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
        cls.hors_metal = Tmpl.create(
            {'name': "Remise", 'metal_regulated': False}).product_variant_id

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
            'metal_fineness': 800, 'metal_quantity_mode': 'gram',
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


@tagged('post_install', '-at_install')
class TestMentionsObligatoiresCatalogue(TransactionCase):
    """Les mentions que le registre exige de chaque objet se tiennent au
    catalogue : « la nature, le nombre, le poids, le titre » (CGI, ann. IV,
    art. 56 J quindecies). Le nombre vient de la ligne d'achat ; les trois
    autres sont des attributs de l'article.
    """

    def setUp(self):
        super().setUp()
        self.or_ = self.env.ref('fr_numismatics_metals.metal_nature_or')
        # Voir `_police_juge_la_saisie` : la contrainte se tait en
        # super-utilisateur, il faut donc écrire sous une identité réelle.
        self.env_utilisateur = self.env(user=self.env.ref('base.user_admin'))

    def _article(self, **valeurs):
        base = {
            'name': "Article de test", 'type': 'consu',
            'metal_nature': self.or_.id, 'metal_quantity_mode': 'gram',
            'metal_fineness': 750.0,
        }
        base.update(valeurs)
        return self.env_utilisateur['product.template'].create(base)

    def test_bien_complet_accepte(self):
        article = self._article()
        self.assertTrue(article.metal_regulated)

    def test_nature_exigee(self):
        with self.assertRaises(ValidationError) as refus:
            self._article(metal_nature=False)
        self.assertIn("nature", str(refus.exception))

    def test_regime_de_quantite_exige(self):
        with self.assertRaises(ValidationError) as refus:
            self._article(metal_quantity_mode=False)
        self.assertIn("régime de quantité", str(refus.exception))

    def test_titre_exige(self):
        with self.assertRaises(ValidationError) as refus:
            self._article(metal_fineness=0.0)
        self.assertIn("titre", str(refus.exception))

    def test_poids_unitaire_exige_au_regime_piece(self):
        with self.assertRaises(ValidationError) as refus:
            self._article(metal_quantity_mode='unit', metal_unit_weight=0.0)
        self.assertIn("poids unitaire", str(refus.exception))

    def test_lot_heterogene_dispense_de_titre(self):
        """Un lot n'a pas de titre unique : en exiger un ferait porter au
        registre une mention fausse."""
        article = self._article(metal_quantity_mode='lot', metal_fineness=0.0)
        self.assertTrue(article.metal_regulated)
        self.assertFalse(article.metal_fineness)

    def test_service_hors_registre(self):
        service = self.env['product.template'].create(
            {'name': "Remise", 'type': 'service'})
        self.assertFalse(service.metal_regulated)

    def test_article_de_gestion_exempte_par_decochage(self):
        """La sortie de secours : un bien qui ne désigne aucun objet."""
        article = self.env['product.template'].create({
            'name': "Arrondi de règlement", 'type': 'consu',
            'metal_regulated': False,
        })
        self.assertFalse(article.metal_regulated)

    def test_retrait_d_une_mention_refuse(self):
        article = self._article()
        with self.assertRaises(ValidationError):
            article.metal_nature = False
