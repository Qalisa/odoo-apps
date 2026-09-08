# -*- coding: utf-8 -*-
"""Reclasser une part d'un lot sous sa nature réelle.

Un lot entre au registre sous la nature qu'on lui prête au comptoir. Le tri,
plus tard, révèle ce qu'il contenait : une part n'est pas de l'or titré comme
le reste, c'est de l'or blanc — palladium, platine. Elle ne part pas au
fondeur avec les autres ; elle reste, et il faut qu'elle reste sous son vrai
nom.

Rien n'entre et rien ne sort. Le métal était déjà là, sous une autre
désignation. C'est pourquoi cet écran n'est ni un achat ni une vente :

- **aucun tiers, aucun prix.** Le contournement consistant à revendre le lot
  entier puis à le racheter à 0 € porterait au registre trois mentions
  fausses : un vendeur qui n'a rien vendu, une personne physique de chez lui
  qui aurait remis les objets (art. R321-3 2°), et une sortie pour du métal
  qui n'est jamais parti ;
- **la date d'entrée ne change pas.** Ce métal est entré dans ces murs le
  jour du rachat, et le tri n'est pas une entrée ;
- **un nouveau numéro d'ordre**, en revanche. C'est un autre lot, il porte
  une autre étiquette, et « le numéro d'ordre […] figure de manière apparente
  sur chaque objet ou lot d'objets » (c. pén., art. R321-4).

L'inscription d'origine, elle, se réduit d'autant — par une rectification
portant son motif, la seule correction que le texte admette (CGI, ann. IV,
art. 56 J sexdecies, 2° c).
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.fr_numismatics_metals.tools import metals


class LivrePoliceRequalification(models.TransientModel):
    _name = 'livre.police.requalification'
    _description = "Livre de police - requalifier une part de lot"

    inscription_id = fields.Many2one(
        'livre.police.ligne', string="Inscription à reclasser",
        required=True, readonly=True, ondelete='cascade',
    )
    numero_ordre = fields.Char(
        related='inscription_id.numero_ordre', readonly=True,
        string="N° d'ordre d'origine")
    designation_origine = fields.Char(
        related='inscription_id.designation', readonly=True,
        string="Désignation d'origine")
    quantite_inscrite = fields.Float(
        string="Quantité inscrite", digits=(12, 4), readonly=True,
        compute='_compute_etat')
    poids_inscrit = fields.Float(
        string="Poids inscrit (g)", digits=(12, 4), readonly=True,
        compute='_compute_etat')

    quantite_retiree = fields.Float(
        string="Quantité retirée du lot", digits=(12, 4), required=True,
        help="Ce qu'on ôte de l'inscription d'origine, dans son unité à elle.",
    )
    poids_retire = fields.Float(
        string="Poids retiré (g)", digits=(12, 4), readonly=True,
        compute='_compute_poids',
        help="Déduit à la proportion de l'inscrit, comme pour toute "
             "rectification de quantité.",
    )
    product_id = fields.Many2one(
        'product.product', string="Article réel", required=True,
        domain="[('metal_regulated', '=', True)]",
        help="Ce que cette part est réellement. C'est de lui que le registre "
             "tirera la nature du métal, le titre et le régime de quantité.",
    )
    quantite = fields.Float(
        string="Quantité reclassée", digits=(12, 4), required=True,
        help="Dans l'unité du nouvel article.",
    )
    poids = fields.Float(
        string="Poids reclassé (g)", digits=(12, 4), readonly=True,
        compute='_compute_poids',
        help="Déduit du nouvel article : au gramme la quantité vaut le "
             "poids, à la pièce elle est multipliée par le poids unitaire.",
    )
    description = fields.Text(
        string="Description des objets",
        help="Ce que la désignation ne dit pas. Exigée sur les articles qui "
             "la réclament (art. R321-3 3° du code pénal).",
    )
    motif = fields.Text(
        string="Motif de la requalification", required=True,
        help="Ce que le tri a constaté. Cette mention part au registre, sur "
             "les deux inscriptions : celle qui se réduit et celle qui naît.",
    )

    @api.depends('inscription_id')
    def _compute_etat(self):
        for wiz in self:
            courante = wiz.inscription_id._rectification_finale()
            wiz.quantite_inscrite = courante.quantite
            wiz.poids_inscrit = courante.poids

    @api.depends('quantite_retiree', 'quantite', 'product_id',
                 'quantite_inscrite', 'poids_inscrit')
    def _compute_poids(self):
        for wiz in self:
            reference = wiz.quantite_inscrite
            wiz.poids_retire = (wiz.poids_inscrit * wiz.quantite_retiree
                                / reference) if reference else 0.0
            modele = wiz.product_id.product_tmpl_id
            wiz.poids = metals.derive_weight(
                modele.metal_quantity_mode, modele.metal_unit_weight,
                wiz.quantite) or 0.0

    def _verifier(self):
        self.ensure_one()
        source = self.inscription_id
        if source.sens != 'entree':
            raise UserError(_(
                "Seule une entrée se reclasse : une sortie dit ce qui est "
                "parti, et cela ne se requalifie pas."))
        if self.quantite_retiree <= 0 or self.quantite <= 0:
            raise UserError(_("Les deux quantités doivent être positives."))
        if self.quantite_retiree > self.quantite_inscrite + 0.00005:
            raise UserError(_(
                "L'inscription %(numero)s ne porte que %(inscrite)s : on ne "
                "peut pas en retirer %(retiree)s.",
                numero=source.numero_ordre, inscrite=self.quantite_inscrite,
                retiree=self.quantite_retiree))
        # Le tri sépare, il ne crée pas de matière. Un poids reclassé
        # supérieur au poids retiré ne décrirait aucune opération réelle.
        if self.poids > self.poids_retire + 0.00005:
            raise UserError(_(
                "Le poids reclassé (%(poids).4f g) dépasse le poids retiré du "
                "lot (%(retire).4f g). Un tri sépare, il ne crée pas de "
                "matière : reprenez l'une des deux quantités.",
                poids=self.poids, retire=self.poids_retire))
        modele = self.product_id.product_tmpl_id
        if not modele.metal_regulated:
            raise UserError(_(
                "« %(article)s » n'est pas soumis au livre de police : il ne "
                "peut pas désigner du métal reclassé.",
                article=self.product_id.display_name))
        if modele.police_description_required and not (self.description or '').strip():
            raise UserError(_(
                "« %(article)s » réclame une description des objets : sa "
                "désignation ne dit pas ce que le métal est.",
                article=self.product_id.display_name))

    def action_requalifier(self):
        """Réduit l'inscription d'origine, et inscrit la part reclassée."""
        self.ensure_one()
        self._verifier()
        source = self.inscription_id
        courante = source._rectification_finale()
        motif = self.motif.strip()
        Registre = self.env['livre.police.ligne']
        societe = source.company_id

        # 1. L'origine se réduit — une inscription ne se réécrit pas, la
        #    correction s'inscrit à la suite avec son motif.
        mentions = {nom: (courante[nom].id
                          if courante._fields[nom].type == 'many2one'
                          else courante[nom])
                    for nom in self.env['livre.police.rectification']._MENTIONS}
        mentions.update({
            'quantite': courante.quantite - self.quantite_retiree,
            'poids': courante.poids - self.poids_retire,
        })
        rectification = source._inscrire_rectification(mentions, _(
            "Requalification : %(quantite).4f retirés du lot et reclassés en "
            "« %(article)s ». %(motif)s",
            quantite=self.quantite_retiree,
            article=self.product_id.display_name, motif=motif))
        source._ajuster_le_stock(-self.quantite_retiree)

        # 2. La part reclassée naît sous son propre numéro d'ordre.
        numero = Registre._sequence(societe).next_by_id()
        entrepot = self.env['stock.warehouse'].sudo().search(
            [('company_id', '=', societe.id)], limit=1)
        lot = self.env['stock.lot'].sudo().with_company(societe).create({
            'name': numero, 'product_id': self.product_id.id,
            'company_id': societe.id,
        })
        quant = self.env['stock.quant'].sudo().with_company(
            societe).with_context(inventory_mode=True).create({
                'product_id': self.product_id.id,
                'location_id': entrepot.lot_stock_id.id,
                'lot_id': lot.id,
                'inventory_quantity': self.quantite,
            })
        # La requalification inscrit ce qu'elle ajuste — voir `stock_quant.py`.
        quant.with_context(police_ajustement=True).action_apply_inventory()
        mouvement = self.env['stock.move.line'].sudo().search(
            [('lot_id', '=', lot.id), ('state', '=', 'done')],
            order='id desc', limit=1)

        valeurs = Registre._valeurs_depuis_requalification(
            source, mouvement, self.product_id, self.poids,
            self.description, motif)
        valeurs['numero_ordre'] = numero
        inscription = Registre.sudo().create(valeurs)

        return {
            'type': 'ir.actions.act_window',
            'name': _("Requalification de %s") % source.numero_ordre,
            'res_model': 'livre.police.ligne',
            'view_mode': 'list,form',
            'domain': [('id', 'in', (rectification | inscription).ids)],
        }
