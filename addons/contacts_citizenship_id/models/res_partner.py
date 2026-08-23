# -*- coding: utf-8 -*-

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ------------------------------------------------------------------
    # Naissance
    # ------------------------------------------------------------------
    birthdate = fields.Date(
        string='Date de Naissance',
        help="Cerfa 2093-SD — zones Q 007, Q 008 et Q 009 (jour, mois, année "
             "de naissance).\n\n"
             "Sévérité : NON BLOQUANTE. Absente, elle part en 00/00/0000 et "
             "l'anomalie est seulement signalée. Une date non numérique, elle, "
             "serait bloquante — le cas ne peut pas se produire ici, Odoo ne "
             "stocke qu'une date valide.\n\n"
             "Livre de police : aide à l'identification, lève les homonymes. "
             "Fortement recommandée.",
    )
    # Champ historique conservé (texte libre), remplacé par « Commune de naissance ».
    birthplace = fields.Char(
        string='Lieu de Naissance (texte libre)',
        help="Ancien champ (texte libre). Obsolète : remplacé par « Commune de "
             "naissance ». Conservé uniquement pour l'historique.",
    )

    birth_country_id = fields.Many2one(
        'res.country', string='Pays de naissance',
        help="Cerfa 2093-SD — n'a pas de zone à lui, mais commande trois "
             "zones : Q 010 prend « 99 » pour une naissance hors de France, "
             "Q 011 attend alors le code INSEE du pays et Q 012 son libellé.\n\n"
             "Sévérité : NON BLOQUANTE.\n\n"
             "Le « 99 » se déduit du pays de NAISSANCE, jamais du pays de "
             "l'adresse. Choix explicite, sans valeur par défaut.",
    )
    birth_department = fields.Char(
        string='Département de naissance', size=3,
        help="Cerfa 2093-SD — zone Q 010, département de naissance.\n\n"
             "Sévérité : NON BLOQUANTE. Le cahier des charges DGFiP tolère "
             "« 00 », en précisant « dans l'attente de la mise à jour du livre "
             "de police » : l'administration annonce là une évolution à venir, "
             "elle ne décrit pas une obligation actuelle. À ce jour, l'art. "
             "R321-3 du code pénal n'exige du registre ni la date ni le lieu "
             "de naissance — seuls le nom, les prénoms, la qualité, le domicile "
             "et les mentions de la pièce d'identité y figurent.\n\n"
             "Vaut 99 pour une naissance à l'étranger, valeur déduite du pays "
             "de naissance. Laissé vide, il est déclaré « 00 » comme le veut "
             "le cahier des charges. Champ masqué de la saisie.",
    )
    birth_insee_code = fields.Char(
        string='Code INSEE commune/pays de naissance', size=5,
        help="Cerfa 2093-SD — zone Q 011, code INSEE de la commune de "
             "naissance, ou code du pays pour une naissance à l'étranger.\n\n"
             "Sévérité : NON BLOQUANTE (« 000 si inconnu »).\n\n"
             "Champ masqué de la saisie.",
    )
    birth_city = fields.Char(
        string='Commune de naissance',
        help="Cerfa 2093-SD — zone Q 012, libellé de la commune de naissance "
             "(ou du pays pour une naissance hors de France).\n\n"
             "Sévérité : NON BLOQUANTE (« espace si inconnue »).\n\n"
             "Livre de police : aide à l'identification. Recommandé. "
             "Ex. : « Metz ». Naissance à l'étranger : laisser vide, le pays "
             "renseigné ci-dessus suffit, ou préciser la ville étrangère.",
    )

    # ------------------------------------------------------------------
    # Justificatif d'identité (art. R321-3 du code pénal : nature, numéro,
    # date de délivrance et autorité émettrice)
    # ------------------------------------------------------------------
    # Champ historique conservé pour compatibilité ; migré vers id_doc_number.
    id_proof = fields.Char(
        string="Justificatif d'identité (ancien champ)",
        help="Ancien champ. Obsolète : migré vers « Numéro de la pièce "
             "d'identité ». Conservé uniquement pour l'historique.",
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
        help="Livre de police (art. R321-3) : nature de la pièce. Obligatoire "
             "pour un vendeur particulier. Non repris au Cerfa 2093-SD, dont "
             "l'enregistrement Q ne comporte aucune zone « pièce d'identité ».",
    )
    id_doc_number = fields.Char(
        string="Numéro de la pièce d'identité",
        help="Livre de police (art. R321-3) : numéro de la pièce. Obligatoire "
             "pour un vendeur particulier. Non repris au Cerfa 2093-SD, dont "
             "l'enregistrement Q ne comporte aucune zone « pièce d'identité ».",
    )
    id_doc_issue_date = fields.Date(
        string="Date de délivrance",
        help="Livre de police (art. R321-3) : date de délivrance de la pièce. "
             "Obligatoire pour un vendeur particulier.",
    )
    id_doc_authority = fields.Char(
        string="Autorité de délivrance",
        help="Livre de police (art. R321-3) : administration émettrice de la "
             "pièce, telle qu'elle est mentionnée sur le titre. Ex. : "
             "« Préfecture de la Moselle », « Sous-préfecture de Sarreguemines », "
             "« Mairie de Metz », ou « Consulat de France à … » pour une pièce "
             "délivrée à l'étranger.\n\n"
             "Cas particulier — nouvelle carte d'identité française (format "
             "carte bancaire) : l'autorité n'y est plus imprimée. Saisir alors "
             "« Ministère de l'Intérieur », qui est l'autorité émettrice du "
             "titre ; à défaut, « République française ».\n\n"
             "Obligatoire pour un vendeur particulier.",
    )
    id_doc_complete = fields.Boolean(
        string="Pièce d'identité complète (R321-3)",
        compute='_compute_id_doc_complete', store=True,
        help="Vrai lorsque nature, numéro, date de délivrance et autorité sont "
             "tous renseignés (mentions obligatoires du livre de police).",
    )

    # Mentions obligatoires de la pièce d'identité au sens de l'art. R321-3 :
    # « la nature, le numéro et la date de délivrance de la pièce d'identité
    # produite […] avec l'indication de l'autorité qui l'a établie ». Le *lieu*
    # de délivrance n'est PAS exigé (le texte demande l'autorité émettrice), pas
    # plus que par le registre métaux précieux (CGI ann. IV, art. 56 J
    # quindecies, qui se limite aux nom, prénoms et adresse) ni par le Cerfa 2093-SD
    # (aucune zone « pièce d'identité » dans le dessin Q).
    _R321_3_ID_FIELDS = (
        'id_doc_type', 'id_doc_number', 'id_doc_issue_date',
        'id_doc_authority',
    )

    @api.depends('id_doc_type', 'id_doc_number', 'id_doc_issue_date',
                 'id_doc_authority')
    def _compute_id_doc_complete(self):
        for partner in self:
            partner.id_doc_complete = all(
                partner[fname] for fname in self._R321_3_ID_FIELDS
            )

    @api.constrains('id_doc_type', 'id_doc_number', 'id_doc_issue_date',
                    'id_doc_authority', 'is_company')
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
