# -*- coding: utf-8 -*-
"""Corriger une inscription sans la toucher.

Le registre n'admet pas la correction sur place : « les enregistrements
informatiques créés pour les ouvrages d'occasion ne [peuvent] être modifiés
que par création d'un nouvel enregistrement avec indication de son motif »
(CGI, ann. IV, art. 56 J sexdecies, 2° c).

Une rectification est donc une inscription de plus. Elle reçoit son propre
numéro d'ordre, à la suite, porte le motif de la correction et renvoie à
l'inscription qu'elle reprend. L'originale demeure, lisible telle qu'elle a
été écrite le jour du rachat : un registre montre ce qui a été consigné, y
compris ce qui l'a été à tort.

L'assistant part des valeurs d'origine plutôt que d'un formulaire vide. Une
rectification ne corrige presque jamais tout : la recopie manuelle des
mentions justes serait une occasion d'en fausser une seconde.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LivrePoliceRectification(models.TransientModel):
    _name = 'livre.police.rectification'
    _description = "Livre de police - rectification d'une inscription"

    ligne_id = fields.Many2one(
        'livre.police.ligne', string="Inscription à rectifier",
        required=True, readonly=True, ondelete='cascade',
    )
    numero_ordre_origine = fields.Char(
        related='ligne_id.numero_ordre', string="N° d'ordre d'origine",
        readonly=True,
    )
    motif = fields.Text(
        string="Motif de la rectification", required=True,
        help="Ce qui a été constaté, et pourquoi l'inscription d'origine "
             "devait être corrigée. Cette mention est exigée par le texte : "
             "une rectification sans motif ne vaut pas.",
    )

    # Les mentions du registre, préremplies depuis l'inscription d'origine.
    date_achat = fields.Date(string="Date de l'achat", required=True)
    designation = fields.Char(string="Désignation")
    description = fields.Text(string="Description de l'objet")
    provenance = fields.Char(string="Provenance")
    vendeur_nom = fields.Char(string="Nom du vendeur")
    vendeur_qualite = fields.Char(string="Qualité ou profession")
    vendeur_domicile = fields.Text(string="Domicile ou siège social")
    representant_nom = fields.Char(string="Représentant")
    representant_qualite = fields.Char(string="Qualité du représentant")
    piece_nature = fields.Char(string="Nature de la pièce")
    piece_numero = fields.Char(string="N° de la pièce")
    piece_autorite = fields.Char(string="Autorité de délivrance")
    piece_delivrance = fields.Date(string="Date de délivrance")
    prix = fields.Monetary(string="Prix d'achat", currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', readonly=True)
    mode_reglement = fields.Char(string="Mode de règlement")
    protection_patrimoine = fields.Char(string="Protection (code du patrimoine)")
    metal_nature = fields.Char(string="Nature du métal")
    quantite = fields.Float(string="Quantité", digits=(12, 4))
    regime_quantite = fields.Char(string="Régime")
    poids = fields.Float(string="Poids (g)", digits=(12, 4))
    titre = fields.Float(string="Titre (millièmes)", digits=(5, 1))
    titre_lot = fields.Boolean(string="Lot de titres")
    date_sortie = fields.Date(string="Date de sortie")

    _MENTIONS = (
        'date_achat', 'designation', 'description', 'provenance',
        'vendeur_nom', 'vendeur_qualite', 'vendeur_domicile',
        'representant_nom', 'representant_qualite',
        'piece_nature', 'piece_numero', 'piece_autorite', 'piece_delivrance',
        'prix', 'currency_id', 'mode_reglement', 'protection_patrimoine',
        'metal_nature', 'quantite', 'regime_quantite', 'poids', 'titre',
        'titre_lot', 'date_sortie',
    )

    @api.model
    def default_get(self, champs):
        valeurs = super().default_get(champs)
        ligne = self.env['livre.police.ligne'].browse(
            valeurs.get('ligne_id') or self.env.context.get('default_ligne_id'))
        if not ligne.exists():
            return valeurs
        for nom in self._MENTIONS:
            champ = ligne._fields[nom]
            valeurs[nom] = (ligne[nom].id if champ.type == 'many2one'
                            else ligne[nom])
        return valeurs

    def action_rectifier(self):
        """Inscrit la correction à la suite, et laisse l'originale en place."""
        self.ensure_one()
        origine = self.ligne_id
        if not self.motif.strip():
            raise UserError(_(
                "Une rectification s'inscrit avec son motif : « par création "
                "d'un nouvel enregistrement avec indication de son motif » "
                "(CGI, ann. IV, art. 56 J sexdecies, 2° c)."))

        Registre = self.env['livre.police.ligne']
        valeurs = {nom: (self[nom].id if self._fields[nom].type == 'many2one'
                         else self[nom])
                   for nom in self._MENTIONS}
        valeurs.update({
            'numero_ordre': Registre._sequence(origine.company_id).next_by_id(),
            'company_id': origine.company_id.id,
            # La pièce reste rattachée pour qu'on remonte à l'opération ; la
            # ligne d'avoir, non : elle est déjà inscrite, et l'unicité doit
            # continuer d'empêcher une double inscription.
            'move_id': origine.move_id.id,
            'rectifie_id': origine.id,
            'motif_rectification': self.motif.strip(),
            'page_id': self.env['livre.police.page']._page_courante(
                origine.company_id).id,
            'date_inscription': fields.Datetime.now(),
            'inscrit_par_id': self.env.user.id,
        })
        rectification = Registre.sudo().create(valeurs)
        return {
            'type': 'ir.actions.act_window',
            'name': "Inscription %s" % rectification.numero_ordre,
            'res_model': 'livre.police.ligne',
            'res_id': rectification.id,
            'view_mode': 'form',
        }
