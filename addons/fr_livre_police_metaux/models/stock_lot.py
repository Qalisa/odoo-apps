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
    police_avoir_date = fields.Date(
        string="Date de l'avoir", compute='_compute_police_avoir_date',
        # Comme les champs `related` voisins, et pour la meme raison : la
        # piece a deja ete cherchee en `sudo` et filtree sur les societes
        # lisibles. Sans cela, un comptoir sans droits comptables verrait la
        # colonne « Avoir d'achat » remplie et la date a cote vide.
        compute_sudo=True,
        help="Le jour de l'achat, tel que le registre le retient : la date "
             "de facturation de l'avoir, à défaut sa date comptable.",
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

    @api.depends('police_avoir_id')
    def _compute_police_avoir_date(self):
        """La date que le registre a inscrite, et pas une autre.

        `invoice_date or date` est mot pour mot ce que retient
        `_valeurs_depuis_facture` pour `date_achat`. En ecrire un second
        garantirait qu'un jour les deux divergent, et c'est l'ecran qui
        aurait tort contre le registre.
        """
        for lot in self:
            piece = lot.police_avoir_id
            lot.police_avoir_date = piece.invoice_date or piece.date


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
    police_avoir_date = fields.Date(
        related='lot_id.police_avoir_date', string="Date de l'avoir",
        readonly=True)
    police_vendeur_id = fields.Many2one(
        related='lot_id.police_vendeur_id', string="Vendeur", readonly=True)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    police_description = fields.Char(
        string="Objets", compute='_compute_police_lot', compute_sudo=True,
    )
    police_avoir_id = fields.Many2one(
        'account.move', string="Avoir d'achat",
        compute='_compute_police_lot', compute_sudo=True,
    )
    police_avoir_date = fields.Date(
        string="Date de l'avoir",
        compute='_compute_police_lot', compute_sudo=True,
    )
    # Ce que le lot contient a l'emplacement d'ou l'on sort.
    #
    # La liste deroulante « Enlever parmi » l'annonce au moment du choix,
    # puis le tableau ne montre plus qu'un numero d'ordre : on saisit une
    # quantite sans rien a quoi la comparer. C'est ainsi que 60 000,80 g ont
    # ete saisis sur un lot qui en portait 6,80.
    #
    # La colonne le redit, a cote de la quantite qu'on saisit. C'est aussi le
    # plafond que `_police_check_stock_suffisant` fait respecter : les deux
    # disent la meme chose, l'une avant, l'autre au refus.
    police_quant_detenu = fields.Float(
        string="Détenu", readonly=True, digits='Product Unit of Measure',
        compute='_compute_police_quant_detenu',
        help="Ce que ce lot contient à cet emplacement. La quantité sortie "
             "ne peut pas le dépasser : le registre affirmerait qu'un métal "
             "est parti alors qu'il n'a jamais été là.",
    )
    police_vendeur_id = fields.Many2one(
        'res.partner', string="Vendeur",
        compute='_compute_police_lot', compute_sudo=True,
    )

    @api.depends('lot_id', 'quant_id')
    def _compute_police_lot(self):
        """Ce que le lot dit de lui-même, avant meme d'etre rattache.

        Ces quatre colonnes suivaient `lot_id` par un `related`. Or sur une
        ligne qu'on vient d'ajouter, `lot_id` est vide : Odoo ne le tire du
        quant choisi qu'au serveur, a l'ecriture (`_copy_quant_info`, appelee
        depuis `create` et `write`). Les quatre restaient donc blanches au
        moment precis ou l'on choisit — c'est-a-dire quand elles servent.

        Meme issue que pour `police_quant_detenu` : on lit le quant a defaut
        de la ligne.
        """
        for ligne in self:
            lot = ligne.lot_id or ligne.quant_id.lot_id
            ligne.police_description = lot.police_description
            ligne.police_avoir_id = lot.police_avoir_id
            ligne.police_avoir_date = lot.police_avoir_date
            ligne.police_vendeur_id = lot.police_vendeur_id

    @api.depends('lot_id', 'location_id', 'company_id', 'quant_id')
    def _compute_police_quant_detenu(self):
        """Ce que le lot contient la ou l'on vient le prendre.

        On ne se fonde pas sur `quant_id` seul : il n'est renseigne que si
        l'operateur a choisi lui-meme dans « Enlever parmi », et reste vide sur
        les lignes qu'Odoo reserve seul — la colonne serait a zero le plus
        souvent. Mais l'inverse est vrai sur une ligne qu'on vient d'ajouter :
        Odoo ne tire `lot_id` du quant choisi qu'au serveur, a l'ecriture
        (`_copy_quant_info`, appelee depuis `create` et `write`). Tant que la
        ligne n'est pas enregistree, elle n'a ni lot, ni emplacement, ni
        societe, et la colonne annoncait zero au moment precis ou l'on saisit.
        On lit donc le quant a defaut de la ligne.

        Le calcul est celui de `_police_check_stock_suffisant`, mot pour mot :
        la colonne annonce le plafond que le refus fera respecter.
        """
        Quant = self.env['stock.quant'].sudo()
        for ligne in self:
            quant = ligne.quant_id
            lot = ligne.lot_id or quant.lot_id
            emplacement = ligne.location_id or quant.location_id
            societe = ligne.company_id or quant.company_id
            if not lot or emplacement.usage != 'internal':
                ligne.police_quant_detenu = 0.0
                continue
            ligne.police_quant_detenu = sum(Quant.search([
                ('lot_id', '=', lot.id),
                ('location_id', 'child_of', emplacement.id),
                ('company_id', '=', societe.id),
            ]).mapped('quantity'))
