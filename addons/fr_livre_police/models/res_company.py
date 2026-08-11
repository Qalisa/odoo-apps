# -*- coding: utf-8 -*-
"""Paramètres du registre, par établissement.

L'art. 56 J quaterdecies permet à un établissement principal de tenir le
registre pour l'ensemble de ses magasins « à condition de distinguer les
ouvrages qu'il détient lui-même de ceux détenus par les établissements
secondaires ». Chaque société porte donc sa propre date de bascule et sa
propre séquence de numéros d'ordre.
"""

from odoo import models, fields, api

#: Code de la séquence des numéros d'ordre, une par société.
SEQUENCE_CODE = 'livre.police.numero.ordre'


class ResCompany(models.Model):
    _inherit = 'res.company'

    police_start_date = fields.Date(
        string="Début du livre de police",
        help="Date à partir de laquelle les rachats alimentent le registre. "
             "Tant qu'elle est vide, le module reste inerte : aucun mouvement "
             "de stock n'est créé. Les objets détenus en coffre à cette date "
             "doivent y être inscrits par un inventaire d'ouverture.",
    )
    police_sequence_prefix = fields.Char(
        string="Préfixe des numéros d'ordre", size=8,
        help="Trois à huit caractères identifiant l'établissement, repris en "
             "tête du numéro d'ordre : METZ donne METZ-2026-00001.",
    )

    police_opening_date = fields.Datetime(
        string="Inventaire d'ouverture effectué le", readonly=True,
        help="Renseignée au premier inventaire d'ouverture. Empêche de le "
             "rejouer par mégarde.",
    )

    def _police_sequence(self):
        """Séquence de numéros d'ordre de la société, créée au besoin.

        Créée à la demande plutôt qu'à l'installation : une société ajoutée
        plus tard doit obtenir la sienne sans réinstaller le module.
        """
        self.ensure_one()
        Sequence = self.env['ir.sequence'].sudo()
        sequence = Sequence.search(
            [('code', '=', SEQUENCE_CODE), ('company_id', '=', self.id)], limit=1)
        if sequence:
            return sequence
        prefixe = self.police_sequence_prefix or self._police_default_prefix()
        return Sequence.create({
            'name': "Livre de police - %s" % self.name,
            'code': SEQUENCE_CODE,
            'company_id': self.id,
            'prefix': '%s-%%(range_year)s-' % prefixe,
            'padding': 5,
            'use_date_range': True,
            'implementation': 'no_gap',
        })

    def _police_default_prefix(self):
        """Préfixe déduit du code de l'entrepôt, à défaut du nom."""
        self.ensure_one()
        entrepot = self.env['stock.warehouse'].sudo().search(
            [('company_id', '=', self.id)], limit=1)
        source = entrepot.code or self.name
        lettres = ''.join(c for c in source.upper() if c.isalnum())
        return lettres[:8] or 'REG'

    @api.model
    def _police_next_number(self, company):
        """Numéro d'ordre suivant pour cette société."""
        return company._police_sequence().next_by_id()
