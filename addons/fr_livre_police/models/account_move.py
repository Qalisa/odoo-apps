# -*- coding: utf-8 -*-
"""L'avoir de rachat fait entrer l'objet au registre.

Le rachat au comptoir se comptabilise en avoir client. Un avoir ne produit
aucun mouvement de stock : c'est pourquoi rien de ce qui est acheté n'existe
aujourd'hui en stock, et pourquoi la branche « sortie » du registre était
introuvable. Ce module fait le pont — à la comptabilisation, l'avoir crée la
réception et le lot qui portera le numéro d'ordre.

Rien ne se déclenche avant la date de bascule de la société : le registre
commence quand les agences ont compté leurs coffres, pas à l'installation.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    police_origin = fields.Char(
        string="Provenance",
        help="Origine déclarée par le vendeur : succession, héritage, achat "
             "antérieur, vide-grenier… Mention obligatoire du registre "
             "(art. R321-3 3° du code pénal).",
    )
    police_lot_id = fields.Many2one(
        'stock.lot', string="Numéro d'ordre", readonly=True, copy=False,
        help="Lot créé au registre pour cette ligne.",
    )
    police_origin_required = fields.Boolean(
        string="Provenance exigée", compute='_compute_police_origin_required',
        help="Vrai lorsque la ligne fera entrer un objet au registre : la "
             "provenance devient alors une mention obligatoire.",
    )
    police_description_missing = fields.Boolean(
        string="Description manquante", compute='_compute_police_description_missing',
        help="Un article soumis au registre doit être décrit : ajoutez une "
             "note sous la ligne (art. R321-3).",
    )

    @api.depends('product_id', 'move_id.move_type', 'move_id.date',
                 'move_id.company_id.police_start_date')
    def _compute_police_origin_required(self):
        for ligne in self:
            piece = ligne.move_id
            debut = piece.company_id.police_start_date
            ligne.police_origin_required = bool(
                piece.move_type == 'out_refund' and debut and piece.date
                and piece.date >= debut
                and ligne.product_id.product_tmpl_id.metal_regulated)

    @api.depends('police_origin_required', 'sequence',
                 'move_id.invoice_line_ids.display_type',
                 'move_id.invoice_line_ids.name',
                 'move_id.invoice_line_ids.sequence')
    def _compute_police_description_missing(self):
        for ligne in self:
            ligne.police_description_missing = bool(
                ligne.police_origin_required
                and not ligne.move_id._police_description(ligne))


class AccountMove(models.Model):
    _inherit = 'account.move'

    police_picking_id = fields.Many2one(
        'stock.picking', string="Réception au registre", readonly=True, copy=False,
    )

    def _police_description(self, ligne):
        """Description des objets d'une ligne : les notes qui la suivent.

        Une note Odoo n'a aucun lien de parenté avec une ligne d'article : le
        rattachement est celui que l'œil fait en lisant la pièce, la note se
        rapporte à la ligne qu'elle suit. On retient donc toutes les notes
        consécutives placées sous la ligne, jusqu'à la ligne suivante.

        Ce rattachement n'a besoin d'être exact qu'une fois : à la
        comptabilisation, le texte est recopié sur le lot, où il est scellé.
        Effacer la note ensuite n'efface plus rien du registre.
        """
        self.ensure_one()
        lignes = self.invoice_line_ids.sorted(lambda l: (l.sequence, l.id))
        if ligne not in lignes:
            return ""
        rang = list(lignes).index(ligne)
        notes = []
        for suivante in lignes[rang + 1:]:
            if suivante.display_type != 'line_note':
                break
            notes.append((suivante.name or '').strip())
        return '\n'.join(filter(None, notes))

    def _police_check_descriptions(self, lignes):
        """Refuse la comptabilisation d'un objet entrant au registre sans
        description. Un lot « 18k Or, 148,60 g » n'identifie aucun objet ;
        l'art. R321-3 veut les caractéristiques qui servent à le reconnaître.
        """
        self.ensure_one()
        muettes = [l for l in lignes if not self._police_description(l)]
        if muettes:
            raise UserError(_(
                "Ces lignes entrent au livre de police sans description des "
                "objets — ajoutez une note sous chacune d'elles (art. R321-3) "
                ":\n  - %s",
                "\n  - ".join(l.name or l.product_id.display_name
                              for l in muettes)))

    # ------------------------------------------------------------------
    # Entrée au registre
    # ------------------------------------------------------------------
    def _police_lines(self):
        """Lignes de l'avoir portant un objet soumis au registre."""
        self.ensure_one()
        return self.invoice_line_ids.filtered(
            lambda l: l.display_type == 'product'
            and l.product_id.product_tmpl_id.metal_regulated
            and l.quantity)

    def _police_applicable(self):
        """Le registre doit-il être alimenté par cette pièce ?"""
        self.ensure_one()
        debut = self.company_id.police_start_date
        return bool(
            self.move_type == 'out_refund' and debut
            and self.date and self.date >= debut
            and not self.police_picking_id
            and self._police_lines())

    def _police_warehouse(self):
        self.ensure_one()
        entrepot = self.env['stock.warehouse'].search(
            [('company_id', '=', self.company_id.id)], limit=1)
        if not entrepot:
            raise UserError(_(
                "Aucun entrepôt n'est défini pour %s : le livre de police ne "
                "peut pas enregistrer d'entrée.", self.company_id.name))
        return entrepot

    def _police_payment_mode(self):
        """Mode de règlement lu sur les paiements rapprochés, s'il y en a.

        Souvent vide à la comptabilisation : le règlement suit. La mention
        reste alors à compléter, et l'écran de contrôle la réclame.
        """
        self.ensure_one()
        lignes = self.line_ids
        partiels = lignes.matched_debit_ids | lignes.matched_credit_ids
        contreparties = (partiels.debit_move_id | partiels.credit_move_id).move_id
        journaux = (contreparties - self).mapped('journal_id.name')
        return ", ".join(sorted(set(journaux))) if journaux else False

    def _police_create_entry(self):
        """Crée la réception et les lots du registre pour cet avoir."""
        self.ensure_one()
        lignes = self._police_lines()
        non_stockes = lignes.product_id.filtered(lambda p: not p.is_storable)
        if non_stockes:
            raise UserError(_(
                "Ces articles sont soumis au livre de police mais ne sont pas "
                "suivis en stock — cochez « Suivre l'inventaire » : %s",
                ", ".join(non_stockes.mapped('name'))))

        self._police_check_descriptions(lignes)

        entrepot = self._police_warehouse()
        type_entree = entrepot.in_type_id
        fournisseurs = self.env.ref('stock.stock_location_suppliers')
        emplacement = type_entree.default_location_dest_id or entrepot.lot_stock_id
        reglement = self._police_payment_mode()

        picking = self.env['stock.picking'].with_company(self.company_id).create({
            'partner_id': self.partner_id.id,
            'picking_type_id': type_entree.id,
            'location_id': fournisseurs.id,
            'location_dest_id': emplacement.id,
            'scheduled_date': fields.Datetime.to_datetime(self.date),
            'origin': self.name,
        })
        Lot = self.env['stock.lot']
        for ligne in lignes:
            lot = Lot._police_create_entry({
                'product_id': ligne.product_id.id,
                'company_id': self.company_id.id,
                'police_seller_id': self.partner_id.id,
                'police_origin': ligne.police_origin,
                'police_description': self._police_description(ligne),
                'police_weight': ligne.metal_weight,
                'police_quantity': abs(ligne.quantity),
                'police_fineness': ligne.product_id.product_tmpl_id.metal_fineness,
                'police_purchase_price': abs(ligne.quantity * ligne.price_unit),
                'police_currency_id': self.currency_id.id,
                'police_payment_mode': reglement,
                'police_source_move_id': self.id,
            })
            ligne.police_lot_id = lot
            self.env['stock.move'].with_company(self.company_id).create({
                'picking_id': picking.id,
                'product_id': ligne.product_id.id,
                'product_uom_qty': abs(ligne.quantity),
                'name': ligne.name or ligne.product_id.name,
                'location_id': fournisseurs.id,
                'location_dest_id': emplacement.id,
            })

        picking.action_confirm()
        for move, ligne in zip(picking.move_ids, lignes):
            move.move_line_ids.unlink()
            self.env['stock.move.line'].with_company(self.company_id).create({
                'move_id': move.id,
                'picking_id': picking.id,
                'product_id': move.product_id.id,
                'lot_id': ligne.police_lot_id.id,
                'quantity': abs(ligne.quantity),
                'location_id': fournisseurs.id,
                'location_dest_id': emplacement.id,
            })
        picking.button_validate()
        # La date du registre est celle du rachat, non celle de la saisie.
        picking.move_ids.write({'date': fields.Datetime.to_datetime(self.date)})
        picking.move_line_ids.write({'date': fields.Datetime.to_datetime(self.date)})
        self.police_picking_id = picking
        # Inscription au journal chaîné : après la validation, pour que la
        # date d'entrée existe déjà dans les mentions scellées.
        for ligne in lignes:
            ligne.police_lot_id.police_entry_date = fields.Datetime.to_datetime(
                self.date)
        for ligne in lignes:
            ligne.police_lot_id._police_inscrire(
                'entree', fields.Datetime.to_datetime(self.date),
                description=self.name)
        return picking

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        for move in posted:
            if move._police_applicable():
                move._police_create_entry()
        return posted

    def button_draft(self):
        """Une pièce dont les objets sont déjà sortis ne revient pas en brouillon."""
        for move in self:
            sortis = move.invoice_line_ids.police_lot_id.filtered(
                'police_exit_date')
            if sortis:
                raise UserError(_(
                    "Les objets %s sont déjà sortis au livre de police : "
                    "cette pièce ne peut plus être remise en brouillon.",
                    ", ".join(sortis.mapped('name'))))
        return super().button_draft()

    def action_police_view_picking(self):
        """Ouvre la réception qui a fait entrer les objets au registre."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Réception au livre de police"),
            'res_model': 'stock.picking',
            'res_id': self.police_picking_id.id,
            'view_mode': 'form',
        }
