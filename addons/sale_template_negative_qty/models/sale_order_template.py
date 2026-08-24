# -*- coding: utf-8 -*-
"""Le modèle de devis dit s'il sert à acheter ou à vendre.

Le sens de l'opération n'est pas une propriété du code : le même Odoo sert au
comptoir à vendre et à racheter, et c'est le modèle choisi qui tranche. La
case vit donc là, et un modèle ajouté plus tard se règle sans mise à jour.
"""

from odoo import models, fields


class SaleOrderTemplate(models.Model):
    _inherit = 'sale.order.template'

    negative_qty_default = fields.Boolean(
        string="Rachat : quantité négative par défaut",
        help="Coché, l'ajout d'une ligne propose −1 au lieu de 1.\n\n"
             "À réserver aux modèles de rachat, dont le devis devient un "
             "avoir. La quantité reste modifiable : ce n'est qu'un défaut.",
    )
