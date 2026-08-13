# -*- coding: utf-8 -*-
"""Le registre suit la matière : entrée au rachat, sortie à la relève."""

import html
import re

from odoo import fields
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestLivrePolice(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.police_start_date = fields.Date.to_date('2026-01-01')
        cls.company.police_sequence_prefix = 'TEST'
        Warehouse = cls.env['stock.warehouse']
        if not Warehouse.search([('company_id', '=', cls.company.id)]):
            Warehouse.create({'name': cls.company.name, 'code': 'TST',
                              'company_id': cls.company.id})
        cls.or_ = cls.env.ref('fr_numismatics_metals.metal_nature_or')
        cls.vendeur = cls.env['res.partner'].create(
            {'name': "Vendeur de test", 'is_company': True})
        cls.fondeur = cls.env['res.partner'].create(
            {'name': "Fondeur de test", 'is_company': True})
        cls.piece = cls.env['product.template'].create({
            'name': "20 Francs Or (test)", 'metal_nature': cls.or_.id,
            'metal_fineness': 900, 'metal_quantity_mode': 'unit',
            'metal_unit_weight': 6.4516,
        })
        cls.remise = cls.env['product.template'].create(
            {'name': "Remise (test)", 'type': 'service'})

    def _rachat(self, qty=5, price=600.0, origine="Succession", produit=None,
                description="Pièces scellées, millésimes 1907 à 1914"):
        """Un rachat tel qu'il se saisit : la ligne, puis la note qui décrit
        les objets. Sans elle, la comptabilisation est refusée (R321-3)."""
        produit = produit or self.piece.product_variant_id
        lignes = [(0, 0, {
            'product_id': produit.id, 'quantity': qty,
            'price_unit': price, 'tax_ids': [(5, 0, 0)],
            'police_origin': origine, 'sequence': 10})]
        if description:
            lignes.append((0, 0, {
                'display_type': 'line_note', 'name': description,
                'sequence': 11}))
        move = self.env['account.move'].create({
            'move_type': 'out_refund',
            'partner_id': self.vendeur.id,
            'invoice_date': fields.Date.to_date('2026-03-10'),
            'date': fields.Date.to_date('2026-03-10'),
            'invoice_line_ids': lignes,
        })
        move.action_post()
        return move

    def _relever(self, lot, qty):
        entrepot = self.env['stock.warehouse'].search(
            [('company_id', '=', self.company.id)], limit=1)
        emplacement = entrepot.lot_stock_id
        clients = self.env.ref('stock.stock_location_customers')
        picking = self.env['stock.picking'].create({
            'partner_id': self.fondeur.id,
            'picking_type_id': entrepot.out_type_id.id,
            'location_id': emplacement.id,
            'location_dest_id': clients.id,
            'origin': "Bon pour relève",
        })
        self.env['stock.move'].create({
            'picking_id': picking.id, 'product_id': lot.product_id.id,
            'product_uom_qty': qty, 'name': lot.product_id.name,
            'location_id': emplacement.id, 'location_dest_id': clients.id,
        })
        picking.action_confirm()
        picking.action_assign()
        for ligne in picking.move_line_ids:
            ligne.lot_id = lot
            ligne.quantity = qty
        picking.button_validate()
        return picking

    # ------------------------------------------------------------------
    # L'article
    # ------------------------------------------------------------------
    def test_article_soumis_est_suivi_en_stock_et_par_lot(self):
        """Sans stock ni lot, ni entrée, ni sortie, ni numéro d'ordre."""
        self.assertTrue(self.piece.metal_regulated)
        self.assertTrue(self.piece.is_storable)
        self.assertEqual(self.piece.tracking, 'lot')

    def test_article_hors_registre_non_force(self):
        """Un service n'entre jamais dans le périmètre du registre."""
        self.assertFalse(self.remise.metal_regulated)
        self.assertFalse(self.remise.is_storable)

    def test_decochage_ne_retire_pas_le_suivi_de_stock(self):
        """Le module ajoute le suivi, il ne le retire jamais.

        Retirer un article du registre ne dit rien de son intérêt en stock :
        c'est à l'utilisateur d'en décider, pas au module de défaire.
        """
        produit = self.env['product.template'].create(
            {'name': "Objet requalifié", 'metal_nature': self.or_.id,
             'metal_quantity_mode': 'unit', 'metal_unit_weight': 6.4516})
        self.assertTrue(produit.is_storable)
        produit.metal_regulated = False
        self.assertTrue(produit.is_storable)

    # ------------------------------------------------------------------
    # L'entrée
    # ------------------------------------------------------------------
    def test_rachat_cree_une_ligne_de_registre(self):
        move = self._rachat()
        lot = move.invoice_line_ids.police_lot_id
        self.assertTrue(lot, "aucun lot créé")
        self.assertTrue(lot.police_registered)
        self.assertTrue(lot.name.startswith('TEST-2026-'), lot.name)
        self.assertEqual(lot.police_seller_id, self.vendeur)
        self.assertEqual(lot.police_origin, "Succession")
        self.assertAlmostEqual(lot.police_weight, 32.258, places=3)
        self.assertAlmostEqual(lot.police_fineness, 900.0)
        self.assertAlmostEqual(lot.police_purchase_price, 3000.0)
        self.assertEqual(lot.police_source_move_id, move)

    def test_entree_date_et_quantite(self):
        move = self._rachat(qty=5)
        lot = move.invoice_line_ids.police_lot_id
        self.assertEqual(fields.Date.to_date(lot.police_entry_date),
                         fields.Date.to_date('2026-03-10'))
        self.assertAlmostEqual(lot.police_quantity_on_hand, 5.0)
        self.assertFalse(lot.police_exit_date)

    def test_numeros_d_ordre_successifs(self):
        premier = self._rachat().invoice_line_ids.police_lot_id
        second = self._rachat().invoice_line_ids.police_lot_id
        self.assertNotEqual(premier.name, second.name)
        self.assertLess(premier.name, second.name)

    def test_avant_la_bascule_rien_ne_se_passe(self):
        self.company.police_start_date = fields.Date.to_date('2027-01-01')
        move = self._rachat()
        self.assertFalse(move.police_picking_id)
        self.assertFalse(move.invoice_line_ids.police_lot_id)

    def test_sans_date_de_bascule_le_module_est_inerte(self):
        self.company.police_start_date = False
        move = self._rachat()
        self.assertFalse(move.police_picking_id)

    def test_article_hors_registre_n_entre_pas(self):
        move = self._rachat(produit=self.remise.product_variant_id, price=50.0)
        self.assertFalse(move.police_picking_id)

    def test_comptabilisation_ne_cree_pas_d_ecriture_de_stock(self):
        """La valorisation reste hors du résultat."""
        avant = self.env['account.move'].search_count(
            [('stock_move_id', '!=', False)])
        self._rachat()
        apres = self.env['account.move'].search_count(
            [('stock_move_id', '!=', False)])
        self.assertEqual(avant, apres)

    # ------------------------------------------------------------------
    # La sortie
    # ------------------------------------------------------------------
    def test_releve_totale_date_la_sortie(self):
        lot = self._rachat(qty=5).invoice_line_ids.police_lot_id
        self._relever(lot, 5)
        self.assertTrue(lot.police_exit_date)
        self.assertAlmostEqual(lot.police_quantity_on_hand, 0.0)

    def test_releve_partielle_ne_solde_pas_la_ligne(self):
        """Tant qu'il reste de la matière, l'objet n'est pas sorti."""
        lot = self._rachat(qty=5).invoice_line_ids.police_lot_id
        self._relever(lot, 2)
        self.assertFalse(lot.police_exit_date)
        self.assertAlmostEqual(lot.police_quantity_on_hand, 3.0)

    # ------------------------------------------------------------------
    # Intangibilité
    # ------------------------------------------------------------------
    def test_ligne_de_registre_non_supprimable(self):
        lot = self._rachat().invoice_line_ids.police_lot_id
        with self.assertRaises(UserError):
            lot.unlink()

    def test_pas_de_retour_en_brouillon_apres_sortie(self):
        move = self._rachat(qty=5)
        self._relever(move.invoice_line_ids.police_lot_id, 5)
        with self.assertRaises(UserError):
            move.button_draft()

    def test_retour_en_brouillon_possible_tant_que_rien_n_est_sorti(self):
        move = self._rachat(qty=5)
        move.button_draft()
        self.assertEqual(move.state, 'draft')

    # ------------------------------------------------------------------
    # Complétude des mentions
    # ------------------------------------------------------------------
    def test_mention_manquante_signalee(self):
        """Le règlement n'est pas connu à la comptabilisation."""
        lot = self._rachat().invoice_line_ids.police_lot_id
        self.assertFalse(lot.police_payment_mode)
        self.assertFalse(lot.police_complete)
        lot.police_payment_mode = "Virement"
        self.assertTrue(lot.police_complete)

    def test_provenance_absente_signalee(self):
        lot = self._rachat(origine=False).invoice_line_ids.police_lot_id
        self.assertFalse(lot.police_complete)


@tagged('post_install', '-at_install')
class TestIntangibilite(TestLivrePolice):
    """R321-6-1 : intégrité, intangibilité, sécurité des données."""

    def _journal(self, company=None):
        return self.env['livre.police.evenement'].sudo().search(
            [('company_id', '=', (company or self.company).id)],
            order='sequence_number')

    def test_entree_inscrite_au_journal(self):
        lot = self._rachat().invoice_line_ids.police_lot_id
        journal = self._journal()
        self.assertEqual(len(journal), 1)
        self.assertEqual(journal.event_type, 'entree')
        self.assertEqual(journal.lot_id, lot)
        self.assertEqual(journal.sequence_number, 1)
        self.assertFalse(journal.previous_hash)
        self.assertEqual(len(journal.current_hash), 64)

    def test_chaine_des_empreintes(self):
        self._rachat()
        self._rachat()
        journal = self._journal()
        self.assertEqual(len(journal), 2)
        self.assertEqual(journal[1].previous_hash, journal[0].current_hash)
        self.assertEqual(journal.mapped('sequence_number'), [1, 2])

    def test_sortie_inscrite_une_seule_fois(self):
        lot = self._rachat(qty=5).invoice_line_ids.police_lot_id
        self._relever(lot, 2)
        self.assertEqual(self._journal().mapped('event_type'), ['entree'],
                         "une relève partielle ne sort pas l'objet")
        self._relever(lot, 3)
        self.assertEqual(self._journal().mapped('event_type'),
                         ['entree', 'sortie'])

    def test_correction_tracee(self):
        """On n'écrase pas une mention : on inscrit sa rectification."""
        lot = self._rachat().invoice_line_ids.police_lot_id
        lot.police_payment_mode = "Virement"
        journal = self._journal()
        self.assertEqual(journal.mapped('event_type'), ['entree', 'correction'])
        self.assertIn("Mode de règlement", journal[1].description)
        self.assertIn("Virement", journal[1].description)

    def test_correction_sans_changement_reel_non_inscrite(self):
        lot = self._rachat().invoice_line_ids.police_lot_id
        lot.police_origin = "Succession"  # valeur identique
        self.assertEqual(len(self._journal()), 1)

    def test_journal_en_ajout_seul(self):
        self._rachat()
        evenement = self._journal()
        with self.assertRaises(UserError):
            evenement.description = "retouche"
        with self.assertRaises(UserError):
            evenement.unlink()

    def test_integrite_confirmee(self):
        self._rachat()
        self._rachat()
        self.assertIsNone(
            self.env['livre.police.evenement']._verifier_chaine(self.company))

    def test_empreinte_falsifiee_detectee(self):
        """Modifier une mention inscrite doit casser la chaîne."""
        self._rachat()
        self._rachat()
        evenement = self._journal()[0]
        self.env.cr.execute(
            "UPDATE livre_police_evenement SET payload = %s WHERE id = %s",
            ('{"poids":0.0}', evenement.id))
        evenement.invalidate_recordset()
        defaut = self.env['livre.police.evenement']._verifier_chaine(self.company)
        self.assertIsNotNone(defaut, "la falsification n'a pas été détectée")
        self.assertEqual(defaut[0], evenement)

    def test_evenement_retire_detecte(self):
        self._rachat()
        self._rachat()
        premier = self._journal()[0]
        self.env.cr.execute(
            "DELETE FROM livre_police_evenement WHERE id = %s", (premier.id,))
        self.env['livre.police.evenement'].invalidate_model()
        defaut = self.env['livre.police.evenement']._verifier_chaine(self.company)
        self.assertIsNotNone(defaut, "le retrait n'a pas été détecté")

    def test_mentions_normalisees_stables(self):
        """Une même réalité produit toujours la même empreinte."""
        lot = self._rachat().invoice_line_ids.police_lot_id
        premier = lot._police_mentions_normalisees()
        lot.invalidate_recordset()
        self.assertEqual(premier, lot._police_mentions_normalisees())


@tagged('post_install', '-at_install')
class TestInventaireOuverture(TestLivrePolice):
    """R321-4 : ce qui est détenu en stock à la bascule entre au registre."""

    def _ouvrir(self, lignes=None, **valeurs):
        lignes = lignes if lignes is not None else [
            (0, 0, {'product_id': self.piece.id, 'quantity': 30})]
        wizard = self.env['livre.police.ouverture'].create(dict({
            'company_id': self.company.id,
            'line_ids': lignes,
        }, **valeurs))
        wizard.action_valider()
        return wizard

    def test_ouverture_cree_les_lignes_et_le_stock(self):
        self._ouvrir()
        lot = self.env['stock.lot'].search(
            [('police_opening', '=', True)], limit=1)
        self.assertTrue(lot.name.startswith('TEST-2026-'))
        self.assertTrue(lot.police_registered)
        self.assertAlmostEqual(lot.police_quantity, 30.0)
        self.assertAlmostEqual(lot.police_weight, 193.548, places=3)
        self.assertAlmostEqual(lot.police_fineness, 900.0)
        self.assertAlmostEqual(lot.police_quantity_on_hand, 30.0)
        self.assertEqual(fields.Date.to_date(lot.police_entry_date),
                         self.company.police_start_date)

    def test_poids_deduit_du_regime(self):
        wizard = self.env['livre.police.ouverture'].create({
            'company_id': self.company.id,
            'line_ids': [(0, 0, {'product_id': self.piece.id, 'quantity': 4})],
        })
        self.assertAlmostEqual(wizard.line_ids.weight, 25.8064, places=4)

    def test_ligne_d_ouverture_complete_sans_vendeur_ni_prix(self):
        """On ne fabrique pas un vendeur : la ligne reste néanmoins complète."""
        self._ouvrir()
        lot = self.env['stock.lot'].search(
            [('police_opening', '=', True)], limit=1)
        self.assertFalse(lot.police_seller_id)
        self.assertFalse(lot.police_purchase_price)
        self.assertTrue(lot.police_complete)

    def test_ouverture_inscrite_au_journal(self):
        self._ouvrir()
        journal = self.env['livre.police.evenement'].sudo().search(
            [('company_id', '=', self.company.id)])
        self.assertEqual(journal.mapped('event_type'), ['ouverture'])

    def test_poids_obligatoire(self):
        with self.assertRaises(UserError):
            self._ouvrir(lignes=[(0, 0, {
                'product_id': self.piece.id, 'quantity': 1, 'weight': 0.0})])

    def test_sans_ligne_refuse(self):
        with self.assertRaises(UserError):
            self._ouvrir(lignes=[])

    def test_second_passage_refuse_sans_confirmation(self):
        """Rejouer une ouverture doublerait le stock et le registre."""
        self._ouvrir()
        self.assertTrue(self.company.police_opening_date)
        with self.assertRaises(UserError):
            self._ouvrir()

    def test_second_passage_accepte_si_confirme(self):
        self._ouvrir()
        self._ouvrir(confirm_complement=True)
        self.assertEqual(self.env['stock.lot'].search_count(
            [('police_opening', '=', True)]), 2)

    def test_sans_date_de_bascule_refuse(self):
        self.company.police_start_date = False
        with self.assertRaises(UserError):
            self._ouvrir()

    def test_objet_ouvert_puis_releve(self):
        """Une ligne d'ouverture se solde comme une autre."""
        self._ouvrir()
        lot = self.env['stock.lot'].search(
            [('police_opening', '=', True)], limit=1)
        self._relever(lot, 30)
        self.assertTrue(lot.police_exit_date)
        journal = self.env['livre.police.evenement'].sudo().search(
            [('company_id', '=', self.company.id)], order='sequence_number')
        self.assertEqual(journal.mapped('event_type'), ['ouverture', 'sortie'])
        self.assertIsNone(
            self.env['livre.police.evenement']._verifier_chaine(self.company))


@tagged('post_install', '-at_install')
class TestMentionsEditees(TestLivrePolice):
    """Les mentions portées sur l'édition du registre.

    L'art. 56 J quindecies de l'annexe IV veut « les noms, prénoms et
    adresses » ; l'art. R321-4 du code pénal y ajoute « la nature, le numéro
    et la date de délivrance de la pièce d'identité […] avec l'indication de
    l'autorité qui l'a établie ». Le seul nom d'usage ne suffit pas.
    """

    def _particulier(self):
        return self.env['res.partner'].create({
            'lastname': "Kieffer", 'firstname': "Marie-Claire",
            'is_company': False,
            'street': "14 rue des Clercs", 'zip': '57000', 'city': "Metz",
            'id_doc_type': 'cni', 'id_doc_number': '051257304118',
            'id_doc_issue_date': fields.Date.to_date('2019-06-03'),
            'id_doc_authority': "Préfecture de la Moselle",
        })

    def _lot_vendu_par(self, partenaire):
        return self.env['stock.lot']._police_create_entry({
            'product_id': self.piece.product_variant_id.id,
            'company_id': self.company.id,
            'police_seller_id': partenaire.id,
            'police_origin': "Bijoux de famille",
            'police_quantity': 1, 'police_weight': 6.4516,
            'police_entry_date': fields.Datetime.now(),
        })

    def test_vendeur_porte_nom_prenoms_et_domicile(self):
        lot = self._lot_vendu_par(self._particulier())
        mention = lot._police_vendeur()
        self.assertIn("KIEFFER", mention)
        self.assertIn("Marie-Claire", mention)
        self.assertIn("14 rue des Clercs", mention)
        self.assertIn("57000 Metz", mention)

    def test_piece_identite_porte_les_quatre_mentions(self):
        """Nature, numéro, date de délivrance, autorité — et rien de plus :
        l'art. R321-4 n'exige pas le lieu de délivrance."""
        lot = self._lot_vendu_par(self._particulier())
        mention = lot._police_piece_identite()
        self.assertIn("Carte nationale d'identité", mention)
        self.assertIn("051257304118", mention)
        self.assertIn("03/06/2019", mention)
        self.assertIn("Préfecture de la Moselle", mention)

    def test_ligne_d_ouverture_n_invente_ni_vendeur_ni_piece(self):
        lot = self.env['stock.lot']._police_create_entry({
            'product_id': self.piece.product_variant_id.id,
            'company_id': self.company.id, 'police_opening': True,
            'police_origin': "Reprise du registre antérieur",
            'police_quantity': 3, 'police_weight': 19.3548,
            'police_entry_date': fields.Datetime.now(),
        })
        self.assertEqual(lot._police_vendeur(), "")
        self.assertEqual(lot._police_piece_identite(), "")

    def test_la_sortie_inscrit_son_destinataire(self):
        move = self._rachat(qty=4)
        lot = move.police_picking_id.move_line_ids.lot_id
        self._relever(lot, 4)
        self.assertEqual(lot.police_exit_picking_id.partner_id, self.fondeur)

    def test_edition_porte_les_mentions_obligatoires(self):
        """L'édition est la pièce présentée au contrôleur : elle doit porter
        toutes les mentions, pas seulement celles qui tiennent à l'écran.

        On rend le QWeb, pas le PDF : fabriquer le PDF réclame wkhtmltopdf et
        un serveur HTTP vivant, ce qui éprouverait la tuyauterie d'Odoo et non
        notre registre.
        """
        lot = self._lot_vendu_par(self._particulier())
        rapport = self.env.ref('fr_livre_police.action_report_livre_police')
        self.assertEqual(rapport.paperformat_id.orientation, 'Landscape')

        edition = rapport._render_qweb_html(rapport.report_name, lot.ids)[0]
        edition = edition.decode() if isinstance(edition, bytes) else edition
        # QWeb échappe les données : l'apostrophe y devient `&#39;`.
        edition = html.unescape(edition)

        for entete in ("N° d'ordre", "référence", "entrées",
                       "Origine des achats",
                       "Noms et adresses des fournisseurs",
                       "Désignation des objets achetés ou confiés,",
                       "Nombre", "Objets achetés aux fabricants",
                       "Objets d’occasion achetés à des particuliers",
                       "Autres achats", "Objets confiés par des tiers",
                       "Poids", "Platine", "Or et", "Argent",
                       "remise", "vendus", "Observations"):
            self.assertIn(entete, edition, entete)

        for mention in (lot.name, "KIEFFER", "Marie-Claire",
                        "14 rue des Clercs", "57000 Metz",
                        "Carte nationale d'identité", "051257304118",
                        "Préfecture de la Moselle", "Bijoux de famille"):
            self.assertIn(mention, edition, mention)

        # Page de garde : ouverture, clôture et visa de l'autorité.
        self.assertIn("Registre ouvert le", edition)
        self.assertIn("Registre clôturé le", edition)
        self.assertIn("Visa du commissaire de police ou du maire", edition)


@tagged('post_install', '-at_install')
class TestDescriptionDesObjets(TestLivrePolice):
    """Un lot « 18 carats, 148,60 g » n'identifie aucun objet.

    L'art. R321-3 veut « les caractéristiques ainsi que les noms, signatures,
    monogrammes, lettres, chiffres, numéros de série, emblèmes et signes de
    toute nature apposés sur [l'objet] et qui servent à l'identifier ». La
    description se saisit en note sous la ligne de l'avoir ; le registre en
    garde une copie scellée.
    """

    NOTE = "3 alliances, 1 gourmette maille anglaise, 1 pendentif cassé"

    def _avoir(self, notes=(NOTE,), origine="Succession"):
        lignes = [(0, 0, {
            'product_id': self.piece.product_variant_id.id,
            'quantity': 5, 'price_unit': 600.0, 'tax_ids': [(5, 0, 0)],
            'police_origin': origine, 'sequence': 10,
        })]
        for rang, texte in enumerate(notes):
            lignes.append((0, 0, {
                'display_type': 'line_note', 'name': texte,
                'sequence': 11 + rang,
            }))
        return self.env['account.move'].create({
            'move_type': 'out_refund', 'partner_id': self.vendeur.id,
            'invoice_date': fields.Date.to_date('2026-03-10'),
            'date': fields.Date.to_date('2026-03-10'),
            'invoice_line_ids': lignes,
        })

    def test_la_note_devient_la_description_du_lot(self):
        avoir = self._avoir()
        avoir.action_post()
        lot = avoir.police_picking_id.move_line_ids.lot_id
        self.assertEqual(lot.police_description, self.NOTE)

    def test_plusieurs_notes_se_suivent(self):
        avoir = self._avoir(notes=("2 alliances 18k", "1 chaîne maille forçat"))
        avoir.action_post()
        lot = avoir.police_picking_id.move_line_ids.lot_id
        self.assertEqual(lot.police_description,
                         "2 alliances 18k\n1 chaîne maille forçat")

    def test_sans_note_la_comptabilisation_est_refusee(self):
        avoir = self._avoir(notes=())
        with self.assertRaises(UserError):
            avoir.action_post()

    def test_la_ligne_muette_se_signale_avant_la_comptabilisation(self):
        avoir = self._avoir(notes=())
        ligne = avoir.invoice_line_ids.filtered('product_id')
        self.assertTrue(ligne.police_description_missing)
        avoir_decrit = self._avoir()
        ligne = avoir_decrit.invoice_line_ids.filtered('product_id')
        self.assertFalse(ligne.police_description_missing)

    def test_effacer_la_note_n_efface_pas_le_registre(self):
        """La note est la saisie ; le registre en garde une copie scellée."""
        avoir = self._avoir()
        avoir.action_post()
        lot = avoir.police_picking_id.move_line_ids.lot_id
        avoir.button_draft()
        avoir.invoice_line_ids.filtered(
            lambda l: l.display_type == 'line_note').unlink()
        self.assertEqual(lot.police_description, self.NOTE)

    def test_retoucher_la_description_laisse_une_correction(self):
        avoir = self._avoir()
        avoir.action_post()
        lot = avoir.police_picking_id.move_line_ids.lot_id
        avant = len(lot.police_event_ids)
        lot.police_description = self.NOTE + ", 1 médaille de baptême"
        self.assertEqual(len(lot.police_event_ids), avant + 1)
        correction = lot.police_event_ids.sorted('sequence_number')[-1]
        self.assertEqual(correction.event_type, 'correction')
        self.assertIn("médaille de baptême", correction.description)

    def test_la_description_entre_dans_l_empreinte(self):
        avoir = self._avoir()
        avoir.action_post()
        lot = avoir.police_picking_id.move_line_ids.lot_id
        self.assertIn(self.NOTE, lot._police_mentions_normalisees())
        self.assertFalse(self.env['livre.police.evenement']._verifier_chaine(
            self.company))


@tagged('post_install', '-at_install')
class TestVentilationDuRegistre(TestLivrePolice):
    """Le registre ne totalise pas le métal : il le ventile.

    Douze cases de poids — quatre canaux d'acquisition croisés avec platine,
    or et alliages, argent. Une ligne n'en sert qu'une.
    """

    def _lot_particulier(self):
        partenaire = self.env['res.partner'].create({
            'lastname': "Muller", 'firstname': "Paul", 'is_company': False})
        return self.env['stock.lot']._police_create_entry({
            'product_id': self.piece.product_variant_id.id,
            'company_id': self.company.id,
            'police_seller_id': partenaire.id,
            'police_origin': "Succession", 'police_quantity': 2,
            'police_weight': 12.9032,
            'police_entry_date': fields.Datetime.now(),
        })

    def test_l_or_d_un_particulier_ne_sert_qu_une_case(self):
        lot = self._lot_particulier()
        cases = lot._police_cases_poids()
        self.assertEqual(cases['particuliers/or'], 12.9032)
        servies = [cle for cle, poids in cases.items() if poids]
        self.assertEqual(servies, ['particuliers/or'])

    def test_une_societe_verse_aux_autres_achats(self):
        lot = self.env['stock.lot']._police_create_entry({
            'product_id': self.piece.product_variant_id.id,
            'company_id': self.company.id,
            'police_seller_id': self.vendeur.id,
            'police_origin': "Rachat confrère", 'police_quantity': 1,
            'police_weight': 6.4516,
            'police_entry_date': fields.Datetime.now(),
        })
        self.assertEqual(lot._police_canal(), 'autres')
        self.assertEqual(lot._police_cases_poids()['autres/or'], 6.4516)

    def test_une_ligne_d_ouverture_verse_aux_autres_achats(self):
        lot = self.env['stock.lot']._police_create_entry({
            'product_id': self.piece.product_variant_id.id,
            'company_id': self.company.id, 'police_opening': True,
            'police_origin': "Reprise", 'police_quantity': 1,
            'police_weight': 6.4516,
            'police_entry_date': fields.Datetime.now(),
        })
        self.assertEqual(lot._police_canal(), 'autres')

    def test_un_metal_hors_colonnes_passe_en_observations(self):
        """Le registre n'a que platine, or et argent : le palladium n'a pas
        de case. Son poids passe en observations plutôt que sous un faux
        métal — il ne disparaît pas."""
        palladium = self.env.ref('fr_numismatics_metals.metal_nature_palladium')
        article = self.env['product.template'].create({
            'name': "Palladium (test)", 'metal_nature': palladium.id,
            'metal_quantity_mode': 'gram'})
        lot = self.env['stock.lot']._police_create_entry({
            'product_id': article.product_variant_id.id,
            'company_id': self.company.id,
            'police_seller_id': self.vendeur.id,
            'police_origin': "Rachat", 'police_quantity': 1,
            'police_weight': 31.5,
            'police_entry_date': fields.Datetime.now(),
        })
        self.assertIsNone(lot._police_colonne_metal())
        self.assertFalse([p for p in lot._police_cases_poids().values() if p])
        self.assertIn("Palladium", lot._police_observations())
        self.assertIn("31.5", lot._police_observations())

    def test_les_canaux_non_pratiques_sont_grises(self):
        """Les colonnes inutilisées restent au registre, grisées : les
        retirer donnerait à lire un registre remanié."""
        lot = self._lot_particulier()
        rapport = self.env.ref('fr_livre_police.action_report_livre_police')
        edition = rapport._render_qweb_html(rapport.report_name, lot.ids)[0]
        edition = edition.decode() if isinstance(edition, bytes) else edition
        edition = html.unescape(edition)

        def grise(intitule):
            motif = r'<th style="([^"]*)"[^>]*>\s*' + re.escape(intitule)
            trouve = re.search(motif, edition)
            self.assertTrue(trouve, intitule)
            return '#e4e9ef' in trouve.group(1)

        for inutilise in ("Objets achetés aux fabricants",
                          "Objets confiés par des tiers"):
            self.assertTrue(grise(inutilise), inutilise)
        for pratique in ("Objets d’occasion achetés à des particuliers",
                         "Autres achats"):
            self.assertFalse(grise(pratique), pratique)

    def test_chaque_ligne_a_autant_de_cellules_que_de_colonnes(self):
        """Une cellule vide ne doit pas emporter sa colonne.

        `t-out` retire la balise quand la valeur est nulle : une case de
        poids non servie ferait disparaître son `<td>` et décalerait toute
        la ligne — le poids d'un particulier se lirait sous « fabricants ».
        """
        lots = self._lot_particulier()
        rapport = self.env.ref('fr_livre_police.action_report_livre_police')
        edition = rapport._render_qweb_html(rapport.report_name, lots.ids)[0]
        edition = edition.decode() if isinstance(edition, bytes) else edition

        colonnes = len(re.findall(r'<col ', edition))
        self.assertEqual(colonnes, 20)
        corps = edition[edition.index('<tbody>'):edition.index('</tbody>')]
        for rang, ligne in enumerate(re.findall(r'<tr[^>]*>(.*?)</tr>',
                                                corps, re.S), 1):
            self.assertEqual(ligne.count('<td'), colonnes,
                             "ligne %d : %d cellules pour %d colonnes"
                             % (rang, ligne.count('<td'), colonnes))
