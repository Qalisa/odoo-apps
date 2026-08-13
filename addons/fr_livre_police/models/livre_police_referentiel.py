# -*- coding: utf-8 -*-
"""Vocabulaires du registre : provenances et qualités.

Deux mentions obligatoires ne se déduisent d'aucune donnée d'Odoo — la
provenance de l'objet (art. R321-3 3° du code pénal, art. 56 J quindecies de
l'annexe IV au CGI) et la qualité du vendeur (art. R321-3 1°). Les saisir en
texte libre revient à ne pas les tenir : « Succession », « succession »,
« héritage » et « SUCC. » cessent d'être une information dès qu'il faut
retrouver, contrôler ou totaliser.

D'où ces référentiels, choisis dans une liste fermée mais administrable.

**Une valeur employée ne se renomme plus.** R321-6 veut un registre « sans
blanc, rature ni abréviation », R321-6-1 l'intangibilité des données : si le
libellé pouvait changer, renommer « Héritage » en « Achat » réécrirait
silencieusement toutes les lignes passées, sans laisser de trace. On archive
donc au lieu de renommer — la valeur disparaît des listes de saisie, les
lignes déjà inscrites gardent la leur.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class LivrePoliceReferentiel(models.AbstractModel):
    _name = 'livre.police.referentiel'
    _description = "Valeur de référence du livre de police"
    _order = 'sequence, name'

    name = fields.Char(string="Libellé", required=True)
    sequence = fields.Integer(string="Ordre", default=10)
    active = fields.Boolean(
        string="Actif", default=True,
        help="Décocher retire la valeur des listes de saisie sans toucher aux "
             "lignes du registre qui la portent déjà.",
    )
    note = fields.Char(
        string="Précision",
        help="Aide à la saisie, affichée au comptoir. N'est pas reportée au "
             "registre.",
    )
    lot_count = fields.Integer(
        string="Lignes du registre", compute='_compute_lot_count',
        help="Nombre de lignes déjà inscrites au registre avec cette valeur.",
    )

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Cette valeur existe déjà : deux libellés identiques rendraient le "
         "registre ambigu."),
    ]

    # ------------------------------------------------------------------
    # Emploi au registre
    # ------------------------------------------------------------------
    def _police_lots_domain(self):
        """Domaine des lots inscrits au registre portant ces valeurs."""
        raise NotImplementedError

    def _compute_lot_count(self):
        Lot = self.env['stock.lot'].sudo()
        for valeur in self:
            valeur.lot_count = Lot.search_count(valeur._police_lots_domain())

    def _police_employee(self):
        self.ensure_one()
        return bool(self.env['stock.lot'].sudo().search_count(
            self._police_lots_domain()))

    def write(self, values):
        """Le libellé se fige dès qu'une ligne du registre le porte."""
        if 'name' in values:
            for valeur in self:
                if valeur.name != values['name'] and valeur._police_employee():
                    raise UserError(_(
                        "« %(nom)s » figure déjà sur %(nb)s ligne(s) du livre "
                        "de police : la renommer réécrirait ces lignes. "
                        "Archivez-la et créez la nouvelle valeur.",
                        nom=valeur.name, nb=valeur.lot_count))
        return super().write(values)

    def unlink(self):
        for valeur in self:
            if valeur._police_employee():
                raise UserError(_(
                    "« %(nom)s » figure sur %(nb)s ligne(s) du livre de "
                    "police et ne peut pas être supprimée. Archivez-la pour "
                    "la retirer de la saisie.",
                    nom=valeur.name, nb=valeur.lot_count))
        return super().unlink()


class LivrePoliceProvenance(models.Model):
    _name = 'livre.police.provenance'
    _inherit = 'livre.police.referentiel'
    _description = "Provenance déclarée au livre de police"

    def _police_lots_domain(self):
        return [('police_registered', '=', True),
                ('police_origin_id', 'in', self.ids)]


class LivrePoliceQualite(models.Model):
    _name = 'livre.police.qualite'
    _inherit = 'livre.police.referentiel'
    _description = "Qualité ou profession du vendeur"

    representant = fields.Boolean(
        string="Qualité de représentant",
        help="Vrai pour les qualités par lesquelles une personne agit au nom "
             "d'une société — gérant, président, mandataire. L'art. R321-3 "
             "emploie le mot « qualité » dans les deux sens : la profession "
             "pour le vendeur particulier (2° du modèle de registre : "
             "« qualité ou profession »), la fonction pour le représentant "
             "d'une personne morale.",
    )

    def _police_lots_domain(self):
        return [('police_registered', '=', True),
                ('police_seller_qualite_id', 'in', self.ids)]
