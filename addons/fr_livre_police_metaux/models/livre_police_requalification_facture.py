# -*- coding: utf-8 -*-
"""Faire revenir au coffre du métal qu'une facture a fait sortir à tort.

Une vente est facturée et livrée, puis le tri révèle qu'une part n'est pas
partie : elle est restée en réserve, souvent sous une autre nature que celle
sous laquelle elle avait été vendue — de l'or blanc dans un lot d'or titré.
Le registre, lui, affirme que tout est parti.

La correction juste serait de rectifier chaque sortie, lot par lot, puis de
requalifier ce qui reste : le métal retrouve alors ses lots d'origine, ses
dates de rachat et sa filiation. C'est ce que le module sait faire, et cela
demande de dire ce qui n'est pas parti lot par lot — un travail que le
comptoir n'est pas toujours en mesure de fournir.

Cet écran est l'autre chemin, et il faut savoir ce qu'il coûte : le métal
rentre sous un **nouveau numéro d'ordre, sans filiation** avec les rachats
d'où il venait. Leurs dates et leurs vendeurs ne le suivent pas. C'est une
perte de traçabilité, assumée par celui qui l'inscrit.

Ce qui la borne, c'est la **facture**. Elle est obligatoire : l'entrée n'a
pas d'origine au registre, mais elle a un dossier, et le tiers, la pièce et
sa date disent d'où ce métal revient. Ces références partent dans la
**provenance** — la colonne que le modèle officiel réserve à « l'indication
de sa provenance » (arrêté du 15 mai 2020, annexe I, colonne 3) —, où le
chiffre de contrôle de la page les couvre. Le lien cliquable reste à côté,
hors du sceau, comme `facture_vente_ids` l'est déjà sur une sortie : le sceau
couvre le texte, pas le lien.

Le poids revenu ne peut pas dépasser celui que la facture porte. Une facture
ne rend pas plus de métal qu'elle n'en a fait sortir.

Écran réservé au droit « Livre de police - correction du stock » : il rouvre
ce que l'ajustement d'inventaire ferme, et n'a pas à être donné au comptoir.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.fr_numismatics_metals.tools import metals


class LivrePoliceRequalificationFacture(models.TransientModel):
    _name = 'livre.police.requalification.facture'
    _description = "Livre de police - requalification sur facture"

    partner_id = fields.Many2one(
        'res.partner', string="Client facturé", required=True,
        help="Celui à qui le métal avait été vendu. Il ne redevient pas "
             "vendeur pour autant : rien ne lui a été racheté, et les "
             "colonnes du vendeur restent vides.",
    )
    move_id = fields.Many2one(
        'account.move', string="Facture d'origine", required=True,
        domain="[('partner_id', 'child_of', partner_id),"
               " ('move_type', 'in', ('out_invoice', 'out_refund')),"
               " ('state', '=', 'posted')]",
        help="La pièce qui a fait sortir ce métal. Sa référence et sa date "
             "partent au registre : c'est là que se retrouve le dossier que "
             "le I de l'art. L102 B du LPF fait conserver.",
    )
    company_id = fields.Many2one(
        'res.company', string="Établissement", compute='_compute_facture',
        store=True, readonly=True,
        help="Le registre où l'entrée s'inscrit — celui de la facture.",
    )
    poids_facture = fields.Float(
        string="Poids facturé (g)", digits=(12, 4), readonly=True,
        compute='_compute_facture',
        help="Ce que la facture porte de métal réglementé. Ce qui revient ne "
             "peut pas peser davantage.",
    )
    date_achat = fields.Date(
        string="Date d'entrée", required=True,
        help="Le jour où ce métal est constaté au coffre.",
    )
    provenance = fields.Text(
        string="Provenance", required=True,
        help="Pourquoi ce métal revient, et ce qui n'est pas parti. C'est la "
             "seule mention où cette justification figurera ; la référence "
             "de la facture s'y ajoute d'elle-même. Couverte par le chiffre "
             "de contrôle de la page : écrite, elle ne se réécrit plus.",
    )
    ligne_ids = fields.One2many(
        'livre.police.requalification.facture.ligne', 'requalification_id',
        string="Métal qui revient",
    )
    poids_total = fields.Float(
        string="Poids qui revient (g)", digits=(12, 4), readonly=True,
        compute='_compute_poids_total',
    )

    @api.depends('move_id')
    def _compute_facture(self):
        for wiz in self:
            piece = wiz.move_id
            wiz.company_id = piece.company_id
            wiz.poids_facture = sum(
                abs(ligne.metal_weight or 0.0)
                for ligne in piece.invoice_line_ids
                if ligne.product_id.product_tmpl_id.metal_regulated)

    @api.depends('ligne_ids.poids')
    def _compute_poids_total(self):
        for wiz in self:
            wiz.poids_total = sum(wiz.ligne_ids.mapped('poids'))

    @api.onchange('move_id')
    def _onchange_move_id(self):
        """La date d'entrée part de celle de la facture, faute de mieux.

        Ce métal n'est jamais sorti : sa vraie date d'entrée est celle des
        rachats, que cet écran ne sait pas retrouver. Celle de la facture est
        la plus proche qu'on puisse écrire sans l'inventer.
        """
        for wiz in self:
            piece = wiz.move_id
            if piece and not wiz.date_achat:
                wiz.date_achat = piece.invoice_date or piece.date

    def _entrepot(self):
        self.ensure_one()
        entrepot = self.env['stock.warehouse'].sudo().search(
            [('company_id', '=', self.company_id.id)], limit=1)
        if not entrepot:
            raise UserError(_(
                "L'établissement %(societe)s n'a pas d'entrepôt : ce métal "
                "n'a nulle part où entrer.",
                societe=self.company_id.display_name))
        return entrepot

    def _verifier(self):
        self.ensure_one()
        if not self.env.user.has_group(
                'fr_livre_police_metaux.group_livre_police_correction'):
            raise UserError(_(
                "Faire revenir du métal sans rectifier sa sortie demande le "
                "droit « Livre de police - correction du stock ».\n\n"
                "Ce chemin inscrit une entrée sans filiation : il est "
                "réservé, et c'est voulu."))
        if not self.ligne_ids:
            raise UserError(_(
                "Aucun métal à faire revenir. Une entrée sans lot "
                "n'inscrirait rien."))
        if not (self.provenance or '').strip():
            raise UserError(_(
                "La provenance est la seule mention qui dira pourquoi ce "
                "métal revient : elle ne peut pas rester vide."))
        for ligne in self.ligne_ids:
            modele = ligne.product_id.product_tmpl_id
            if not modele.metal_regulated:
                raise UserError(_(
                    "« %(article)s » n'est pas soumis au livre de police.",
                    article=ligne.product_id.display_name))
            if ligne.quantite <= 0:
                raise UserError(_(
                    "La quantité de « %(article)s » doit être positive.",
                    article=ligne.product_id.display_name))
            if modele.police_description_required and not (
                    ligne.description or '').strip():
                raise UserError(_(
                    "« %(article)s » réclame une description des objets : sa "
                    "désignation ne dit pas ce que le métal est.",
                    article=ligne.product_id.display_name))
        # Une facture ne rend pas plus de métal qu'elle n'en a fait sortir.
        if self.poids_total > self.poids_facture + 0.00005:
            raise UserError(_(
                "Ce qui revient pèse %(revient).4f g, et la facture "
                "%(piece)s n'a fait sortir que %(sorti).4f g de métal "
                "réglementé.",
                revient=self.poids_total, piece=self.move_id.name,
                sorti=self.poids_facture))

    def _provenance_inscrite(self):
        """La justification saisie, suivie de la pièce qu'elle invoque.

        Les références entrent dans le texte parce que c'est lui que le
        chiffre de contrôle couvre, et parce qu'un registre imprimé doit se
        lire sans base de données à côté.
        """
        self.ensure_one()
        piece = self.move_id
        return _(
            "Retour sans rectification de sortie, sur la facture %(piece)s "
            "du %(date)s, client %(client)s. %(motif)s",
            piece=piece.name,
            date=fields.Date.to_string(piece.invoice_date or piece.date),
            client=self.partner_id.display_name,
            motif=self.provenance.strip())

    def action_inscrire(self):
        """Inscrit au registre, crée le lot, et pose la quantité en stock."""
        self.ensure_one()
        self._verifier()
        wiz = self.with_company(self.company_id)
        emplacement = wiz._entrepot().lot_stock_id
        provenance = wiz._provenance_inscrite()
        Registre = self.env['livre.police.ligne']
        Lot = self.env['stock.lot'].sudo()
        Quant = self.env['stock.quant'].sudo()

        inscriptions = Registre
        for ligne in wiz.ligne_ids:
            numero = Registre._sequence(wiz.company_id).next_by_id()
            lot = Lot.with_company(wiz.company_id).create({
                'name': numero,
                'product_id': ligne.product_id.id,
                'company_id': wiz.company_id.id,
            })
            # L'ajustement d'inventaire est le chemin d'Odoo pour du stock qui
            # apparaît sans venir d'un mouvement — ce qui est ici le cas, et
            # tout l'objet de l'écran.
            quant = Quant.with_company(wiz.company_id).with_context(
                inventory_mode=True).create({
                    'product_id': ligne.product_id.id,
                    'location_id': emplacement.id,
                    'lot_id': lot.id,
                    'inventory_quantity': ligne.quantite,
                })
            # L'entrée inscrit ce qu'elle ajuste — voir `stock_quant.py`.
            quant.with_context(police_ajustement=True).action_apply_inventory()
            mouvement = self.env['stock.move.line'].sudo().search(
                [('lot_id', '=', lot.id), ('state', '=', 'done')],
                order='id desc', limit=1)

            valeurs = Registre._valeurs_depuis_requalification_facture(
                wiz, ligne, mouvement, provenance)
            valeurs['numero_ordre'] = numero
            valeurs['numero_lot'] = numero
            inscriptions |= Registre.sudo().create(valeurs)

        return {
            'type': 'ir.actions.act_window',
            'name': _("Entrées inscrites"),
            'res_model': 'livre.police.ligne',
            'view_mode': 'list,form',
            'domain': [('id', 'in', inscriptions.ids)],
        }


class LivrePoliceRequalificationFactureLigne(models.TransientModel):
    _name = 'livre.police.requalification.facture.ligne'
    _description = "Livre de police - métal qui revient sur facture"

    requalification_id = fields.Many2one(
        'livre.police.requalification.facture', required=True,
        ondelete='cascade',
    )
    product_id = fields.Many2one(
        'product.product', string="Article", required=True,
        domain="[('metal_regulated', '=', True)]",
        help="Ce que ce métal est réellement — souvent autre chose que ce "
             "sous quoi il avait été vendu. L'article dit la nature, le "
             "titre et le régime de la quantité.",
    )
    quantite = fields.Float(
        string="Quantité", digits=(12, 4), required=True, default=0.0,
        help="Dans l'unité de l'article.",
    )
    poids = fields.Float(
        string="Poids (g)", digits=(12, 4), readonly=True,
        compute='_compute_poids',
        help="Déduit de l'article : au gramme la quantité vaut le poids, à "
             "la pièce elle est multipliée par le poids unitaire.",
    )
    description = fields.Text(
        string="Description des objets",
        help="Ce que la désignation ne dit pas. Exigée sur les articles qui "
             "la réclament (art. R321-3 3° du code pénal).",
    )

    @api.depends('product_id', 'quantite')
    def _compute_poids(self):
        for ligne in self:
            modele = ligne.product_id.product_tmpl_id
            ligne.poids = metals.derive_weight(
                modele.metal_quantity_mode, modele.metal_unit_weight,
                ligne.quantite) or 0.0
