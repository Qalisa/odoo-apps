# -*- coding: utf-8 -*-
"""Rectifier les quantités de plusieurs inscriptions d'un seul geste.

Une reprise de stock d'ouverture porte le coffre entier ; quand l'état qui
l'a nourrie se révèle faux, ce n'est pas une inscription qu'il faut corriger,
c'en est une poignée, pour la même raison et le même jour. Les reprendre une
par une multiplierait les occasions de saisir un motif un peu différent à
chaque fois — et le motif est ce que le texte exige (CGI, ann. IV,
art. 56 J sexdecies, 2° c). Un seul motif, porté par un seul geste, dit
mieux ce qui s'est passé.

L'assistant ne touche qu'à la quantité, et le poids en découle : il ne se
saisit pas. Une inscription porte le poids de ce qu'elle décrit, et vingt
lingots de vingt grammes qui n'ont jamais existé en retirent quatre cents ;
la proportion vaut pour les deux régimes de saisie — au gramme, la quantité
*est* le poids ; à la pièce, elle en est le multiple. Laisser saisir le poids
librement ici ouvrirait la porte à une inscription qui se contredit
elle-même.

Ce n'est jamais une sortie. Une sortie affirmerait que le métal est parti,
sans acheteur ni facture ; ce métal n'est pas parti, il n'a jamais été là.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LivrePoliceRectificationQuantite(models.TransientModel):
    _name = 'livre.police.rectification.quantite'
    _description = "Livre de police - rectifier des quantités"

    motif = fields.Text(
        string="Motif de la rectification", required=True,
        help="Ce qui a été constaté, et pourquoi ces inscriptions devaient "
             "être corrigées. Le même motif s'inscrit sur chacune : elles "
             "procèdent du même constat.\n\n"
             "Cette mention est exigée par le texte — une rectification sans "
             "motif ne vaut pas (CGI, ann. IV, art. 56 J sexdecies, 2° c).",
    )
    ligne_ids = fields.One2many(
        'livre.police.rectification.quantite.ligne', 'wizard_id',
        string="Inscriptions à rectifier",
    )

    @api.model
    def default_get(self, champs):
        valeurs = super().default_get(champs)
        inscriptions = self.env['livre.police.ligne'].browse(
            self.env.context.get('active_ids') or [])
        inscriptions = inscriptions.exists().filtered(
            lambda l: l.sens == 'entree' and not l.rectifie_id)
        if not inscriptions:
            raise UserError(_(
                "Cet écran rectifie des quantités entrées. Sélectionnez des "
                "inscriptions d'entrée qui ne sont pas elles-mêmes des "
                "rectifications."))
        societes = inscriptions.company_id
        if len(societes) > 1:
            raise UserError(_(
                "Ces inscriptions relèvent de plusieurs établissements "
                "(%(societes)s). Un registre est tenu pour chacun (c. pén., "
                "art. R321-6) : rectifiez-les établissement par "
                "établissement.",
                societes=", ".join(societes.mapped('display_name'))))
        # La quantité part de ce qui est inscrit : on ne corrige que ce
        # qu'on change, et une ligne laissée telle quelle ne rectifie rien.
        valeurs['ligne_ids'] = [
            (0, 0, {'inscription_id': inscription.id,
                    'quantite': inscription._rectification_finale().quantite})
            for inscription in inscriptions.sorted('numero_ordre')]
        return valeurs

    def action_rectifier(self):
        """Inscrit une rectification par ligne changée, et ajuste le stock."""
        self.ensure_one()
        changees = self.ligne_ids.filtered('changee')
        if not changees:
            raise UserError(_(
                "Aucune quantité n'a été modifiée : il n'y a rien à "
                "rectifier."))

        rectifications = self.env['livre.police.ligne']
        for ligne in changees:
            origine = ligne.inscription_id
            courante = origine._rectification_finale()
            mentions = {nom: (courante[nom].id
                              if courante._fields[nom].type == 'many2one'
                              else courante[nom])
                        for nom in self.env[
                            'livre.police.rectification']._MENTIONS}
            mentions.update({'quantite': ligne.quantite, 'poids': ligne.poids})
            rectifications |= origine._inscrire_rectification(
                mentions, self.motif)
            origine._ajuster_le_stock(ligne.quantite - courante.quantite)

        return {
            'type': 'ir.actions.act_window',
            'name': _("Rectifications inscrites"),
            'res_model': 'livre.police.ligne',
            'view_mode': 'list,form',
            'domain': [('id', 'in', rectifications.ids)],
        }


class LivrePoliceRectificationQuantiteLigne(models.TransientModel):
    _name = 'livre.police.rectification.quantite.ligne'
    _description = "Livre de police - quantité à rectifier"

    wizard_id = fields.Many2one(
        'livre.police.rectification.quantite', required=True,
        ondelete='cascade',
    )
    inscription_id = fields.Many2one(
        'livre.police.ligne', string="Inscription", required=True,
        readonly=True, ondelete='cascade',
    )
    numero_ordre = fields.Char(
        related='inscription_id.numero_ordre', string="N° d'ordre",
        readonly=True,
    )
    designation = fields.Char(
        related='inscription_id.designation', string="Désignation",
        readonly=True,
    )
    quantite_inscrite = fields.Float(
        string="Quantité inscrite", digits=(12, 4), readonly=True,
        compute='_compute_etat_actuel',
        help="Ce que le registre affirme aujourd'hui — la dernière "
             "rectification s'il y en a eu.",
    )
    poids_inscrit = fields.Float(
        string="Poids inscrit (g)", digits=(12, 4), readonly=True,
        compute='_compute_etat_actuel',
    )
    quantite_en_stock = fields.Float(
        string="Quantité en stock", digits=(12, 4), readonly=True,
        compute='_compute_etat_actuel',
        help="Ce que le stock détient pour ce lot. Il peut différer de la "
             "quantité inscrite quand une partie est déjà repartie : ces "
             "départs-là sont inscrits au registre et ne se rectifient pas "
             "ici.",
    )
    quantite = fields.Float(
        string="Quantité réelle", digits=(12, 4), required=True,
        default=0.0,
        help="La quantité réellement détenue. Le poids en découle.",
    )
    poids = fields.Float(
        string="Poids rectifié (g)", digits=(12, 4), readonly=True,
        compute='_compute_poids',
        help="Déduit de la quantité, à la proportion du poids inscrit : au "
             "gramme la quantité vaut le poids, à la pièce elle en est le "
             "multiple. Il ne se saisit pas — une inscription ne doit pas "
             "pouvoir se contredire elle-même.",
    )
    changee = fields.Boolean(compute='_compute_poids')

    @api.depends('inscription_id')
    def _compute_etat_actuel(self):
        for ligne in self:
            courante = ligne.inscription_id._rectification_finale()
            ligne.quantite_inscrite = courante.quantite
            ligne.poids_inscrit = courante.poids
            lot = ligne.inscription_id._lot_du_registre()
            ligne.quantite_en_stock = sum(
                self.env['stock.quant'].sudo().search([
                    ('lot_id', '=', lot.id),
                    ('company_id', '=', ligne.inscription_id.company_id.id),
                    ('location_id.usage', '=', 'internal'),
                ]).mapped('quantity')) if lot else 0.0

    @api.depends('quantite', 'quantite_inscrite', 'poids_inscrit')
    def _compute_poids(self):
        for ligne in self:
            reference = ligne.quantite_inscrite
            ligne.poids = (ligne.poids_inscrit * ligne.quantite / reference
                           if reference else 0.0)
            ligne.changee = abs(
                ligne.quantite - reference) > 0.00005
