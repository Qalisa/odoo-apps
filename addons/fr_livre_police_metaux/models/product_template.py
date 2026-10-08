# -*- coding: utf-8 -*-
"""Quels articles réclament une description au rachat.

Le registre veut « la nature, la provenance et la description des objets
acquis » (art. R321-3 3° du code pénal). Les deux dernières mentions tiennent
dans la même phrase, mais elles ne manquent pas de la même façon.

**La provenance** n'est jamais donnée par la désignation de l'article : elle
est déclarée par le vendeur, et rien d'autre ne la fournit. Elle est donc due
de tout article inscrit au registre, et suit « Soumis au livre de police »
(``metal_regulated``) — aucune case supplémentaire à cocher.

**La description** est déjà donnée par la désignation dès que l'article
désigne un type catalogué : « 20 FRANCS OR » dit la nature, le diamètre, le
millésime et l'effigie mieux qu'une phrase saisie au comptoir. Elle ne
manque que là où l'article ne dit rien de l'objet — un rachat d'or au
gramme, un lot de pièces, une ligne d'argent en vrac.

Ce tri-là ne se devine pas : il se déclare, article par article, par la case
ci-dessous. Une case non cochée n'est pas un oubli du paramétrage, c'est
l'affirmation que la désignation suffit à décrire ce qui entre.
"""

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Le nom du champ dit encore « required » seul : il précède la séparation
    # des deux exigences, et le renommer imposerait une migration de colonne
    # sur une base en production pour un gain de lecture.
    police_description_required = fields.Boolean(
        string="Description des objets obligatoire au rachat",
        help="Coché, un rachat portant cet article ne peut être confirmé ni "
             "comptabilisé sans que les objets soient décrits, ligne par "
             "ligne, sous la désignation de l'article.\n\n"
             "Le modèle officiel du registre réclame en colonne 3 une "
             "« description précise de l'objet (nature, dimensions, style, "
             "signature et éventuellement signes distinctifs) » (arrêté du "
             "15 mai 2020, annexe I). Sur un type catalogué — une pièce, un "
             "lingot d'un poids donné — la désignation de l'article la donne "
             "déjà. Cochez donc là où elle ne dit rien de l'objet : or au "
             "gramme, lot de pièces, argent en vrac.\n\n"
             "LA PROVENANCE NE DÉPEND PAS DE CETTE CASE. Elle est exigée de "
             "tout article coché « Soumis au livre de police » — le registre "
             "veut l'origine de chaque objet acquis (art. R321-3 3° du code "
             "pénal ; CGI, ann. IV, art. 56 J quindecies), et aucune "
             "désignation ne la fournit.",
    )

    @api.onchange('metal_regulated', 'type')
    def _onchange_suivi_par_lot(self):
        if self.metal_regulated and self.type == 'consu':
            self.is_storable = True
            self.tracking = 'lot'

    @staticmethod
    def _suivi_par_lot_d_office(vals):
        """Un bien se presume soumis au registre : il se suit donc par lot.

        Le complement ne vaut que pour ce que la saisie tait. Decocher le
        suivi, ou declarer l'article hors registre, reste un choix explicite.
        """
        if (vals.get('type', 'consu') == 'consu'
                and vals.get('metal_regulated', True)
                and 'is_storable' not in vals):
            vals['is_storable'] = True
            vals.setdefault('tracking', 'lot')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            self._suivi_par_lot_d_office(vals)
        return super().create(vals_list)

    def write(self, vals):
        if vals.get('type') == 'consu' and not any(self.mapped('is_storable')):
            self._suivi_par_lot_d_office(vals)
        return super().write(vals)

    @api.constrains('metal_regulated', 'type', 'is_storable', 'tracking')
    def _check_suivi_par_lot(self):
        """Un bien soumis au registre se suit en stock, et par lot.

        Le numéro d'ordre est le nom du lot : c'est lui qui « figure de
        manière apparente sur chaque objet ou lot d'objets » (c. pén.,
        art. R321-4). Un article qui ne suit pas son stock s'inscrit au
        registre, mais sa réception ne crée ni lot ni quantité — le métal
        est entré et le coffre l'ignore. Le cas s'est produit, et Odoo
        interdit ensuite de corriger l'article par sa fiche.
        """
        if not self._police_juge_la_saisie():
            return
        for article in self:
            if (article.metal_regulated and article.type == 'consu'
                    and not (article.is_storable and article.tracking == 'lot')):
                raise ValidationError(_(
                    "« %(article)s » est soumis au livre de police : il doit "
                    "suivre son inventaire, par lot. Le lot porte le numéro "
                    "d'ordre de l'inscription (c. pén., art. R321-4) ; sans "
                    "lui, la réception inscrit le métal au registre sans le "
                    "mettre au coffre.\n\n"
                    "Cochez « Suivre l'inventaire » et choisissez « Par lot ».",
                    article=article.display_name))
