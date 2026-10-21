# -*- coding: utf-8 -*-
"""Une requalification saisie à l'écran, et non par le serveur.

L'écran a refusé sa première requalification réelle : « un champ obligatoire
n'est pas défini », sur l'inscription de chaque lot trié. Le navigateur
n'envoie que les champs de la vue, et celui-là n'y figurait pas. Les essais
passaient par le serveur, qui remplit les lignes lui-même : rien ne le
montrait. Le formulaire de test, lui, ne transmet que ce que la vue porte.
"""

from odoo import fields
from odoo.tests import Form, TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestRequalificationDepuisLEcran(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.comptoir = cls.env['res.company'].create({'name': "Comptoir d'essai"})
        cls.env.user.company_ids |= cls.comptoir
        or_jaune = cls.env.ref('fr_numismatics_metals.metal_nature_or')
        dix_huit, titre_divers = cls.env['product.template'].create([{
            'name': nom, 'type': 'consu', 'is_storable': True, 'tracking': 'lot',
            'metal_nature': or_jaune.id, 'metal_fineness': titre,
            'metal_quantity_mode': 'gram', 'police_description_required': True,
        } for nom, titre in (("18K d'essai (gr)", 750.0),
                             ("Titre divers d'essai (gr)", 585.0))])
        cls.titre_divers = titre_divers.product_variant_id
        reprise = cls.env['livre.police.reprise'].with_company(cls.comptoir).create({
            'company_id': cls.comptoir.id,
            'date_arrete': fields.Date.context_today(cls.env['res.company']),
            'libelle': "Reprise d'essai",
            'ligne_ids': [(0, 0, {
                'product_id': dix_huit.product_variant_id.id, 'quantite': 2.5,
                'description': "Une bague"})],
        })
        reprise.action_inscrire()
        cls.entree = reprise.inscription_ids

    def test_saisi_en_18k_reclasse_en_titre_divers(self):
        ecran = Form(self.env['livre.police.requalification'].with_company(
            self.comptoir).with_context(
                active_model='livre.police.ligne', active_ids=self.entree.ids))
        with ecran.ligne_ids.edit(0) as lot:
            lot.quantite_retiree = 2.5
        ecran.product_id = self.titre_divers
        ecran.description = "Une bague, poinçon 14 carats"
        ecran.motif = "Saisie en 18K par erreur."
        action = ecran.save().action_requalifier()

        reclassee = self.env['livre.police.ligne'].browse(
            action['domain'][0][2]).filtered(lambda l: not l.rectifie_id)
        self.assertEqual(reclassee.poids, 2.5)
        self.assertEqual(self.entree._rectification_finale().poids, 0.0)
