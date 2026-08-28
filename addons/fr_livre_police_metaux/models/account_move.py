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

Les deux exigences ne portent pas sur les mêmes articles — voir l'en-tête de
``sale_order.py`` : la provenance est due de tout article inscrit au
registre, la description des seuls articles dont la désignation ne dit rien
de l'objet.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..tools.description import description_ajoutee
from ..tools.reglement import MODES_REGLEMENT


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
    police_origin_expected = fields.Boolean(
        string="Article au registre",
        compute='_compute_police_origin_expected',
        help="Vrai lorsque l'article fait entrer un objet au registre, et "
             "réclame donc sa provenance, indépendamment du sens de "
             "l'opération.",
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
                ligne.display_type == 'product'
                and ligne.product_id.product_tmpl_id.police_description_required)

    @api.depends('display_type',
                 'product_id.product_tmpl_id.metal_regulated',
                 'product_id.product_tmpl_id.police_description_required')
    def _compute_police_origin_expected(self):
        """Voir ``sale_order.py`` : les deux signaux valent."""
        for ligne in self:
            fiche = ligne.product_id.product_tmpl_id
            ligne.police_origin_expected = bool(
                ligne.display_type == 'product'
                and (fiche.metal_regulated or fiche.police_description_required))

    def _police_entree(self):
        """La ligne fait-elle entrer un objet dans les murs ?"""
        self.ensure_one()
        type_piece = self.move_id.move_type
        return bool(
            (type_piece == 'out_refund' and self.quantity > 0)
            or (type_piece == 'out_invoice' and self.quantity < 0))

    @api.depends('police_description_expected', 'quantity', 'move_id.move_type')
    def _compute_police_description_required(self):
        for ligne in self:
            ligne.police_description_required = bool(
                ligne.police_description_expected and ligne._police_entree())

    @api.depends('police_origin_expected', 'quantity', 'move_id.move_type')
    def _compute_police_origin_required(self):
        for ligne in self:
            ligne.police_origin_required = bool(
                ligne.police_origin_expected and ligne._police_entree())

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


class AccountMove(models.Model):
    _inherit = 'account.move'

    police_registre_concerne = fields.Boolean(
        string="Document soumis au registre",
        compute='_compute_police_registre_concerne',
        help="Vrai sur une pièce client portant un article inscrit au "
             "registre. Commande l'affichage de la colonne « Provenance ».",
    )

    police_reglement = fields.Selection(
        MODES_REGLEMENT, string="Mode de règlement",
        help="Comment le vendeur a été payé. Repris du devis, ou saisi ici "
             "lorsque l'avoir est établi directement.\n\n"
             "Le modèle officiel du registre range cette mention avec le "
             "prix (arrêté du 15 mai 2020, annexe I). Seuls le chèque barré "
             "et le virement sont proposés : « lorsqu'un professionnel "
             "achète des métaux à un particulier ou à un autre "
             "professionnel, le paiement est effectué par chèque barré ou "
             "par virement à un compte ouvert au nom du vendeur » (code "
             "monétaire et financier, art. L112-6).",
    )
    police_representant_id = fields.Many2one(
        'res.partner', string="Représentant",
        domain="[('is_company', '=', False)]",
        ondelete='restrict', index='btree_not_null',
        help="Personne physique qui a remis les objets au nom de la société "
             "(art. R321-3 2° du code pénal).\n\n"
             "Le client de la pièce est la société — c'est elle qui a vendu. "
             "La personne, elle, est ce que le registre doit nommer, et c'est "
             "ce champ qui la porte. Repris du devis, où c'est elle qui "
             "figurait comme client.",
    )
    # « Poste » (`function`) — voir la note dans `sale_order.py`.
    police_representant_poste = fields.Char(
        string="Poste du représentant",
        compute='_compute_police_representant_poste',
        help="Poste occupé dans la société, au sens du champ « Poste » de la "
             "fiche contact. C'est la « qualité » que le registre exige du "
             "représentant (art. R321-3 2° du code pénal). Simple report de "
             "sa fiche, non modifiable ici.",
    )
    police_representant_required = fields.Boolean(
        string="Représentant exigé",
        compute='_compute_police_representant_required',
        help="Vrai sur une pièce qui fait entrer au registre un objet remis "
             "au nom d'une société.",
    )
    police_representant_missing = fields.Boolean(
        string="Personne physique non désignée",
        compute='_compute_police_representant_missing',
        help="Aucune personne physique n'est nommée, et le registre en veut "
             "une.",
    )
    police_poste_missing = fields.Boolean(
        string="Poste manquant",
        compute='_compute_police_poste_missing',
        help="La personne qui engage la société est nommée, mais sa fiche ne "
             "dit pas à quel titre elle l'engage.",
    )

    def _police_personne(self):
        """La personne physique que le registre doit nommer.

        Deux chemins mènent ici, et ils ne posent pas la personne au même
        endroit. Une pièce issue d'un devis porte la société comme client et
        la personne dans ``police_representant_id`` (voir
        ``sale_order._prepare_invoice``). Une pièce saisie directement porte
        souvent le contact comme client, et rien d'autre. Les deux valent.
        """
        self.ensure_one()
        if self.police_representant_id:
            return self.police_representant_id
        return self.partner_id if not self.partner_id.is_company \
            else self.env['res.partner']

    @api.depends('invoice_line_ids.police_origin_required')
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
                piece.invoice_line_ids.mapped('police_origin_required'))

    @api.onchange('partner_id')
    def _onchange_police_societe_comme_client(self):
        """Voir ``sale_order.py``. Limité à l'avoir : c'est la seule pièce qui
        constate un rachat au comptoir, et donc la seule où le client doive
        être la société plutôt que la personne venue pour elle."""
        for piece in self:
            if piece.move_type != 'out_refund':
                continue
            personne = piece.partner_id
            societe = personne.commercial_partner_id
            if personne and not personne.is_company and societe != personne:
                piece.partner_id = societe
                piece.police_representant_id = personne

    # Pas de pendant à `police_representant_expected` ici : sur une pièce
    # comptable le signe de la quantité est arrêté, on sait déjà si un objet
    # entre. Voir `_compute_police_registre_concerne`, qui suit la même règle.
    @api.depends('commercial_partner_id.is_company',
                 'invoice_line_ids.police_origin_required')
    def _compute_police_representant_required(self):
        """Voir ``sale_order.py`` : ce qui compte est la société, pas le
        contact par lequel on la joint."""
        for piece in self:
            piece.police_representant_required = bool(
                piece.commercial_partner_id.is_company
                and any(piece.invoice_line_ids.mapped('police_origin_required')))

    @api.depends('police_representant_required', 'police_representant_id',
                 'partner_id.is_company')
    def _compute_police_representant_missing(self):
        for piece in self:
            piece.police_representant_missing = bool(
                piece.police_representant_required and not piece._police_personne())

    @api.depends('police_representant_required', 'police_representant_id',
                 'partner_id.is_company',
                 'police_representant_id.function', 'partner_id.function')
    def _compute_police_poste_missing(self):
        for piece in self:
            personne = piece._police_personne()
            piece.police_poste_missing = bool(
                piece.police_representant_required
                and personne and not personne.function)

    @api.depends('police_representant_id.function', 'partner_id.function',
                 'partner_id.is_company')
    def _compute_police_representant_poste(self):
        for piece in self:
            piece.police_representant_poste = piece._police_personne().function

    def _police_check_representant(self):
        """Voir ``sale_order.py`` : une société ne se présente pas au comptoir."""
        for piece in self:
            societe = piece.commercial_partner_id
            if piece.police_representant_missing:
                raise UserError(_(
                    "« %(societe)s » est une personne morale, et aucune "
                    "personne physique n'est nommée sur cette pièce.\n\n"
                    "Le registre comporte, pour une société, « la dénomination "
                    "et le siège de celle-ci ainsi que les nom, prénoms, "
                    "qualité et domicile du représentant » (art. R321-3 2° du "
                    "code pénal). Indiquez qui a remis les objets.",
                    societe=societe.display_name))
            if piece.police_poste_missing:
                raise UserError(_(
                    "La fiche de « %(personne)s » ne dit pas quel poste elle "
                    "occupe.\n\n"
                    "Le registre veut « les nom, prénoms, qualité et domicile "
                    "du représentant » de la personne morale (art. R321-3 2° "
                    "du code pénal). Ouvrez sa fiche contact et renseignez "
                    "« Poste » : à quel titre engage-t-elle « %(societe)s » — "
                    "gérant(e), mandataire, salarié(e) ?",
                    personne=piece._police_personne().display_name,
                    societe=societe.display_name))

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

    def _police_check_reglement(self):
        """Voir ``sale_order.py``. Répété ici : un avoir se saisit aussi
        directement, et la mention est due de la pièce, pas du devis."""
        for piece in self:
            if piece.police_registre_concerne and not piece.police_reglement:
                raise UserError(_(
                    "Le registre veut savoir comment le rachat « %(piece)s » "
                    "a été payé : le modèle officiel porte le prix d'achat et "
                    "le mode de règlement dans la même colonne (arrêté du "
                    "15 mai 2020, annexe I).\n\n"
                    "Seuls le chèque barré et le virement sont proposés : "
                    "« lorsqu'un professionnel achète des métaux à un "
                    "particulier ou à un autre professionnel, le paiement est "
                    "effectué par chèque barré ou par virement à un compte "
                    "ouvert au nom du vendeur » (code monétaire et financier, "
                    "art. L112-6). Les espèces sont exclues quel que soit le "
                    "montant.",
                    piece=piece.display_name))

    def _post(self, soft=True):
        self._police_check_representant()
        self._police_check_registre()
        self._police_check_reglement()
        pieces = super()._post(soft=soft)
        # L'inscription vient après, jamais avant : c'est la comptabilisation
        # qui arrête la pièce, et un registre n'inscrit pas un brouillon.
        # `soft=True` peut ne poster qu'une partie de `self` — on n'inscrit
        # que ce qui est réellement posté.
        self.env['livre.police.ligne']._inscrire(pieces)
        return pieces
