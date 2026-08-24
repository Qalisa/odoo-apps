# -*- coding: utf-8 -*-
"""D'où vient l'objet — vocabulaire du registre.

L'art. R321-3 3° du code pénal veut de chaque objet acquis « la nature, la
provenance et la description ». La provenance ne se déduit d'aucune donnée
d'Odoo : elle est déclarée par le vendeur, au comptoir, et elle disparaît avec
lui.

La saisir en texte libre reviendrait à ne pas la tenir. « Succession »,
« succession », « héritage » et « SUCC. » cessent d'être une information dès
qu'il faut retrouver, contrôler ou totaliser. D'où une liste, administrable
mais fermée à la variante orthographique.

**Une valeur employée ne se renomme plus.** L'art. R321-6 veut un registre
« sans blanc, rature ni abréviation » et l'art. R321-6-1 l'intangibilité des
données : si le libellé pouvait changer, renommer « Héritage » en « Achat »
réécrirait silencieusement toutes les lignes passées, sans laisser de trace.
On archive donc au lieu de renommer — la valeur quitte les listes de saisie,
les pièces déjà comptabilisées gardent la leur.

Le comptoir peut créer une valeur à la volée, parce qu'une provenance
imprévue se présentera. Ce qu'il ne peut pas, c'est en créer une qui n'est
qu'une variante d'écriture d'une valeur existante : le doublon est renvoyé
vers l'original, fût-il archivé.
"""

import unicodedata

from odoo import models, fields, api, _
from odoo.exceptions import UserError


# Mots qui relient sans désigner. « Héritage ou succession », « Héritage /
# succession » et « Héritage et succession » nomment la même provenance : les
# retenir ferait entrer trois libellés pour une seule information.
LIAISONS = frozenset((
    'a', 'au', 'aux', 'd', 'de', 'des', 'du', 'en', 'et', 'l', 'la', 'le',
    'les', 'ou', 'par', 'pour', 'sur', 'un', 'une',
))


def cle_de_comparaison(libelle):
    """Forme normalisée d'un libellé, pour ne pas créer deux fois le même.

    Ni la casse, ni les accents, ni la ponctuation, ni les mots de liaison ne
    distinguent deux provenances. Ce qui reste est l'ensemble des mots
    porteurs, trié : « HÉRITAGE / SUCCESSION » et « Héritage ou succession »
    donnent la même clé et ne peuvent pas coexister au registre.

    La comparaison reste orthographique. Elle ne connaît pas les synonymes :
    « Legs » passera à côté de « Héritage ou succession », et c'est au
    responsable de l'arbitrer depuis Ventes ▸ Configuration ▸ Provenances.
    """
    texte = unicodedata.normalize('NFKD', libelle or '')
    texte = ''.join(c for c in texte if not unicodedata.combining(c))
    mots = ''.join(c if c.isalnum() else ' ' for c in texte.lower()).split()
    porteurs = [mot for mot in mots if mot not in LIAISONS]
    return ' '.join(sorted(porteurs or mots))


class LivrePoliceProvenance(models.Model):
    _name = 'livre.police.provenance'
    _description = "Provenance déclarée au livre de police"
    _order = 'sequence, name'

    name = fields.Char(string="Libellé", required=True)
    sequence = fields.Integer(string="Ordre", default=10)
    active = fields.Boolean(
        string="Actif", default=True,
        help="Décocher retire la valeur des listes de saisie sans toucher aux "
             "pièces qui la portent déjà.",
    )
    note = fields.Char(
        string="Précision",
        help="Aide à la saisie, affichée au comptoir. N'est pas reportée au "
             "registre.",
    )
    line_count = fields.Integer(
        string="Lignes comptabilisées", compute='_compute_line_count',
        help="Nombre de lignes de pièces comptabilisées portant cette "
             "provenance. Au-delà de zéro, le libellé est figé.",
    )

    _sql_constraints = [
        ('name_unique', 'unique(name)',
         "Cette provenance existe déjà : deux libellés identiques rendraient "
         "le registre ambigu."),
    ]

    # ------------------------------------------------------------------
    # Emploi au registre
    # ------------------------------------------------------------------
    def _police_lines_domain(self):
        """Lignes de registre portant ces provenances.

        Seules comptent les pièces **comptabilisées** : un devis se corrige,
        une écriture postée ne se corrige plus.
        """
        return [('parent_state', '=', 'posted'),
                ('police_origin_id', 'in', self.ids)]

    def _compute_line_count(self):
        Ligne = self.env['account.move.line'].sudo()
        for valeur in self:
            valeur.line_count = Ligne.search_count(valeur._police_lines_domain())

    def _police_employee(self):
        self.ensure_one()
        return bool(self.env['account.move.line'].sudo().search_count(
            self._police_lines_domain()))

    # ------------------------------------------------------------------
    # Unicité au-delà de l'orthographe
    # ------------------------------------------------------------------
    @api.model
    def _police_doublon(self, libelle, hormis=None):
        """Provenance existante que ``libelle`` ne ferait que réécrire."""
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
                      else "elle est archivée, réactivez-la depuis "
                           "Ventes ▸ Configuration ▸ Provenances")))

    @api.model_create_multi
    def create(self, vals_list):
        for values in vals_list:
            if values.get('name'):
                self._police_check_doublon(values['name'])
        return super().create(vals_list)

    def write(self, values):
        """Le libellé se fige dès qu'une pièce comptabilisée le porte."""
        if 'name' in values:
            for valeur in self:
                if valeur.name == values['name']:
                    continue
                if valeur._police_employee():
                    raise UserError(_(
                        "« %(nom)s » figure déjà sur %(nb)s ligne(s) "
                        "comptabilisée(s) : la renommer réécrirait ces "
                        "lignes du registre. Archivez-la et créez la "
                        "nouvelle valeur.",
                        nom=valeur.name, nb=valeur.line_count))
                self._police_check_doublon(values['name'], hormis=valeur)
        return super().write(values)

    def unlink(self):
        for valeur in self:
            if valeur._police_employee():
                raise UserError(_(
                    "« %(nom)s » figure sur %(nb)s ligne(s) comptabilisée(s) "
                    "du registre et ne peut pas être supprimée. Archivez-la "
                    "pour la retirer de la saisie.",
                    nom=valeur.name, nb=valeur.line_count))
        return super().unlink()
