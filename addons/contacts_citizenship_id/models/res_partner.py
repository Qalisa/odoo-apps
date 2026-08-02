# -*- coding: utf-8 -*-

from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ------------------------------------------------------------------
    # Naissance
    # ------------------------------------------------------------------
    birthdate = fields.Date(string='Date de Naissance')
    # Champ historique conservé (texte libre). Le format structuré ci-dessous
    # le remplace pour les usages réglementaires (déclaration DMET, livre de police).
    birthplace = fields.Char(string='Lieu de Naissance (texte libre)')

    birth_country_id = fields.Many2one(
        'res.country', string='Pays de naissance',
        default=lambda self: self.env.ref('base.fr', raise_if_not_found=False),
    )
    birth_department = fields.Char(
        string='Département de naissance', size=3,
        help="Code département (ex. 57). 99 pour une naissance à l'étranger.",
    )
    birth_insee_code = fields.Char(
        string='Code INSEE commune/pays de naissance', size=5,
        help="Code INSEE de la commune de naissance, ou code pays si né à l'étranger.",
    )
    birth_city = fields.Char(
        string='Commune de naissance',
        help="Libellé de la commune de naissance (ou du pays si né à l'étranger).",
    )

    # ------------------------------------------------------------------
    # Justificatif d'identité (art. R321-3 du code pénal : nature, numéro,
    # date de délivrance et autorité émettrice)
    # ------------------------------------------------------------------
    # Champ historique conservé pour compatibilité ; migré vers id_doc_number.
    id_proof = fields.Char(
        string="Justificatif d'identité (ancien champ)",
        help="Champ historique. Utilisez de préférence les zones structurées ci-dessous.",
    )
    id_doc_type = fields.Selection(
        selection=[
            ('cni', "Carte nationale d'identité"),
            ('passeport', 'Passeport'),
            ('permis', 'Permis de conduire'),
            ('sejour', 'Titre de séjour'),
            ('autre', 'Autre'),
        ],
        string="Nature de la pièce d'identité",
    )
    id_doc_number = fields.Char(string="Numéro de la pièce d'identité")
    id_doc_issue_date = fields.Date(string="Date de délivrance")
    id_doc_authority = fields.Char(string="Autorité de délivrance")

    @api.onchange('birth_country_id')
    def _onchange_birth_country_id(self):
        """Pré-remplit le département à 99 pour une naissance hors de France."""
        for partner in self:
            if partner.birth_country_id and partner.birth_country_id.code != 'FR':
                partner.birth_department = '99'
