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

    police_origin_id = fields.Many2one(
        'livre.police.provenance', string="Provenance", ondelete='restrict',
        index='btree_not_null',
        help="Origine déclarée par le vendeur : héritage, bijoux personnels, "
             "achat antérieur… Mention obligatoire du registre "
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
    police_representative_id = fields.Many2one(
        'res.partner', string="Représentant du vendeur",
        compute='_compute_police_representative_id', store=True, readonly=False,
        ondelete='restrict', index='btree_not_null',
        domain="[('id', 'child_of', police_seller_company_id),"
               " ('is_company', '=', False)]",
        help="Personne physique qui a réalisé l'opération pour le compte de "
             "la société venderesse (art. R321-3 2°). Le registre exige ses "
             "nom, prénoms, qualité et domicile, et les références de sa "
             "pièce d'identité : une société ne se présente pas au comptoir, "
             "quelqu'un s'y présente pour elle.",
    )
    police_seller_company_id = fields.Many2one(
        'res.partner', string="Société venderesse",
        compute='_compute_police_representative_id', store=True,
        help="Société pour le compte de laquelle la vente est faite, s'il y "
             "en a une. Déduite du contact retenu sur la pièce.",
    )
    police_representative_required = fields.Boolean(
        string="Représentant exigé",
        compute='_compute_police_representative_required',
    )

    @api.depends('partner_id')
    def _compute_police_representative_id(self):
        """Qui vend, et pour le compte de qui ?

        Deux saisies mènent au même achat à une société : retenir la société
        elle-même, ou retenir directement le contact rattaché. Le second cas
        porte déjà la réponse — la personne physique est là, la société est
        son parent commercial ; on ne la redemande pas. Le premier la laisse
        ouverte : c'est le champ que la comptabilisation réclamera.
        """
        for piece in self:
            partenaire = piece.partner_id
            societe = partenaire.commercial_partner_id
            if partenaire and societe.is_company:
                piece.police_seller_company_id = societe
                if not partenaire.is_company:
                    piece.police_representative_id = partenaire
                elif piece.police_representative_id.commercial_partner_id != societe:
                    piece.police_representative_id = False
            else:
                piece.police_seller_company_id = False
                piece.police_representative_id = False

    @api.depends('police_seller_company_id', 'move_type', 'date',
                 'company_id.police_start_date',
                 'invoice_line_ids.police_origin_required')
    def _compute_police_representative_required(self):
        for piece in self:
            piece.police_representative_required = bool(
                piece.police_seller_company_id
                and piece.invoice_line_ids.filtered('police_origin_required'))

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

    #: États d'un paiement qui valent règlement constaté. `draft` et les états
    #: d'échec n'ont rien réglé : le registre ne doit pas les mentionner.
    ETATS_REGLES = ('in_process', 'paid')

    def _police_payment_mode(self):
        """Mode de règlement constaté, lu sur le paiement Odoo.

        Le registre ne demande pas au comptoir de *déclarer* un mode de
        règlement : il constate celui qui a été employé. La source est donc le
        paiement rattaché à l'avoir, ce qui rend impossible une mention
        invérifiable : pas de paiement, pas de mention.

        Deux rattachements coexistent en Odoo 18 et sont lus tous les deux :
        le paiement enregistré depuis la pièce (`matched_payment_ids`), qui
        n'a pas encore d'écriture tant qu'il n'est pas au relevé, et le
        lettrage comptable classique, contre une écriture de banque ou de
        caisse.

        Le libellé retenu est celui du **mode de paiement** — c'est lui qui
        nomme le canal (virement, chèque) —, à défaut celui du journal.

        Souvent vide à la comptabilisation : le règlement suit. La ligne reste
        alors signalée incomplète jusqu'au paiement, qui la complète tout seul
        (cf. `_police_write_payment_mode`).
        """
        self.ensure_one()
        modes = set()
        for paiement in self.matched_payment_ids:
            if paiement.state in self.ETATS_REGLES:
                modes.add(paiement.payment_method_line_id.name
                          or paiement.journal_id.name)
        lignes = self.line_ids
        partiels = lignes.matched_debit_ids | lignes.matched_credit_ids
        contreparties = (partiels.debit_move_id | partiels.credit_move_id).move_id
        modes.update((contreparties - self).mapped('journal_id.name'))
        return ", ".join(sorted(filter(None, modes))) or False

    def _police_write_payment_mode(self):
        """Reporte le mode de règlement constaté sur les lignes du registre.

        Appelée au lettrage comme au délettrage. L'écriture passe par
        `write`, donc toute évolution laisse une correction au journal chaîné :
        le registre montre qu'il a été complété, et quand.
        """
        # Le lettrage vient d'être créé (ou défait) : les champs inverses des
        # lignes ne portent pas encore le nouvel état dans le cache.
        self.env['account.move.line'].invalidate_model(
            ['matched_debit_ids', 'matched_credit_ids'])
        for piece in self:
            mode = piece._police_payment_mode()
            lots = piece.invoice_line_ids.police_lot_id
            a_ecrire = lots.filtered(lambda l: l.police_payment_mode != mode)
            if a_ecrire:
                a_ecrire.sudo().write({'police_payment_mode': mode})

    def _police_check_seller(self):
        """Le vendeur porte-t-il les mentions que le registre exige de lui ?

        L'art. R321-3 1° veut « les nom, prénoms, qualité et domicile ». La
        qualité ne se devine pas et ne se rattrape pas : une fois le vendeur
        reparti, personne ne sait s'il était retraité ou artisan. Le contrôle
        est donc posé à la comptabilisation, tant qu'il est encore au comptoir.
        """
        self.ensure_one()
        if self.police_seller_company_id:
            return self._police_check_representative()
        vendeur = self.partner_id
        if vendeur and not vendeur.is_company and not vendeur.police_qualite_id:
            raise UserError(_(
                "« %s » n'a pas de qualité ou profession renseignée. Le livre "
                "de police l'exige du vendeur (art. R321-3 1°) : complétez sa "
                "fiche avant de comptabiliser ce rachat.",
                vendeur.display_name))

    def _police_check_representative(self):
        """Mentions exigées quand le vendeur est une personne morale.

        L'art. R321-3 2° veut, outre la dénomination et le siège, « les nom,
        prénoms, qualité et domicile du représentant de la personne morale qui
        a effectué l'opération pour son compte, avec les références de la
        pièce d'identité produite ». « Références » est plus léger que
        l'énumération du 1° : on s'en tient à la nature et au numéro, sans
        réclamer la date ni l'autorité.
        """
        self.ensure_one()
        representant = self.police_representative_id
        if not representant:
            raise UserError(_(
                "Ce rachat est fait à « %s ». Le livre de police exige "
                "l'identité de la personne qui a réalisé l'opération pour son "
                "compte (art. R321-3 2°) : retenez le contact rattaché à la "
                "société dans « Représentant du vendeur ».",
                self.police_seller_company_id.display_name))
        manques = []
        if not representant.police_qualite_id:
            manques.append(_("sa qualité (gérant, mandataire…)"))
        if not representant.street or not representant.city:
            manques.append(_("son domicile"))
        if not representant.id_doc_type or not representant.id_doc_number:
            manques.append(_("les références de sa pièce d'identité"))
        if manques:
            raise UserError(_(
                "La fiche de « %(nom)s », qui vend pour le compte de "
                "« %(societe)s », est incomplète au regard du livre de police "
                "(art. R321-3 2°). Il manque : %(manques)s.",
                nom=representant.display_name,
                societe=self.police_seller_company_id.display_name,
                manques=", ".join(manques)))

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
        self._police_check_seller()

        muettes = lignes.filtered(lambda l: not l.police_origin_id)
        if muettes:
            raise UserError(_(
                "La provenance est une mention obligatoire du registre "
                "(art. R321-3 3°). Elle manque sur :\n  - %s",
                "\n  - ".join(l.name or l.product_id.display_name
                              for l in muettes)))

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
                # Le vendeur est la société quand il y en a une ; la personne
                # physique qui a agi pour elle est le représentant. La qualité
                # inscrite est toujours celle de qui s'est présenté.
                'police_seller_id': (self.police_seller_company_id
                                     or self.partner_id).id,
                'police_representative_id': self.police_representative_id.id,
                'police_seller_qualite_id': (
                    self.police_representative_id
                    or self.partner_id).police_qualite_id.id,
                'police_origin_id': ligne.police_origin_id.id,
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

    def write(self, values):
        """Rattacher un paiement à la pièce complète sa ligne au registre."""
        resultat = super().write(values)
        if 'matched_payment_ids' in values:
            self.filtered('police_picking_id')._police_write_payment_mode()
        return resultat

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


class AccountPayment(models.Model):
    """Un paiement remis en brouillon ne règle plus rien.

    `action_draft` ne défait pas le rattachement à la pièce : c'est l'état du
    paiement qui dit s'il y a eu règlement. Le registre suit donc cet état,
    dans les deux sens.
    """
    _inherit = 'account.payment'

    def write(self, values):
        resultat = super().write(values)
        if 'state' in values or 'invoice_ids' in values:
            self.invoice_ids.filtered(
                'police_picking_id')._police_write_payment_mode()
        return resultat


class AccountPartialReconcile(models.Model):
    """Le lettrage complète le registre.

    Le mode de règlement est la seule mention obligatoire qui n'est pas
    connue au comptoir : le rachat est saisi, le virement part ensuite. Plutôt
    que de la faire ressaisir — et donc de la laisser diverger du paiement
    réel —, on la reprend du lettrage, dans les deux sens : lettrer complète
    la ligne, délettrer la rouvre.
    """
    _inherit = 'account.partial.reconcile'

    def _police_pieces(self):
        pieces = (self.debit_move_id | self.credit_move_id).move_id
        return pieces.filtered('police_picking_id')

    @api.model_create_multi
    def create(self, vals_list):
        partiels = super().create(vals_list)
        partiels._police_pieces()._police_write_payment_mode()
        return partiels

    def unlink(self):
        # Les pièces sont relevées avant la suppression : après, le lien
        # n'existe plus et le registre resterait sur un règlement défait.
        pieces = self._police_pieces()
        resultat = super().unlink()
        pieces._police_write_payment_mode()
        return resultat
