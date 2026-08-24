# -*- coding: utf-8 -*-
"""Ce dont le registre a besoin et qu'Odoo ne sait pas : les vocabulaires.

Deux mentions obligatoires du registre ne se déduisent d'aucune donnée
existante — la provenance de l'objet (c. pén., art. R321-3 3°) et la qualité
du vendeur (art. R321-3 1°). Elles sont déclarées au comptoir et repartent
avec le vendeur.

Ce modèle abstrait porte ce que les deux ont en commun : une liste ordonnée,
administrable, fermée à la variante d'écriture, et dont **une valeur employée
ne se renomme plus**. Ce dernier point n'est pas une précaution de style :
renommer « Héritage ou succession » en « Achat antérieur » réécrirait d'un
coup tout ce qui la porte, silencieusement. On archive donc au lieu de
renommer — la valeur quitte les listes de saisie, ce qui la portait la garde.

Chaque vocabulaire dit ensuite ce qu'« employée » veut dire chez lui, en
implémentant ``_police_usage_domain``.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..tools.referentiel import cle_de_comparaison


class LivrePoliceReferentiel(models.AbstractModel):
    _name = 'livre.police.referentiel'
    _description = "Valeur de référence du livre de police"
    _order = 'sequence, name'

    #: Ce que compte ``usage_count``, au singulier puis au pluriel.
    _police_usage_noms = ("enregistrement", "enregistrements")
    #: Ce que renommer une valeur employée ferait, dit au responsable.
    _police_effet_renommage = "réécrirait ces enregistrements"

    name = fields.Char(string="Libellé", required=True)
    sequence = fields.Integer(string="Ordre", default=10)
    active = fields.Boolean(
        string="Actif", default=True,
        help="Décocher retire la valeur des listes de saisie sans toucher à "
             "ce qui la porte déjà.",
    )
    note = fields.Char(
        string="Précision",
        help="Aide à la saisie, affichée au comptoir. N'est pas reportée au "
             "registre.",
    )
    usage_count = fields.Integer(
        string="Emplois", compute='_compute_usage_count',
        help="Nombre d'enregistrements portant cette valeur. Au-delà de zéro, "
             "le libellé est figé.",
    )

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Cette valeur existe déjà : deux libellés identiques rendraient le "
         "registre ambigu."),
    ]

    # ------------------------------------------------------------------
    # Emploi
    # ------------------------------------------------------------------
    def _police_usage_domain(self):
        """Où cette valeur est employée : ``(nom du modèle, domaine)``."""
        raise NotImplementedError

    def _police_search_usage(self):
        self.ensure_one()
        modele, domaine = self._police_usage_domain()
        return self.env[modele].sudo().with_context(
            active_test=False).search_count(domaine)

    def _compute_usage_count(self):
        for valeur in self:
            valeur.usage_count = valeur._police_search_usage()

    def _police_phrase_usage(self, nb):
        singulier, pluriel = self._police_usage_noms
        return "%s %s" % (nb, singulier if nb == 1 else pluriel)

    # ------------------------------------------------------------------
    # Unicité au-delà de l'orthographe
    # ------------------------------------------------------------------
    @api.model
    def _police_doublon(self, libelle, hormis=None):
        """Valeur existante que ``libelle`` ne ferait que réécrire."""
        cle = cle_de_comparaison(libelle)
        if not cle:
            return self.browse()
        candidates = self.with_context(active_test=False).search([])
        if hormis:
            candidates -= hormis
        for valeur in candidates:
            if cle_de_comparaison(valeur.name) == cle:
                return valeur
        return self.browse()

    def _police_check_doublon(self, libelle, hormis=None):
        jumelle = self._police_doublon(libelle, hormis=hormis)
        if jumelle:
            raise UserError(_(
                "« %(nouveau)s » ne se distingue de « %(existant)s » que par "
                "l'orthographe. Employez la valeur existante — %(etat)s.",
                nouveau=libelle, existant=jumelle.name,
                etat=("elle est active" if jumelle.active
                      else "elle est archivée, réactivez-la depuis la liste "
                           "de configuration")))

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('name'):
                self._police_check_doublon(values['name'])
        return super().create(vals_list)

    def write(self, values):
        """Le libellé se fige dès qu'un enregistrement le porte."""
        if 'name' in values:
            for valeur in self:
                if valeur.name == values['name']:
                    continue
                emplois = valeur._police_search_usage()
                if emplois:
                    raise UserError(_(
                        "« %(nom)s » figure déjà sur %(usage)s : la renommer "
                        "%(effet)s. Archivez-la et créez la nouvelle valeur.",
                        nom=valeur.name,
                        usage=valeur._police_phrase_usage(emplois),
                        effet=valeur._police_effet_renommage))
                self._police_check_doublon(values['name'], hormis=valeur)
        return super().write(values)

    def unlink(self):
        for valeur in self:
            emplois = valeur._police_search_usage()
            if emplois:
                raise UserError(_(
                    "« %(nom)s » figure sur %(usage)s et ne peut pas être "
                    "supprimée. Archivez-la pour la retirer de la saisie.",
                    nom=valeur.name,
                    usage=valeur._police_phrase_usage(emplois)))
        return super().unlink()
