# -*- coding: utf-8 -*-
"""Inscrire une arrivée que le document de transfert n'a pas portée.

Le métal passe d'un établissement à l'autre par un document de transfert, qui
tient les deux bouts : la sortie chez celui qui envoie, l'entrée chez celui
qui reçoit. Quand il n'a pas été employé — un bon de livraison fait à la main,
et le métal part quand même — la sortie s'inscrit tout de même, parce qu'elle
naît du mouvement de stock. L'entrée, elle, ne s'inscrit nulle part.

Le comptoir d'arrivée détient alors du métal que son registre ignore, et c'est
le manquement : « un registre est tenu pour chaque établissement » (c. pén.,
art. R321-6). Cet écran inscrit l'entrée manquante.

Il ne refait pas le transfert, et ne prétend pas que rien ne s'est passé. La
sortie de l'autre comptoir reste ce qu'elle est — elle est vraie, le métal est
bien parti. Ce qui lui manque, c'est de dire où : cela se rectifie de son
côté, par une inscription portant son motif.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LivrePoliceRegularisation(models.TransientModel):
    _name = 'livre.police.regularisation'
    _description = "Livre de police - régulariser une arrivée"

    sortie_id = fields.Many2one(
        'livre.police.ligne', string="Sortie de l'autre établissement",
        required=True, ondelete='cascade',
        domain="[('sens', '=', 'sortie')]",
        help="L'inscription de sortie déjà portée au registre du comptoir "
             "qui a envoyé le métal. C'est elle qui dit ce qui est parti, "
             "quand, et de quel lot.",
    )
    company_id = fields.Many2one(
        'res.company', string="Établissement qui a reçu", required=True,
        help="Le comptoir où le métal se trouve réellement, et dont le "
             "registre doit désormais le porter.",
    )
    designation = fields.Char(related='sortie_id.designation', readonly=True)
    quantite_sortie = fields.Float(
        related='sortie_id.quantite', string="Quantité sortie", readonly=True)
    date_sortie = fields.Date(
        related='sortie_id.date_mouvement', string="Partie le", readonly=True)
    etablissement_depart = fields.Char(
        related='sortie_id.company_id.display_name', readonly=True,
        string="Partie de")
    quantite = fields.Float(
        string="Quantité reçue", digits=(12, 4), required=True,
        help="Ce que le comptoir a réellement reçu. Au plus ce qui est sorti "
             "de l'autre : le registre de départ fait foi de ce qui a quitté "
             "ses murs.",
    )
    motif = fields.Text(
        string="Motif de la régularisation", required=True,
        help="Pourquoi cette entrée s'inscrit après coup — le document de "
             "transfert n'a pas été employé, et il faut le dire. Cette "
             "mention part au registre : sans elle, un lecteur verrait une "
             "entrée sans cause.",
    )

    @api.model
    def default_get(self, champs):
        valeurs = super().default_get(champs)
        sortie = self.env['livre.police.ligne'].browse(
            valeurs.get('sortie_id')
            or self.env.context.get('default_sortie_id'))
        if sortie.exists():
            valeurs.setdefault('quantite', sortie.quantite)
        return valeurs

    def _verifier(self):
        self.ensure_one()
        sortie = self.sortie_id
        if sortie.sens != 'sortie':
            raise UserError(_(
                "L'inscription %(numero)s n'est pas une sortie : elle ne peut "
                "pas être l'origine d'une arrivée.", numero=sortie.numero_ordre))
        if self.company_id == sortie.company_id:
            raise UserError(_(
                "Le métal serait reçu par l'établissement qui l'a envoyé. "
                "Une régularisation d'arrivée relie deux registres, pas un "
                "registre à lui-même."))
        if self.quantite <= 0:
            raise UserError(_("La quantité reçue doit être positive."))
        if self.quantite > sortie.quantite + 0.00005:
            raise UserError(_(
                "Le registre de %(etablissement)s dit que %(sortie)s sont "
                "sortis : on ne peut pas en faire entrer %(entree)s ailleurs.",
                etablissement=sortie.company_id.display_name,
                sortie=sortie.quantite, entree=self.quantite))
        manquantes = (self.company_id | sortie.company_id) - self.env.user.company_ids
        if manquantes:
            raise UserError(_(
                "Vous n'avez pas accès à l'établissement %(societes)s.\n\n"
                "Régulariser une arrivée touche les deux registres : celui "
                "qui a inscrit la sortie et celui qui doit inscrire "
                "l'entrée.",
                societes=", ".join(manquantes.mapped('display_name'))))
        deja = self.env['livre.police.ligne'].sudo().search([
            ('company_id', '=', self.company_id.id),
            ('origine_id', '=', (sortie.origine_id or sortie.entree_id or sortie).id),
            ('sens', '=', 'entree'),
        ], limit=1)
        if deja:
            raise UserError(_(
                "Ce métal est déjà entré au registre de %(etablissement)s "
                "sous le numéro %(numero)s. Une entrée ne s'inscrit pas deux "
                "fois.",
                etablissement=self.company_id.display_name,
                numero=deja.numero_ordre))

    def action_inscrire(self):
        """Inscrit l'entrée manquante, et fait entrer le métal en stock."""
        self.ensure_one()
        self._verifier()
        sortie = self.sortie_id
        Registre = self.env['livre.police.ligne']
        entrepot = self.env['stock.warehouse'].sudo().search(
            [('company_id', '=', self.company_id.id)], limit=1)
        if not entrepot:
            raise UserError(_(
                "L'établissement %(societe)s n'a pas d'entrepôt : le métal "
                "n'a nulle part où arriver.",
                societe=self.company_id.display_name))

        # Le sachet garde le numéro du **comptoir de rachat** — c'est celui
        # qui y est apposé (c. pén., art. R321-4) — et non celui de la sortie,
        # qui n'est qu'un mouvement. Le nom en base se qualifie, « MONDE/000026
        # », parce que le même numéro existe dans chaque agence et qu'Odoo
        # refuserait le second.
        #
        # C'est le **même enregistrement de lot** qui traverse, comme dans un
        # transfert : rien n'est recréé à l'arrivée, et la traçabilité du
        # stock n'est pas coupée en deux.
        origine = sortie.origine_id or sortie.entree_id or sortie
        produit = sortie.mouvement_stock_id.product_id
        nom = origine._nom_lot_partage()
        lot = sortie.mouvement_stock_id.lot_id.sudo()
        if not lot:
            raise UserError(_(
                "La sortie %(numero)s ne désigne aucun lot : rien ne permet "
                "de savoir quel métal est arrivé.", numero=sortie.numero_ordre))
        if lot.name != nom or lot.company_id:
            lot.write({'name': nom, 'company_id': False})

        quant = self.env['stock.quant'].sudo().with_company(
            self.company_id).with_context(inventory_mode=True).create({
                'product_id': produit.id,
                'location_id': entrepot.lot_stock_id.id,
                'lot_id': lot.id,
                'inventory_quantity': self.quantite,
            })
        # Le document inscrit ce qu'il ajuste : il passe donc la garde
        # posée sur l'ajustement nu (voir `stock_quant.py`).
        quant.with_context(police_ajustement=True).action_apply_inventory()
        mouvement = self.env['stock.move.line'].sudo().search(
            [('lot_id', '=', lot.id), ('state', '=', 'done'),
             ('company_id', '=', self.company_id.id)],
            order='id desc', limit=1)

        valeurs = Registre._valeurs_depuis_regularisation(
            sortie, mouvement, self.motif.strip())
        valeurs['numero_ordre'] = Registre._sequence(
            self.company_id).next_by_id()
        inscription = Registre.sudo().create(valeurs)
        return {
            'type': 'ir.actions.act_window',
            'name': _("Inscription %s") % inscription.numero_ordre,
            'res_model': 'livre.police.ligne',
            'res_id': inscription.id,
            'view_mode': 'form',
        }
