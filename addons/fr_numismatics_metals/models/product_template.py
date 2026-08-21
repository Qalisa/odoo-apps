# -*- coding: utf-8 -*-
"""Caractéristiques métal d'un article du catalogue.

Ces champs portent les mentions que le registre exige de chaque objet :

* **CGI, annexe IV, art. 56 J quindecies** — le registre indique « la nature,
  le nombre, le poids, le titre, la date d'entrée et de sortie et l'origine »
  des matières ou ouvrages, « afin de permettre leur identification
  individuelle ». Nature, poids et titre se tiennent donc au catalogue ;
* **code pénal, art. R321-3 3°** — « la nature, la provenance et la
  description des objets acquis ou détenus en vue de la vente ou de
  l'échange ». La description est propre à chaque achat (elle se saisit en
  note sous la ligne) ; la nature, elle, est un attribut de l'article.

Sans ces champs, le poids d'une ligne d'achat n'est pas calculable dès que la
quantité compte des pièces plutôt que des grammes — et un registre sans poids
n'est pas tenu.

(L'art. R321-4, longtemps cité ici, ne traite pas de la désignation mais du
**numéro d'ordre** porté sur le registre et sur l'objet ; il est cité à sa
place dans `fr_livre_police`.)

Pourquoi ne pas réutiliser le champ standard ``weight`` (onglet Logistique) ?

* il est exprimé dans l'unité de ``product.weight_in_lbs``, soit **kg** ici,
  et arrondi à la précision décimale ``Stock Weight`` — **2 décimales** en
  production. Un 20 Francs Or (6,4516 g = 0,0064516 kg) y serait stocké à
  0,01 kg, soit **10 g** : 55 % d'erreur, et toutes les pièces d'argent
  légères tomberaient à zéro ;
* il ne porte qu'un poids : ni la nature, ni le titre, ni surtout le *régime*
  de saisie de la quantité, dont dépend tout le calcul du poids des lignes.

Le poids unitaire vit donc ici, en **grammes**, unité du métier et du registre.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

from ..tools import metals

MODE_SELECTION = [
    ('gram', "Au gramme (quantité = poids)"),
    ('unit', "À la pièce (poids unitaire fixe)"),
    ('lot', "Au lot (poids saisi à la ligne)"),
]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    metal_regulated = fields.Boolean(
        string="Soumis au livre de police",
        compute='_compute_metal_regulated', store=True, readonly=False,
        help="Coché d'office sur les biens : un objet acheté d'occasion doit "
             "figurer au registre des achats, ventes, réceptions et "
             "livraisons de métaux précieux (art. 537 du code général des "
             "impôts).\n\n"
             "Tant que la case est cochée, l'enregistrement de l'article "
             "exige les mentions que le registre porte sur chaque objet : "
             "nature, titre et poids (CGI, ann. IV, art. 56 J quindecies).\n\n"
             "Décocher pour les articles de gestion — remise, acompte, "
             "arrondi, régularisation — qui ne désignent aucun objet et n'ont "
             "donc rien à faire au registre.",
    )
    metal_nature = fields.Many2one(
        'metal.nature', string="Nature du métal", ondelete='restrict', index=True,
        help="« La nature […] des matières ou ouvrages » : première des "
             "mentions exigées par l'art. 56 J quindecies de l'annexe IV au "
             "CGI, reprise par l'art. R321-3 3° du code pénal pour la "
             "description de l'objet acquis.\n\n"
             "Obligatoire pour tout objet soumis au registre. Laissé vide sur "
             "les articles de gestion (remise, arrondi, acompte, "
             "régularisation). La liste des natures se complète librement.",
    )
    metal_fineness = fields.Float(
        string="Titre (millièmes)", digits=(5, 1),
        help="« Le titre » des matières ou ouvrages (CGI, ann. IV, art. 56 J "
             "quindecies), exprimé en millièmes : 750 pour l'or 18 carats, "
             "900 pour les pièces de l'Union latine, 999 pour un lingot.\n\n"
             "Obligatoire, sauf au régime « au lot » : un lot hétérogène n'a "
             "pas de titre unique, et en afficher un serait inexact. Le "
             "détail se porte alors dans la description de l'achat.",
    )
    metal_quantity_mode = fields.Selection(
        MODE_SELECTION, string="Régime de quantité",
        help="Détermine comment le poids d'une ligne d'achat se déduit de sa "
             "quantité — et le poids est une mention obligatoire du registre "
             "(CGI, ann. IV, art. 56 J quindecies).\n\n"
             "Obligatoire pour tout objet soumis au registre : sans lui, une "
             "ligne d'achat n'a pas de poids calculable.",
    )
    metal_unit_weight = fields.Float(
        string="Poids unitaire (g)", digits=(12, 4),
        help="Poids d'une pièce ou d'un lingotin, en grammes — c'est de lui "
             "que se déduit « le poids » porté au registre (CGI, ann. IV, "
             "art. 56 J quindecies).\n\n"
             "Obligatoire au régime « à la pièce », sans objet pour les "
             "autres : au gramme la quantité vaut le poids, au lot le poids "
             "se saisit sur chaque ligne d'achat.",
    )
    metal_is_object = fields.Boolean(
        string="Objet soumis au livre de police", compute='_compute_metal_is_object',
        store=True,
        help="Vrai dès qu'un régime de quantité est renseigné.",
    )
    metal_weight_undetermined = fields.Boolean(
        string="Poids non déductible", compute='_compute_metal_is_object', store=True,
        help="Objet en métal dont le poids ne peut pas se déduire de la "
             "quantité : lot hétérogène, ou pièce dont le poids unitaire "
             "reste à renseigner. Le poids devra être saisi ligne à ligne.",
    )

    # Un bien est présumé soumis au registre ; un service ne l'est jamais.
    # `readonly=False` laisse le dernier mot à l'utilisateur : la case se
    # décoche à la main, et son choix survit à tout enregistrement ultérieur.
    @api.depends('type')
    def _compute_metal_regulated(self):
        for product in self:
            product.metal_regulated = product.type == 'consu'

    def _police_juge_la_saisie(self):
        """La contrainte ne juge que ce qu'une personne a saisi.

        Elle se tait dans deux cas.

        **Pendant le chargement des modules.** À l'installation, Odoo calcule
        `metal_regulated` pour tout le catalogue existant : chaque bien déjà
        présent devient soumis au registre sans porter aucune des mentions,
        qui n'existaient pas la veille. Refuser à cet instant n'exprimerait
        rien — personne n'a rien déclaré — et ferait échouer l'installation.

        **Devant une écriture en super-utilisateur.** Odoo crée des articles
        pour son propre compte, et les scripts de reprise aussi. Leur opposer
        une mention de registre n'a pas de sens : ces articles ne désignent
        aucun objet acheté, et la contrainte y bloquait des fonctionnements
        internes sans rien protéger.

        Ce que cela ne rouvre pas : un import CSV et une duplication depuis
        l'interface s'exécutent sous l'identité de l'utilisateur, jamais en
        super-utilisateur. Ils restent contrôlés, ce qui était la raison
        d'être de cette contrainte.

        Les articles qui échappent ainsi au contrôle restent présumés soumis
        au registre et figurent à l'écran « Articles à caractériser ».
        """
        return self.env.registry.ready and not self.env.su

    @api.constrains('metal_regulated', 'metal_nature', 'metal_quantity_mode',
                    'metal_unit_weight', 'metal_fineness')
    def _check_police_mentions(self):
        """Un objet soumis au registre porte ses mentions dès le catalogue.

        Les exiger dans la vue ne suffit pas : un import ou une duplication
        passent à côté, et le manque n'apparaît alors qu'au comptoir — au
        moment où l'on ne peut plus ni peser ni titrer ce qui vient d'être
        acheté.

        Le registre veut, pour chaque objet, « la nature, le nombre, le poids,
        le titre » (CGI, ann. IV, art. 56 J quindecies). Le nombre vient de la
        ligne d'achat ; les trois autres se tiennent ici.

        Voir `_police_juge_la_saisie` pour ce que la contrainte laisse passer.
        """
        if not self._police_juge_la_saisie():
            return
        for product in self:
            if not product.metal_regulated:
                continue
            manques = []
            if not product.metal_nature:
                manques.append(_("la nature du métal"))
            if not product.metal_quantity_mode:
                manques.append(_("le régime de quantité (dont dépend le poids)"))
            elif (product.metal_quantity_mode == 'unit'
                    and not product.metal_unit_weight):
                manques.append(_("le poids unitaire, exigé au régime « à la "
                                 "pièce »"))
            # Un lot hétérogène n'a pas de titre unique : lui en imposer un
            # serait porter au registre une mention fausse.
            if (product.metal_quantity_mode != 'lot'
                    and not product.metal_fineness):
                manques.append(_("le titre en millièmes"))
            if manques:
                raise ValidationError(_(
                    "« %(article)s » est soumis au livre de police, qui exige "
                    "de chaque objet sa nature, son poids et son titre "
                    "(CGI, ann. IV, art. 56 J quindecies). Il manque : "
                    "%(manques)s.\n\n"
                    "S'il s'agit d'un article de gestion — remise, acompte, "
                    "arrondi, régularisation — décochez « Soumis au livre de "
                    "police » : il ne désigne alors aucun objet acheté.",
                    article=product.display_name,
                    manques=", ".join(manques)))

    @api.depends('metal_quantity_mode', 'metal_unit_weight')
    def _compute_metal_is_object(self):
        for product in self:
            mode = product.metal_quantity_mode
            product.metal_is_object = bool(mode)
            product.metal_weight_undetermined = bool(mode) and metals.derive_weight(
                mode, product.metal_unit_weight, 1.0) is None
