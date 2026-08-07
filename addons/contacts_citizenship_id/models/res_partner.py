# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


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
    id_doc_issue_place = fields.Char(
        string="Lieu de délivrance",
        help="Lieu de délivrance de la pièce. L'art. R321-3 impose : nature, "
             "numéro, date ET lieu de délivrance, et autorité émettrice.",
    )

    id_doc_complete = fields.Boolean(
        string="Pièce d'identité complète (R321-3)",
        compute='_compute_id_doc_complete', store=True,
        help="Vrai lorsque nature, numéro, date, lieu de délivrance et autorité "
             "sont tous renseignés (mentions obligatoires du livre de police).",
    )

    # Mentions obligatoires de la pièce d'identité au sens de l'art. R321-3.
    _R321_3_ID_FIELDS = (
        'id_doc_type', 'id_doc_number', 'id_doc_issue_date',
        'id_doc_issue_place', 'id_doc_authority',
    )

    @api.depends('id_doc_type', 'id_doc_number', 'id_doc_issue_date',
                 'id_doc_issue_place', 'id_doc_authority')
    def _compute_id_doc_complete(self):
        for partner in self:
            partner.id_doc_complete = all(
                partner[fname] for fname in self._R321_3_ID_FIELDS
            )

    @api.constrains('id_doc_type', 'id_doc_number', 'id_doc_issue_date',
                    'id_doc_issue_place', 'id_doc_authority', 'is_company')
    def _check_id_doc_r321_3(self):
        """Cohérence R321-3 : si une pièce d'identité est saisie sur une personne
        physique, toutes ses mentions obligatoires doivent l'être.

        On n'impose pas la *présence* d'une pièce sur tous les contacts (cela
        casserait la création d'individus non concernés) : l'obligation « le
        vendeur DOIT présenter une pièce » relève du flux d'achat (avoir), pas
        de la fiche contact.
        """
        labels = {
            'id_doc_type': "la nature",
            'id_doc_number': "le numéro",
            'id_doc_issue_date': "la date de délivrance",
            'id_doc_issue_place': "le lieu de délivrance",
            'id_doc_authority': "l'autorité de délivrance",
        }
        for partner in self:
            if partner.is_company:
                continue
            started = any(partner[fname] for fname in self._R321_3_ID_FIELDS)
            if not started:
                continue
            missing = [labels[fname] for fname in self._R321_3_ID_FIELDS
                       if not partner[fname]]
            if missing:
                raise ValidationError(_(
                    "Pièce d'identité incomplète pour « %(name)s » "
                    "(art. R321-3) : renseigner %(missing)s.",
                    name=partner.display_name,
                    missing=", ".join(missing),
                ))

    @api.onchange('birth_country_id')
    def _onchange_birth_country_id(self):
        """Pré-remplit le département à 99 pour une naissance hors de France."""
        for partner in self:
            if partner.birth_country_id and partner.birth_country_id.code != 'FR':
                partner.birth_department = '99'
