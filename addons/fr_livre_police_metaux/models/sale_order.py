# -*- coding: utf-8 -*-
"""Le rachat se saisit sur un devis, en quantité négative.

L'établissement n'y vend rien : il achète. C'est le signe de la quantité qui
dit le sens de l'opération, et donc si la ligne fait entrer un objet dans les
murs — le seul cas où le registre réclame description et provenance.

L'art. R321-3 3° les tient dans la même phrase : « la nature, la provenance et
la description des objets acquis ». **Elles ne manquent pourtant pas de la
même façon.** La description d'une « 20 FRANCS OR » est déjà donnée par la
désignation — c'est un type catalogué, ses caractéristiques ne varient pas.
La provenance ne l'est jamais : elle est déclarée par le vendeur, et rien
d'autre ne la fournit, que l'objet soit une bague anonyme ou un souverain.

Les deux exigences se règlent donc séparément :

* la **provenance** est due de tout article qui fait entrer un objet au
  registre — « Soumis au livre de police » sur sa fiche, ou, à défaut, la
  case de description ci-dessous, qui l'affirme autrement ;
* la **description** n'est due que des articles dont la désignation ne dit
  rien de l'objet — un rachat d'or au gramme, un lot de pièces. C'est ce que
  déclare la case sur la fiche de l'article.

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
    police_origin_expected = fields.Boolean(
        string="Article au registre",
        compute='_compute_police_origin_expected',
        help="Vrai lorsque l'article fait entrer un objet au registre, et "
             "réclame donc sa provenance. Ne dépend pas du sens de "
             "l'opération : la colonne s'ouvre dès le choix de l'article.",
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
    police_origin_required = fields.Boolean(
        string="Provenance exigée",
        compute='_compute_police_origin_required',
        help="Vrai lorsque la ligne fait entrer un objet au registre.",
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

    @api.depends('display_type',
                 'product_id.product_tmpl_id.metal_regulated',
                 'product_id.product_tmpl_id.police_description_required')
    def _compute_police_origin_expected(self):
        """Tout objet qui entre au registre doit sa provenance.

        « Soumis au livre de police » le dit déjà de l'article. La case de
        description l'affirme autrement, sur un article qu'on aurait sorti du
        registre par ailleurs : les deux signaux valent, et le second ne peut
        pas contredire le premier sans laisser un objet sans origine.
        """
        for ligne in self:
            fiche = ligne.product_id.product_tmpl_id
            ligne.police_origin_expected = bool(
                not ligne.display_type
                and (fiche.metal_regulated or fiche.police_description_required))

    @api.depends('police_description_expected', 'product_uom_qty')
    def _compute_police_description_required(self):
        for ligne in self:
            ligne.police_description_required = bool(
                ligne.police_description_expected and ligne.product_uom_qty < 0)

    @api.depends('police_origin_expected', 'product_uom_qty')
    def _compute_police_origin_required(self):
        for ligne in self:
            ligne.police_origin_required = bool(
                ligne.police_origin_expected and ligne.product_uom_qty < 0)

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

    @api.depends('police_origin_required', 'police_origin_id')
    def _compute_police_origin_missing(self):
        for ligne in self:
            ligne.police_origin_missing = bool(
                ligne.police_origin_required and not ligne.police_origin_id)

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
        help="Vrai dès qu'une ligne porte un article inscrit au registre. "
             "Commande l'affichage de la colonne « Provenance ».",
    )

    @api.depends('order_line.police_origin_expected')
    def _compute_police_registre_concerne(self):
        for commande in self:
            commande.police_registre_concerne = any(
                commande.order_line.mapped('police_origin_expected'))

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
