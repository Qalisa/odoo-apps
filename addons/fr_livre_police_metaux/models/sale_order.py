# -*- coding: utf-8 -*-
"""Le rachat se saisit sur un devis, en quantité négative.

L'établissement n'y vend rien : il achète. C'est le signe de la quantité qui
dit le sens de l'opération, et donc si la ligne fait entrer un objet dans les
murs — le seul cas où le registre réclame description et provenance.

L'art. R321-3 3° les tient dans la même phrase : « la nature, la provenance et
la description des objets acquis ». Le modèle officiel du registre les tient
dans la même colonne. Elles sont donc exigées ensemble, par la même case sur
la fiche de l'article.

La description n'a pas de champ à elle : elle se met là où le comptoir la met
déjà, dans le champ « Description » de la ligne, sous la désignation de
l'article. Voir ``tools/description.py`` pour ce qui compte comme description.
La provenance, elle, ne s'écrit nulle part aujourd'hui et prend un champ.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..tools.description import description_ajoutee


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    police_origin_id = fields.Many2one(
        'livre.police.provenance', string="Provenance",
        ondelete='restrict', index='btree_not_null',
        help="Origine déclarée par le vendeur : bijoux personnels, héritage, "
             "achat antérieur… Mention obligatoire du registre "
             "(art. R321-3 3° du code pénal).",
    )
    police_description_expected = fields.Boolean(
        string="Article à décrire",
        compute='_compute_police_description_expected',
        help="Vrai lorsque l'article réclame une description de ses objets. "
             "Ne dépend pas du sens de l'opération : la zone de saisie s'ouvre "
             "dès le choix de l'article, avant que la quantité soit connue.",
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
                not ligne.display_type
                and ligne.product_id.product_tmpl_id.police_description_required)

    @api.depends('police_description_expected', 'product_uom_qty')
    def _compute_police_description_required(self):
        for ligne in self:
            ligne.police_description_required = bool(
                ligne.police_description_expected and ligne.product_uom_qty < 0)

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

    def _prepare_invoice_line(self, **optional_values):
        """La provenance suit la ligne jusqu'à la pièce comptable.

        Sans cela, elle serait saisie au comptoir puis perdue à la
        facturation, et le contrôle posé au `_post` refuserait une pièce que
        rien ne permettrait plus de compléter.
        """
        values = super()._prepare_invoice_line(**optional_values)
        if self.police_origin_id:
            values['police_origin_id'] = self.police_origin_id.id
        return values


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    police_registre_concerne = fields.Boolean(
        string="Document soumis au registre",
        compute='_compute_police_registre_concerne',
        help="Vrai dès qu'une ligne porte un article à décrire. Commande "
             "l'affichage de la colonne « Provenance ».",
    )

    @api.depends('order_line.police_description_expected')
    def _compute_police_registre_concerne(self):
        for commande in self:
            commande.police_registre_concerne = any(
                commande.order_line.mapped('police_description_expected'))

    def _police_check_registre(self):
        """Refuse un rachat dont les objets ne sont ni décrits ni situés.

        Le contrôle est posé à la confirmation, tant que le vendeur est
        encore au comptoir : plus tard, personne ne saura dire si c'était une
        gourmette ou une chaîne, ni d'où elle venait.
        """
        for commande in self:
            fautives = commande.order_line.filtered(
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

    def action_confirm(self):
        self._police_check_registre()
        return super().action_confirm()
