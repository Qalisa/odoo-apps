# -*- coding: utf-8 -*-
"""Nature du métal précieux : un modèle, pas une liste figée dans le code.

Les cinq natures usuelles du métier — or, argent, platine, palladium,
rhodium — sont créées à l'installation du module, puis appartiennent au
client : il les renomme, les archive, en ajoute. Une liste de sélection
codée en dur imposerait une mise à jour du module à chaque évolution.

Le modèle ne porte que le nom : c'est la mention qui figure au livre de
police. Rien d'autre n'a à être paramétré ici — un cours, une fourchette de
prix ou un titre par défaut se démoderaient, et se déduisent de toute façon
de l'article et de la saisie du vendeur.
"""

from odoo import models, fields, _


class MetalNature(models.Model):
    _name = 'metal.nature'
    _description = "Nature de métal précieux"
    _order = 'name'

    name = fields.Char(
        string="Nature", required=True, translate=True,
        help="Nom du métal tel qu'il doit apparaître au livre de police.",
    )
    active = fields.Boolean(
        string="Actif", default=True,
        help="Décocher pour retirer la nature des listes sans la supprimer : "
             "les articles et le registre qui s'y réfèrent restent intacts.",
    )
    product_count = fields.Integer(
        string="Articles", compute='_compute_product_count',
        help="Nombre d'articles du catalogue rattachés à cette nature, "
             "archivés compris.",
    )

    _sql_constraints = [
        ('name_uniq', 'unique(name)',
         "Cette nature de métal existe déjà."),
    ]

    def _compute_product_count(self):
        counts = dict(self.env['product.template'].with_context(
            active_test=False)._read_group(
                [('metal_nature', 'in', self.ids)],
                groupby=['metal_nature'], aggregates=['__count']))
        for nature in self:
            nature.product_count = counts.get(nature, 0)

    def action_view_products(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Articles en %s", self.name),
            'res_model': 'product.template',
            'view_mode': 'list,form',
            'domain': [('metal_nature', '=', self.id)],
            'context': {'active_test': False, 'default_metal_nature': self.id},
        }
