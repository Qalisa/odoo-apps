# -*- coding: utf-8 -*-
"""Journal chaîné des événements du registre.

R321-6-1 : « Le traitement automatisé garantit l'intégrité, l'intangibilité
et la sécurité des données enregistrées. » R321-6, pour le registre papier :
« sans blanc, rature ni abréviation ». Un registre modifiable n'est pas un
registre.

Interdire toute modification serait pourtant faux : le mode de règlement
n'est pas connu au comptoir, une provenance se précise. Un registre légal ne
gèle pas la vérité, il **trace** ses corrections — on n'efface pas une ligne,
on en ajoute une qui rectifie.

D'où ce journal : chaque entrée, chaque sortie, chaque correction y est
inscrite avec l'état des mentions à cet instant, et chaînée à la précédente
par une empreinte SHA-256. Modifier un événement passé casse la chaîne de
tous les suivants, et le contrôle d'intégrité le montre. Le journal est en
ajout seul : ni écriture, ni suppression, pour personne.

Les lignes du registre restent lisibles sur le lot ; ce journal en est la
preuve.
"""

import hashlib
import json

from odoo import models, fields, api, _
from odoo.exceptions import UserError

#: Mentions dont la modification doit laisser une trace.
MENTIONS = (
    'police_seller_id', 'police_seller_qualite_id', 'police_origin_id',
    'police_description', 'police_weight', 'police_quantity',
    'police_fineness', 'police_purchase_price', 'police_payment_mode',
)


class LivrePoliceEvenement(models.Model):
    _name = 'livre.police.evenement'
    _description = "Événement du livre de police"
    _order = 'company_id, sequence_number'

    lot_id = fields.Many2one(
        'stock.lot', string="Objet", required=True, ondelete='restrict',
        index=True)
    company_id = fields.Many2one(
        'res.company', string="Établissement", required=True, index=True)
    event_type = fields.Selection(
        [('ouverture', "Ouverture"), ('entree', "Entrée"),
         ('sortie', "Sortie"), ('correction', "Correction")],
        string="Nature", required=True)
    event_date = fields.Datetime(string="Date de l'événement", required=True)
    description = fields.Char(string="Détail")
    payload = fields.Text(
        string="Mentions", required=True,
        help="État des mentions du registre au moment de l'événement, "
             "sous une forme normalisée servant au calcul de l'empreinte.")
    sequence_number = fields.Integer(
        string="Rang", required=True, index=True,
        help="Position dans la chaîne, sans trou, par établissement.")
    previous_hash = fields.Char(string="Empreinte précédente")
    current_hash = fields.Char(string="Empreinte", required=True, index=True)
    user_id = fields.Many2one('res.users', string="Opérateur", required=True)

    _sql_constraints = [
        ('rang_unique', 'unique(company_id, sequence_number)',
         "Deux événements ne peuvent pas occuper le même rang."),
    ]

    # ------------------------------------------------------------------
    # Ajout seul
    # ------------------------------------------------------------------
    def write(self, values):
        raise UserError(_(
            "Le journal du livre de police est en ajout seul : un événement "
            "inscrit ne se modifie pas. Enregistrez une correction."))

    def unlink(self):
        raise UserError(_(
            "Le journal du livre de police est en ajout seul : un événement "
            "inscrit ne s'efface pas."))

    # ------------------------------------------------------------------
    # Chaînage
    # ------------------------------------------------------------------
    @api.model
    def _empreinte(self, rang, empreinte_precedente, contenu):
        """SHA-256 du rang, de l'empreinte précédente et du contenu."""
        base = "%s|%s|%s" % (rang, empreinte_precedente or '', contenu)
        return hashlib.sha256(base.encode('utf-8')).hexdigest()

    @api.model
    def _inscrire(self, lot, event_type, event_date, description=False):
        """Ajoute un événement au bout de la chaîne de l'établissement."""
        journal = self.sudo()
        societe = lot.company_id
        dernier = journal.search(
            [('company_id', '=', societe.id)], order='sequence_number desc',
            limit=1)
        rang = (dernier.sequence_number or 0) + 1
        contenu = lot._police_mentions_normalisees()
        return journal.create({
            'lot_id': lot.id,
            'company_id': societe.id,
            'event_type': event_type,
            'event_date': event_date or fields.Datetime.now(),
            'description': description,
            'payload': contenu,
            'sequence_number': rang,
            'previous_hash': dernier.current_hash or False,
            'current_hash': self._empreinte(rang, dernier.current_hash, contenu),
            'user_id': self.env.user.id,
        })

    # ------------------------------------------------------------------
    # Contrôle d'intégrité
    # ------------------------------------------------------------------
    @api.model
    def _verifier_chaine(self, company):
        """Recalcule la chaîne et renvoie le premier rang en défaut, ou None."""
        evenements = self.sudo().search(
            [('company_id', '=', company.id)], order='sequence_number')
        attendu_rang, empreinte = 1, False
        for evenement in evenements:
            if evenement.sequence_number != attendu_rang:
                return (evenement, _("rang %s attendu, %s trouvé — un "
                                     "événement a été retiré",
                                     attendu_rang, evenement.sequence_number))
            if evenement.previous_hash != (empreinte or False):
                return (evenement, _("l'empreinte précédente ne correspond pas"))
            recalcul = self._empreinte(
                evenement.sequence_number, evenement.previous_hash,
                evenement.payload)
            if recalcul != evenement.current_hash:
                return (evenement, _("les mentions ont été modifiées après "
                                     "inscription"))
            attendu_rang += 1
            empreinte = evenement.current_hash
        return None

    @api.model
    def action_verifier_integrite(self):
        """Contrôle la chaîne de chaque établissement et rend un compte."""
        lignes = []
        for societe in self.env['res.company'].search([]):
            total = self.sudo().search_count([('company_id', '=', societe.id)])
            if not total:
                continue
            defaut = self._verifier_chaine(societe)
            if defaut:
                evenement, motif = defaut
                lignes.append(_("%s : ROMPUE au rang %s (%s) — %s",
                                societe.name, evenement.sequence_number,
                                evenement.lot_id.name, motif))
            else:
                lignes.append(_("%s : intègre, %s événement(s)",
                                societe.name, total))
        if not lignes:
            lignes = [_("Aucun événement inscrit au journal.")]
        rompue = any("ROMPUE" in ligne for ligne in lignes)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Intégrité du livre de police"),
                'message': "\n".join(lignes),
                'type': 'danger' if rompue else 'success',
                'sticky': True,
            },
        }
