# -*- coding: utf-8 -*-
"""L'ajustement d'inventaire, et le rebut, sur du métal soumis au registre.

Le stock et le registre disent la même chose de deux façons. Le registre ne se
modifie que par une inscription nouvelle portant son motif (CGI, ann. IV,
art. 56 J sexdecies, 2° c) ; le stock, lui, s'ajuste d'un clic, et rien ne
s'inscrit. C'est par là que les deux divergent — en silence, ce qui est le
pire des deux défauts : une sortie non justifiée se lit au moins au registre,
un ajustement ne se lit nulle part.

Les documents du module ajustent le stock en même temps qu'ils inscrivent, et
posent pour cela une clef de contexte qui leur est propre. Ce qui reste fermé,
c'est l'ajustement nu — celui qu'aucune inscription n'accompagne.

Le rebut suit la même règle, et pour une raison plus simple encore : un lingot
ne se met pas au rebut. Il se vend, se transfère, ou se fond — et la fonte est
une vente au fondeur.
"""

from odoo import _, fields, models
from odoo.exceptions import UserError

#: Posée par les documents du module quand ils ajustent le stock qu'ils
#: viennent d'inscrire. Elle ne s'écrit nulle part ailleurs.
CONTEXTE_AJUSTEMENT = 'police_ajustement'

DROIT_CORRECTION = 'fr_livre_police_metaux.group_livre_police_correction'


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # Odoo laisse `available_quantity` hors de portee d'un domaine : le champ
    # est calcule et n'a pas de `search`. C'est ce qui oblige la liste ou l'on
    # choisit un lot a se rabattre sur la quantite physique, et a proposer des
    # lots qu'un autre bon a deja reserves. Le rendre interrogeable suffit a
    # corriger la regle la ou elle est ecrite — le filtre de la vue de
    # recherche — sans toucher au composant qui ouvre cette liste.
    available_quantity = fields.Float(search='_search_available_quantity')

    #: Les seuls operateurs qu'une comparaison de quantite appelle. La liste
    #: est aussi ce qui rend sur la concatenation dans la requete ci-dessous.
    _POLICE_OPERATEURS = ('<', '<=', '=', '!=', '>', '>=')

    def _search_available_quantity(self, operator, value):
        """Ce qui reste libre : le detenu moins ce que d'autres bons ont pris.

        Le calcul est celui d'Odoo — `quantity - reserved_quantity`, mot pour
        mot `_compute_available_quantity`. Il se fait en SQL et non en Python :
        un domaine peut tomber sur toute la table, et rien ne garantit qu'il
        arrive deja restreint a un article.
        """
        if operator not in self._POLICE_OPERATEURS or isinstance(value, bool) \
                or not isinstance(value, (int, float)):
            raise UserError(_("Opération non gérée sur la quantité disponible."))
        self.env['stock.quant'].flush_model(['quantity', 'reserved_quantity'])
        self.env.cr.execute(
            "SELECT id FROM stock_quant "
            "WHERE quantity - reserved_quantity " + operator + " %s", (value,))
        return [('id', 'in', [ligne[0] for ligne in self.env.cr.fetchall()])]

    def _apply_inventory(self):
        self._police_check_ajustement()
        return super()._apply_inventory()

    def _police_check_ajustement(self):
        if self.env.context.get(CONTEXTE_AJUSTEMENT):
            return
        if self.env.user.has_group(DROIT_CORRECTION):
            return
        concernes = self.filtered(
            lambda q: q.product_id.product_tmpl_id.metal_regulated)
        if not concernes:
            return
        raise UserError(_(
            "Le stock d'un métal soumis au registre ne s'ajuste pas à la "
            "main.\n\n"
            "Le stock et le registre disent la même chose : corriger l'un "
            "sans l'autre les fait diverger, et rien ne le signalerait.\n\n"
            "Selon le cas : « Rectifier les quantités » corrige un stock "
            "inscrit à tort, « Régulariser une arrivée » inscrit du métal reçu "
            "sans document, « Requalifier une part du lot » reclasse ce qu'un "
            "tri a révélé. Chacun inscrit au registre ce qu'il change au "
            "stock.\n\n"
            "Articles concernés : %(articles)s",
            articles=", ".join(concernes.mapped('product_id.name'))))


class StockScrap(models.Model):
    _inherit = 'stock.scrap'

    def do_scrap(self):
        self._police_check_rebut()
        return super().do_scrap()

    def _police_check_rebut(self):
        if self.env.user.has_group(DROIT_CORRECTION):
            return
        concernes = self.filtered(
            lambda s: s.product_id.product_tmpl_id.metal_regulated)
        if not concernes:
            return
        raise UserError(_(
            "Un métal soumis au registre ne se met pas au rebut.\n\n"
            "Un lingot ne se jette pas : il se vend, se transfère, ou se fond "
            "— et la fonte est une vente au fondeur, qui s'inscrit comme "
            "telle. Un rebut ne passe par aucun bon : le métal disparaîtrait "
            "du stock et du registre à la fois, sans laisser de trace.\n\n"
            "Articles concernés : %(articles)s",
            articles=", ".join(concernes.mapped('product_id.name'))))
