# -*- coding: utf-8 -*-
"""La date d'entrée d'un métal reçu d'un autre établissement.

Ce constat vient d'un cas rencontré en exploitation, pas d'une intention.
Un transfert fait le 3 septembre s'inscrivait, chez l'établissement qui
recevait, à la date du 2 — celle du rachat d'origine chez celui qui
expédiait. La colonne « date d'entrée » du registre de Metz annonçait donc
une entrée la veille du jour où le métal y était arrivé.

L'inscription recopiait la date d'origine au nom d'un raisonnement qui se
contredit : si les trois établissements n'en faisaient qu'un, ce transfert
n'aurait rien à inscrire nulle part. C'est parce qu'« un registre est tenu
pour chaque établissement » (c. pén., art. R321-6) que l'entrée existe, et
« la date d'entrée et de sortie » qu'il réclame (CGI, ann. IV,
art. 56 J quindecies) est celle de cette entrée-ci.

Le test vérifie aussi que la date du rachat ne se perd pas : elle demeure à
« date du rachat », et la provenance la redit en toutes lettres.
"""

from datetime import timedelta

from odoo import fields
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestDateEntreeTransfert(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.aujourdhui = fields.Date.context_today(cls.env['res.company'])
        cls.veille = cls.aujourdhui - timedelta(days=1)

        Societe = cls.env['res.company']
        cls.depart = Societe.create({'name': "Comptoir qui expédie"})
        cls.arrivee = Societe.create({'name': "Comptoir qui reçoit"})
        cls.env.user.company_ids |= cls.depart | cls.arrivee

        cls.env.ref('stock.stock_location_inter_company').sudo().active = True

        cls.lingot = cls.env['product.template'].create({
            'name': "Lingot d'essai 50 g",
            'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': cls.env.ref('fr_numismatics_metals.metal_nature_or').id,
            'metal_fineness': 999.0, 'metal_quantity_mode': 'unit',
            'metal_unit_weight': 50.0,
        }).product_variant_id

        # Le stock d'ouverture tient lieu d'entrée datée de la veille : c'est
        # le chemin le plus court vers un lot déjà là, avec sa date.
        reprise = cls.env['livre.police.reprise'].with_company(cls.depart).create({
            'company_id': cls.depart.id,
            'date_arrete': cls.veille,
            'libelle': "Reprise d'essai",
            'ligne_ids': [(0, 0, {
                'product_id': cls.lingot.id, 'quantite': 4.0,
                'description': "Voir livre de police manuscrit"})],
        })
        reprise.action_inscrire()
        cls.entree = reprise.inscription_ids

    def test_l_entree_par_transfert_porte_le_jour_de_l_arrivee(self):
        self.assertEqual(self.entree.date_achat, self.veille)

        transfert = self.env['livre.police.transfert'].with_company(
            self.depart).create({
                'company_id': self.depart.id,
                'company_destination_id': self.arrivee.id,
                'motif': "Essai de datation.",
                'ligne_ids': [(0, 0, {'inscription_id': self.entree.id,
                                      'quantite': 2.0})],
            })
        transfert.action_expedier()
        transfert.action_receptionner()

        inscriptions = self.env['livre.police.ligne'].search(
            [('transfert_id', '=', transfert.id)])
        arrivee = inscriptions.filtered(
            lambda l: l.company_id == self.arrivee)
        sortie = inscriptions.filtered(lambda l: l.sens == 'sortie')

        # Chez celui qui reçoit : entré aujourd'hui, racheté la veille.
        self.assertEqual(arrivee.date_achat, self.aujourdhui)
        self.assertEqual(arrivee.date_mouvement, self.aujourdhui)
        self.assertEqual(arrivee.origine_date_achat, self.veille)
        self.assertIn(fields.Date.to_string(self.veille)[-2:],
                      arrivee.provenance or '')

        # Chez celui qui expédie : entré la veille, sorti aujourd'hui.
        self.assertEqual(sortie.date_achat, self.veille)
        self.assertEqual(sortie.date_mouvement, self.aujourdhui)
