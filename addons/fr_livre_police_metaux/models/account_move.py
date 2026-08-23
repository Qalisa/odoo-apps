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

Le libellé de la ligne est recopié du devis par Odoo : la description suit
donc la ligne sans qu'on ait à la transporter.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..tools.description import description_ajoutee


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

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

    @api.depends('display_type', 'quantity', 'move_id.move_type',
                 'product_id.product_tmpl_id.police_description_required')
    def _compute_police_description_required(self):
        for ligne in self:
            type_piece = ligne.move_id.move_type
            entree = (
                (type_piece == 'out_refund' and ligne.quantity > 0)
                or (type_piece == 'out_invoice' and ligne.quantity < 0))
            ligne.police_description_required = bool(
                ligne.display_type == 'product' and entree
                and ligne.product_id.product_tmpl_id.police_description_required)

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


class AccountMove(models.Model):
    _inherit = 'account.move'

    def _police_check_descriptions(self):
        for piece in self:
            muettes = piece.invoice_line_ids.filtered('police_description_missing')
            if muettes:
                raise UserError(_(
                    "Les objets rachetés doivent être décrits (art. R321-3 3° "
                    "du code pénal). Complétez la description sous la "
                    "désignation, sur :\n  - %s",
                    "\n  - ".join(l.product_id.display_name for l in muettes)))

    def _post(self, soft=True):
        self._police_check_descriptions()
        return super()._post(soft=soft)
