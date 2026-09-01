# -*- coding: utf-8 -*-
"""Le lot dit ce qu'il contient, là où on le choisit.

Le lot naît déjà décrit : `_prepare_new_lot_vals` recopie dans sa note la
description que le registre a inscrite. Cette description reste pourtant
invisible au seul endroit où elle sert — les tableaux d'une sortie, qui
affichent « Metz/Stock - 000002 » et ne nomment aucun objet.

Or c'est là que le choix se fait, et il ne se fait pas au hasard : on vend
les objets qu'on a sortis du coffre, pas un numéro. Ces mentions prennent
donc des **colonnes**, et ne se glissent pas dans le nom affiché du lot : ce
nom est le numéro d'ordre, celui que l'étiquette porte et que le registre
indexe (c. pén., art. R321-4), et il est lu ailleurs — traçabilité,
inventaire, éditions — où la description n'a rien à faire.

L'avoir se retrouve par le chemin de la marchandise : la réception, le devis
de rachat, la pièce comptable. Jamais par le registre — le registre est un
livre dont chaque lecture se déclare (arrêté du 15 mai 2020, art. 3, 2°), et
choisir un lot n'est pas le consulter. C'est aussi ce qui permet au comptoir
de lire ces mentions sans le droit de consultation.
"""

from odoo import api, fields, models
from odoo.tools.mail import html2plaintext


class StockLot(models.Model):
    _inherit = 'stock.lot'

    police_description = fields.Char(
        string="Objets", compute='_compute_police_description',
        help="Les objets tels que le comptoir les a décrits au rachat. "
             "« 18k Or 750 ‰(gr) » nomme le métal ; celle-ci nomme lesquels.",
    )
    police_avoir_id = fields.Many2one(
        'account.move', string="Avoir d'achat",
        compute='_compute_police_avoir_id',
        help="La pièce comptable qui a fait entrer ce lot, retrouvée par sa "
             "réception et le devis de rachat.",
    )
    police_vendeur_id = fields.Many2one(
        'res.partner', string="Vendeur",
        related='police_avoir_id.partner_id',
        help="Qui a apporté ce métal. « Vendeur » et non « client » : sur un "
             "rachat, le tiers de la pièce est celui qui a vendu.",
    )

    @api.depends('note')
    def _compute_police_description(self):
        for lot in self:
            lot.police_description = html2plaintext(lot.note or '') or False

    @api.depends('name')
    def _compute_police_avoir_id(self):
        """Remonte du lot à l'avoir, par la réception.

        Un lot est nommé à la validation d'une réception ; cette réception
        naît d'une ligne de devis, et cette ligne se facture. Le chemin est
        celui qu'emprunte déjà `stock.move.police_ligne_id`, arrêté une
        étape plus tôt : on veut la pièce, pas l'inscription.
        """
        Mouvement = self.env['stock.move.line'].sudo()
        for lot in self:
            entree = Mouvement.search([
                ('lot_id', '=', lot.id),
                ('state', '=', 'done'),
                ('move_id.picking_type_id.code', '=', 'incoming'),
            ], limit=1)
            pieces = entree.move_id.sale_line_id.invoice_lines.move_id
            # Un lot transféré n'appartient plus à aucune société : il se lit
            # des trois comptoirs. L'avoir, lui, n'a pas à se lire d'ailleurs
            # que de l'établissement qui l'a passé — c'est le vendeur qu'il
            # nomme, et « le registre d'un établissement n'a pas à montrer les
            # clients d'un autre ». La recherche reste en `sudo` parce que
            # choisir un lot n'est pas consulter le registre ; ce filtre-ci
            # rend au cloisonnement ce que ce `sudo` lui aurait pris.
            lot.police_avoir_id = pieces.filtered(
                lambda piece: piece.company_id in self.env.companies)[:1]


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    # Le stock disponible se consulte aussi en liste — « Voir plus » depuis
    # « Enlever parmi », ou l'inventaire lui-même. Ce sont les mêmes
    # questions qu'au comptoir : quels objets, achetés à qui, sur quelle
    # pièce.
    police_description = fields.Char(
        related='lot_id.police_description', string="Objets", readonly=True)
    police_avoir_id = fields.Many2one(
        related='lot_id.police_avoir_id', string="Avoir d'achat", readonly=True)
    police_vendeur_id = fields.Many2one(
        related='lot_id.police_vendeur_id', string="Vendeur", readonly=True)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    police_description = fields.Char(
        string="Objets", related='lot_id.police_description', readonly=True,
    )
    police_avoir_id = fields.Many2one(
        related='lot_id.police_avoir_id', string="Avoir d'achat", readonly=True,
    )
    police_vendeur_id = fields.Many2one(
        related='lot_id.police_vendeur_id', string="Vendeur", readonly=True,
    )
