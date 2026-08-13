# -*- coding: utf-8 -*-
"""Un article soumis au registre doit être suivi en stock, et par lot.

Le registre est tenu par objet identifié : sans suivi de stock il n'y a ni
date d'entrée ni date de sortie (CGI, ann. IV, art. 56 J quindecies), et sans
lot il n'y a pas de **numéro d'ordre** — que l'art. R321-4 du code pénal veut
« porté sur le registre » et sur l'objet lui-même.

Ces deux réglages sont donc **posés d'office** dès qu'un article entre dans le
périmètre du registre, et une contrainte empêche de les défaire ensuite.

Ils sont posés *avant* l'enregistrement, dans les valeurs, et non après :
les contraintes s'exécutent à l'intérieur de `create` et de `write`, si bien
qu'une correction appliquée après coup arriverait trop tard — l'article serait
déjà refusé. `setdefault` laisse par ailleurs passer un refus explicite :
demander un article non suivi *et* soumis au registre est contradictoire, et
mieux vaut le dire que le corriger en silence.
"""

from odoo import models, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.constrains('metal_regulated', 'is_storable', 'tracking')
    def _check_police_tracking(self):
        """Le suivi par lot n'est pas un confort, c'est le numéro d'ordre.

        Muette pendant le chargement des modules, pour la même raison que
        `_check_police_mentions` : à l'installation, le catalogue existant
        devient soumis au registre sans que personne l'ait demandé, et refuser
        ferait échouer l'installation au lieu d'informer.
        """
        if not self.env.registry.ready:
            return
        for product in self:
            if not product.metal_regulated:
                continue
            if not product.is_storable:
                raise ValidationError(_(
                    "« %s » est soumis au livre de police : il doit être "
                    "suivi en stock, faute de quoi ses objets n'auraient ni "
                    "date d'entrée ni date de sortie (CGI, ann. IV, art. 56 J "
                    "quindecies). Cochez « Suivre l'inventaire », ou décochez "
                    "« Soumis au livre de police » s'il ne désigne aucun objet "
                    "acheté.",
                    product.display_name))
            if product.tracking != 'lot':
                raise ValidationError(_(
                    "« %s » est soumis au livre de police : son suivi doit se "
                    "faire par lot. C'est le lot qui porte le numéro d'ordre "
                    "que l'art. R321-4 du code pénal veut inscrit au registre "
                    "et sur l'objet.",
                    product.display_name))

    @api.model
    def _police_stock_defaults(self, values, regule):
        """Complète les valeurs d'un article entrant au périmètre du registre."""
        if not regule:
            return values
        values = dict(values)
        values.setdefault('is_storable', True)
        values.setdefault('tracking', 'lot')
        return values

    @api.model_create_multi
    def create(self, vals_list):
        prepares = []
        for vals in vals_list:
            regule = vals.get('metal_regulated')
            if regule is None:
                # `metal_regulated` se calcule du type ; le type d'un article
                # vaut « bien » par défaut.
                regule = vals.get('type', 'consu') == 'consu'
            prepares.append(self._police_stock_defaults(vals, regule))
        return super().create(prepares)

    def write(self, values):
        # Deux façons d'entrer au périmètre : cocher la case, ou requalifier
        # un service en bien — la case suit alors le type.
        regule = bool(values.get('metal_regulated')
                      or values.get('type') == 'consu')
        return super().write(self._police_stock_defaults(values, regule))
