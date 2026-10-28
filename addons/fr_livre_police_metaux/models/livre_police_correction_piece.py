# -*- coding: utf-8 -*-
"""Corriger une pièce inscrite au registre, depuis la pièce elle-même.

Une pièce comptabilisée ne revient pas au brouillon dès qu'elle est inscrite
(voir ``account_move.button_draft``). Les chemins de correction existent —
rectifier, requalifier — mais ils partent du registre, et le comptoir part de
la facture. Faute de les trouver, une erreur de dénomination s'est corrigée
un jour par une vente fictive et dix-huit sorties qui n'avaient pas eu lieu.

Cet écran ne corrige rien lui-même, sauf l'annulation : il demande d'abord
ce qui est faux, dit ce que la correction va toucher, puis ouvre l'écran qui
la fait. Les trois premiers choix mènent aux assistants du registre, qui
portent déjà leur motif et ajustent le stock.

L'annulation est la seule correction qui n'avait pas d'écran. Elle défait
toute l'opération : chaque inscription est rectifiée à zéro, avec le motif
(CGI, ann. IV, art. 56 J sexdecies, 2° c), le stock suit, et la pièce reçoit
une **contre-pièce** — un avoir pour une vente, une facture pour un rachat.
La pièce d'origine demeure, comme l'inscription d'origine demeure au
registre. Elle est réservée au responsable.

Un rachat ne s'annule plus quand son année est déclarée à la DGFiP : la
déclaration porte le cumul annuel des achats auprès de chaque vendeur (CGI,
art. 1649 bis), et le changer demande une déclaration rectificative, que le
cahier des charges de la DGFiP n'admet qu'une fois par année.
"""

from odoo import Command, _, api, fields, models
from odoo.exceptions import UserError


class LivrePoliceCorrectionPiece(models.TransientModel):
    _name = 'livre.police.correction.piece'
    _description = "Livre de police - corriger une pièce inscrite"

    move_id = fields.Many2one(
        'account.move', string="Pièce", required=True, readonly=True,
        ondelete='cascade',
    )
    inscription_ids = fields.Many2many(
        'livre.police.ligne', string="Inscriptions de la pièce",
        compute='_compute_inscription_ids',
    )
    nature = fields.Selection(
        [('titre', "L'article ou le titre est faux"),
         ('mention', "Une mention est fausse (vendeur, description, prix…)"),
         ('quantite', "La quantité ou le poids est faux"),
         ('annulation', "Toute l'opération est à annuler")],
        string="Qu'est-ce qui est faux ?", required=True, default='mention',
    )
    ligne_id = fields.Many2one(
        'livre.police.ligne', string="Inscription concernée",
        domain="[('id', 'in', inscription_ids)]",
        help="L'inscription à corriger, quand la pièce en porte plusieurs.",
    )
    consequences = fields.Html(
        string="Ce que la correction va toucher",
        compute='_compute_consequences', sanitize=False,
    )
    motif = fields.Text(
        string="Motif de l'annulation",
        help="Ce qui a été constaté. Il s'inscrit sur chaque rectification : "
             "une rectification sans motif ne vaut pas (CGI, ann. IV, "
             "art. 56 J sexdecies, 2° c).",
    )
    annuler_reglement = fields.Boolean(
        string="Annuler aussi le règlement",
        help="Annule le paiement enregistré sur la pièce, s'il n'est pas "
             "encore rapproché d'un relevé bancaire. Sans cette case, le "
             "paiement reste et devient un montant à rembourser ou à "
             "réaffecter.",
    )

    @api.depends('move_id')
    def _compute_inscription_ids(self):
        for wiz in self:
            wiz.inscription_ids = wiz.move_id._police_inscriptions()

    @api.model
    def default_get(self, champs):
        valeurs = super().default_get(champs)
        piece = self.env['account.move'].browse(
            valeurs.get('move_id') or self.env.context.get('default_move_id'))
        inscriptions = piece._police_inscriptions()
        if len(inscriptions) == 1:
            valeurs['ligne_id'] = inscriptions.id
        return valeurs

    def _rachat(self):
        return bool(self.inscription_ids.filtered(lambda l: l.sens == 'entree'))

    @api.depends('nature', 'move_id')
    def _compute_consequences(self):
        for wiz in self:
            rachat = wiz._rachat()
            numeros = ", ".join(wiz.inscription_ids.mapped('numero_ordre'))
            if wiz.nature == 'titre':
                texte = _(
                    "<p>Le métal est bien entré, mais sous un autre nom. Il "
                    "se <b>requalifie</b> : l'inscription d'origine se réduit, "
                    "et ce qu'il est réellement s'inscrit sous un nouveau "
                    "numéro d'ordre — donc une nouvelle étiquette sur le "
                    "sachet. Le stock change de nature, pas de quantité.</p>"
                    "<p>La facture ne change pas.</p>") if rachat else _(
                    "<p>Une sortie dit ce qui est parti et ne se requalifie "
                    "pas. Si le mauvais article a été vendu, c'est toute "
                    "l'opération qui est à annuler, puis à refaire.</p>")
            elif wiz.nature == 'mention':
                texte = _(
                    "<p>L'inscription d'origine reste au registre telle "
                    "qu'elle a été écrite. La correction s'inscrit à la "
                    "suite, sous un nouveau numéro d'ordre, avec son "
                    "motif.</p><p>Ni le stock ni la facture ne changent.</p>")
            elif wiz.nature == 'quantite':
                texte = _(
                    "<p>La quantité se rectifie au registre, avec son motif, "
                    "et le stock du lot est ajusté d'autant.</p>"
                    "<p>La facture ne change pas : si le montant est faux "
                    "aussi, c'est toute l'opération qui est à annuler, puis "
                    "à refaire.</p>")
            else:
                texte = _(
                    "<ul>"
                    "<li><b>Registre</b> : les inscriptions %(numeros)s sont "
                    "rectifiées à zéro, avec le motif. Elles restent "
                    "lisibles.</li>"
                    "<li><b>Stock</b> : %(stock)s</li>"
                    "<li><b>Comptabilité</b> : une contre-pièce (%(contre)s) "
                    "solde la pièce. La pièce d'origine demeure.</li>"
                    "<li><b>Argent</b> : le règlement n'est annulé que si "
                    "la case est cochée, et seulement s'il n'est pas "
                    "rapproché de la banque. Sinon il reste à rembourser ou "
                    "à réaffecter.</li>"
                    "</ul>"
                    "<p>Réservé au responsable du livre de police.</p>",
                    numeros=numeros or _("(aucune)"),
                    stock=_("le métal du rachat ressort du stock — refusé si "
                            "une partie du lot est déjà revendue ou "
                            "transférée.") if rachat else _(
                            "le métal sorti revient dans ses lots, par un "
                            "retour de la livraison. La commande est annulée "
                            "si plus rien n'y reste facturé."),
                    contre=_("une facture") if rachat else _("un avoir"))
            wiz.consequences = texte

    def action_continuer(self):
        self.ensure_one()
        inscriptions = self.inscription_ids
        if self.nature == 'annulation':
            return self._annuler()
        if self.nature == 'titre':
            entrees = inscriptions.filtered(lambda l: l.sens == 'entree')
            if not entrees:
                raise UserError(_(
                    "Une sortie dit ce qui est parti et ne se requalifie pas. "
                    "Choisissez « Toute l'opération est à annuler », puis "
                    "refaites la pièce avec le bon article."))
            return self._ouvrir('livre.police.requalification',
                                _("Requalifier des parts de lots"),
                                {'active_model': 'livre.police.ligne',
                                 'active_ids': entrees.ids})
        if (self.nature == 'quantite' and len(inscriptions) > 1
                and all(l.sens == 'entree' for l in inscriptions)):
            return self._ouvrir('livre.police.rectification.quantite',
                                _("Rectifier des quantités"),
                                {'active_model': 'livre.police.ligne',
                                 'active_ids': inscriptions.ids})
        if not self.ligne_id:
            raise UserError(_(
                "La pièce porte plusieurs inscriptions : choisissez celle à "
                "corriger."))
        return self.ligne_id.action_rectifier()

    def _ouvrir(self, modele, nom, contexte):
        return {
            'type': 'ir.actions.act_window',
            'name': nom,
            'res_model': modele,
            'view_mode': 'form',
            'target': 'new',
            'context': contexte,
        }

    # -- l'annulation ------------------------------------------------------

    def _retourner(self, a_rendre):
        """Fait revenir par un retour chaque départ de ``a_rendre``.

        Les lignes du retour sont posées à la main, lot par lot : Odoo les
        répartirait sur les lots de toute la livraison, et la pièce annulée
        n'en couvre peut-être qu'une partie.
        """
        bons = {}
        for depart, quantite in a_rendre:
            bons.setdefault(depart.picking_id, []).append((depart, quantite))
        for bon, departs in bons.items():
            assistant = self.env['stock.return.picking'].create(
                {'picking_id': bon.id})
            for ligne in assistant.product_return_moves:
                ligne.quantity = sum(q for d, q in departs
                                     if d.move_id == ligne.move_id)
            retour = assistant._create_return()
            retour.move_line_ids.unlink()
            for depart, quantite in departs:
                mouvement = retour.move_ids.filtered(
                    lambda m: m.origin_returned_move_id == depart.move_id)
                self.env['stock.move.line'].create({
                    'move_id': mouvement.id,
                    'picking_id': retour.id,
                    'product_id': depart.product_id.id,
                    'product_uom_id': depart.product_uom_id.id,
                    'lot_id': depart.lot_id.id,
                    'quantity': quantite,
                    'location_id': mouvement.location_id.id,
                    'location_dest_id': mouvement.location_dest_id.id,
                })
            retour.move_ids.picked = True
            retour.button_validate()

    def _verifier_annulation(self):
        piece = self.move_id
        if not self.env.user.has_group(
                'fr_livre_police_metaux.group_livre_police_responsable'):
            raise UserError(_(
                "L'annulation d'une opération inscrite est réservée au "
                "responsable du livre de police."))
        if not (self.motif or '').strip():
            raise UserError(_(
                "Une rectification s'inscrit avec son motif : « par création "
                "d'un nouvel enregistrement avec indication de son motif » "
                "(CGI, ann. IV, art. 56 J sexdecies, 2° c)."))
        if piece.reversal_move_ids.filtered(lambda m: m.state == 'posted'):
            raise UserError(_(
                "« %(piece)s » a déjà une contre-pièce : %(contre)s.",
                piece=piece.display_name,
                contre=", ".join(piece.reversal_move_ids.mapped('display_name'))))
        for inscription in self.inscription_ids.filtered(
                lambda l: l.sens == 'entree'):
            if inscription.poids_sorti > 0.00005:
                raise UserError(_(
                    "Le lot %(numero)s est déjà reparti en partie (%(poids)s g "
                    "vendus ou transférés). Ces départs sont inscrits au "
                    "registre : le rachat ne peut plus s'annuler d'un bloc. "
                    "Rectifiez ce qui est faux, inscription par inscription.",
                    numero=inscription.numero_ordre,
                    poids=round(inscription.poids_sorti, 4)))
        if self._rachat() and 'fr.dmet.declaration' in self.env:
            deposee = self.env['fr.dmet.declaration'].sudo().search([
                ('millesime', '=', piece.invoice_date.year),
                ('company_ids', 'in', piece.company_id.id),
                ('state', '=', 'deposited'),
            ], limit=1)
            if deposee:
                raise UserError(_(
                    "Les achats de %(annee)s sont déjà déclarés à la DGFiP "
                    "(%(declaration)s). Annuler ce rachat changerait le cumul "
                    "déclaré pour ce vendeur, ce qui demande une déclaration "
                    "rectificative : selon le cahier des charges de la DGFiP, "
                    "elle ne se dépose qu'une fois par année, et plus aucun "
                    "fichier n'est accepté après le 30 septembre de l'année "
                    "qui suit. Voyez-le avec votre comptable avant de "
                    "corriger.",
                    annee=piece.invoice_date.year,
                    declaration=deposee.display_name))
        if self.annuler_reglement:
            rapproches = piece._get_reconciled_payments().filtered('is_matched')
            if rapproches:
                raise UserError(_(
                    "Le règlement %(paiements)s est rapproché de la banque : "
                    "l'argent a réellement circulé, et ce n'est pas d'ici "
                    "qu'il s'annule. Décochez la case ; le remboursement se "
                    "traitera à part.",
                    paiements=", ".join(rapproches.mapped('display_name'))))

    def _annuler(self):
        self._verifier_annulation()
        piece = self.move_id
        motif = self.motif.strip()

        if self.annuler_reglement:
            paiements = piece._get_reconciled_payments()
            paiements.action_draft()
            paiements.action_cancel()

        lignes_de_vente = piece.invoice_line_ids.sale_line_ids
        bons = lignes_de_vente.move_ids.picking_id.filtered(
            lambda b: b.state not in ('done', 'cancel'))
        bons.action_cancel()

        a_rendre = []
        for inscription in self.inscription_ids:
            courante = inscription._rectification_finale()
            if not courante.quantite:
                continue
            mentions = {nom: (courante[nom].id
                              if courante._fields[nom].type == 'many2one'
                              else courante[nom])
                        for nom in self.env[
                            'livre.police.rectification']._MENTIONS}
            mentions.update({'quantite': 0.0, 'poids': 0.0})
            inscription._inscrire_rectification(mentions, motif)
            # Le métal vendu revient par un retour de sa livraison, qui
            # ramène la quantité livrée de la commande et garde la trace du
            # lot ; l'ajustement d'inventaire ne reste qu'au rachat.
            if inscription.sens == 'sortie' and inscription.mouvement_stock_id:
                a_rendre.append((inscription.mouvement_stock_id,
                                 courante.quantite))
            # Un rachat dont la réception n'a pas eu lieu n'a pas de lot :
            # il n'y a rien à retirer, le bon vient d'être annulé.
            elif inscription.sens == 'sortie' or inscription._lot_du_registre():
                inscription._ajuster_le_stock(-courante.quantite)
        self._retourner(a_rendre)

        piece.line_ids.remove_move_reconcile()
        contre = piece.with_context(police_contre_piece=True)._reverse_moves([{
            'ref': _("Annulation de %(piece)s : %(motif)s",
                     piece=piece.name, motif=motif),
            'invoice_date': fields.Date.context_today(self),
            'date': fields.Date.context_today(self),
        }])
        # Une commande dont plus rien ne reste facturé est annulée : elle
        # sort des ventes, et l'avoir lui reste attaché. Sinon la
        # contre-pièce s'en détache — facturés sur la quantité commandée,
        # les articles repasseraient « à facturer ».
        commandes = lignes_de_vente.order_id
        a_annuler = commandes.filtered(lambda c: not (
            c.invoice_ids.filtered(lambda f: f.state == 'posted') - piece))
        if commandes - a_annuler:
            contre.invoice_line_ids.sale_line_ids = [Command.clear()]
        contre.with_context(police_contre_piece=True,
                            move_reverse_cancel=True)._post(soft=False)
        a_annuler._action_cancel()

        piece.message_post(body=_(
            "Opération annulée par %(contre)s. Motif : %(motif)s",
            contre=contre.name, motif=motif))
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': contre.id,
            'view_mode': 'form',
        }
