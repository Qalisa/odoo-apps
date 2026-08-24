# -*- coding: utf-8 -*-
"""Le même contrôle, sur la pièce comptable.

Le devis n'est pas le seul chemin : un avoir se saisit aussi directement, et
un import ou un appel RPC ne passent par aucune vue. Le contrôle est donc
répété à la comptabilisation, là où la pièce devient définitive.

Reste à savoir quelles lignes font entrer un objet. Un rachat part d'une
ligne de devis en quantité négative, et Odoo lui donne ensuite le signe qui
équilibre le document : quantité **positive sur un avoir**, ou **négative sur
une facture** lorsque le rachat est adossé à une vente. Les deux font entrer
l'objet. À l'inverse, une quantité négative sur un avoir défait un rachat :
elle ne fait rien entrer, et n'est pas contrôlée.

Le libellé de la ligne est recopié du devis par Odoo, et la provenance l'est
par ``_prepare_invoice_line`` : les deux mentions suivent la ligne sans qu'on
ait à les ressaisir.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..tools.description import description_ajoutee


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    police_origin_id = fields.Many2one(
        'livre.police.provenance', string="Provenance",
        ondelete='restrict', index='btree_not_null',
        help="Origine déclarée par le vendeur. Mention obligatoire du "
             "registre (art. R321-3 3° du code pénal). Reprise du devis "
             "lorsque la pièce en vient.",
    )
    police_description_expected = fields.Boolean(
        string="Article à décrire",
        compute='_compute_police_description_expected',
        help="Vrai lorsque l'article réclame une description de ses objets, "
             "indépendamment du sens de l'opération.",
    )
    police_description_required = fields.Boolean(
        string="Description exigée",
        compute='_compute_police_description_required',
        help="Vrai lorsque la ligne fait entrer un objet à décrire.",
    )
    police_description_missing = fields.Boolean(
        string="Description manquante",
        compute='_compute_police_description_missing',
        help="Le libellé de la ligne n'ajoute rien à la désignation de "
             "l'article : les objets ne sont pas décrits.",
    )
    police_origin_missing = fields.Boolean(
        string="Provenance manquante",
        compute='_compute_police_origin_missing',
        help="La ligne fait entrer un objet dont l'origine n'est pas déclarée.",
    )

    @api.depends('display_type',
                 'product_id.product_tmpl_id.police_description_required')
    def _compute_police_description_expected(self):
        for ligne in self:
            ligne.police_description_expected = bool(
                ligne.display_type == 'product'
                and ligne.product_id.product_tmpl_id.police_description_required)

    @api.depends('police_description_expected', 'quantity', 'move_id.move_type')
    def _compute_police_description_required(self):
        for ligne in self:
            type_piece = ligne.move_id.move_type
            entree = (
                (type_piece == 'out_refund' and ligne.quantity > 0)
                or (type_piece == 'out_invoice' and ligne.quantity < 0))
            ligne.police_description_required = bool(
                ligne.police_description_expected and entree)

    def _police_description(self):
        """Description des objets lue sur le libellé de la ligne."""
        self.ensure_one()
        produit = self.product_id
        return description_ajoutee(
            self.name, produit.get_product_multiline_description_sale(),
            produit.description_sale)

    @api.depends('police_description_required', 'name')
    def _compute_police_description_missing(self):
        for ligne in self:
            ligne.police_description_missing = bool(
                ligne.police_description_required and not ligne._police_description())

    @api.depends('police_description_required', 'police_origin_id')
    def _compute_police_origin_missing(self):
        for ligne in self:
            ligne.police_origin_missing = bool(
                ligne.police_description_required and not ligne.police_origin_id)

    def _police_manques(self):
        """Mentions du registre absentes de cette ligne, dans l'ordre du texte."""
        self.ensure_one()
        manques = []
        if self.police_origin_missing:
            manques.append("la provenance")
        if self.police_description_missing:
            manques.append("la description")
        return manques


class AccountMove(models.Model):
    _inherit = 'account.move'

    police_registre_concerne = fields.Boolean(
        string="Document soumis au registre",
        compute='_compute_police_registre_concerne',
        help="Vrai sur une pièce client portant un article à décrire. "
             "Commande l'affichage de la colonne « Provenance ».",
    )

    @api.depends('invoice_line_ids.police_description_required')
    def _compute_police_registre_concerne(self):
        """La colonne ne se montre que là où elle a quelque chose à recevoir.

        Sur une pièce comptable, le signe de la quantité est arrêté : on sait
        déjà si la ligne fait entrer un objet. Inutile donc de montrer la
        colonne sur une facture de vente, ni sur une facture fournisseur —
        l'achat de métal à un confrère se facture ainsi, mais ne relève pas du
        registre d'objets mobiliers, qui vise l'acquisition auprès du public.
        Une colonne vide et non modifiable se lit comme un oubli.

        Le devis suit une autre règle (voir ``sale_order.py``) : les lignes
        s'y saisissent, et le signe n'est pas encore connu.
        """
        for piece in self:
            piece.police_registre_concerne = any(
                piece.invoice_line_ids.mapped('police_description_required'))

    def _police_check_registre(self):
        for piece in self:
            fautives = piece.invoice_line_ids.filtered(
                lambda l: l.police_description_missing or l.police_origin_missing)
            if fautives:
                raise UserError(_(
                    "Le registre exige de chaque objet acquis sa provenance et "
                    "sa description (art. R321-3 3° du code pénal). Il "
                    "manque :\n  - %s",
                    "\n  - ".join(
                        "%s : %s" % (l.product_id.display_name,
                                     ", ".join(l._police_manques()))
                        for l in fautives)))

    def _post(self, soft=True):
        self._police_check_registre()
        return super()._post(soft=soft)
