# -*- coding: utf-8 -*-
"""Reclasser sous leur nature réelle des parts prélevées sur plusieurs lots.

Un lot entre au registre sous la nature qu'on lui prête au comptoir. Le tri,
plus tard, révèle ce qu'il contenait : une part n'est pas de l'or titré comme
le reste, c'est de l'or blanc — palladium, platine. Elle ne part pas au
fondeur avec les autres ; elle reste, et il faut qu'elle reste sous son vrai
nom.

Le tri ne porte pas sur un lot, il porte sur une tablée. L'or blanc sort de
huit rachats à la fois et finit dans un seul sachet. Le reclasser lot par lot
donnerait huit numéros d'ordre, donc huit étiquettes, à un sachet unique dont
plus personne ne saura séparer les grains : le registre serait exact et la
réalité fausse. Ce que cet écran inscrit est donc **un lot**, sous un seul
numéro d'ordre, portant une seule étiquette — « le numéro d'ordre […] figure
de manière apparente sur chaque objet ou lot d'objets » (c. pén., art.
R321-4).

Rien n'entre et rien ne sort. Le métal était déjà là, sous d'autres
désignations. C'est pourquoi cet écran n'est ni un achat ni une vente :

- **aucun tiers, aucun prix.** Le contournement consistant à revendre les lots
  puis à les racheter à 0 € porterait au registre trois mentions fausses : un
  vendeur qui n'a rien vendu, une personne physique de chez lui qui aurait
  remis les objets (art. R321-3 2°), et une sortie pour du métal qui n'est
  jamais parti ;
- **la date d'entrée n'est pas celle du tri.** Ce métal est entré dans ces
  murs le jour des rachats, et le tri n'est pas une entrée. Quand plusieurs
  lots se rejoignent, c'est **la plus récente** de leurs dates que
  l'inscription porte : la plus ancienne ferait dire au registre que tout ce
  métal était là avant qu'il n'y soit, et rien ne doit surestimer la durée de
  détention. Le détail, lui, ne se perd pas — la provenance nomme chaque
  rachat avec sa date ;
- **un nouveau numéro d'ordre**, en revanche, pour la raison dite plus haut.

Les mentions d'origine — le comptoir de rachat, son numéro d'ordre, son jour
— ne se remplissent que lorsqu'un seul lot alimente la requalification. À
plusieurs, il n'y a pas *une* origine, et en désigner une reviendrait à
choisir laquelle des huit le registre va taire. C'est la colonne provenance
qui les porte alors toutes, en toutes lettres, comme elle porte le renvoi au
registre manuscrit sur une reprise de stock d'ouverture.

Les inscriptions d'origine, elles, se réduisent d'autant — chacune par une
rectification portant son motif, la seule correction que le texte admette
(CGI, ann. IV, art. 56 J sexdecies, 2° c). Le motif est saisi une fois et
vaut pour toutes : elles procèdent du même tri.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.fr_numismatics_metals.tools import metals


class LivrePoliceRequalification(models.TransientModel):
    _name = 'livre.police.requalification'
    _description = "Livre de police - requalifier des parts de lots"

    ligne_ids = fields.One2many(
        'livre.police.requalification.ligne', 'wizard_id',
        string="Lots triés",
    )
    poids_retire_total = fields.Float(
        string="Poids retiré au total (g)", digits=(12, 4), readonly=True,
        compute='_compute_poids_retire_total',
        help="Ce que le tri a ôté aux inscriptions d'origine. Le poids "
             "reclassé ne peut pas le dépasser.",
    )

    product_id = fields.Many2one(
        'product.product', string="Article réel", required=True,
        domain="[('metal_regulated', '=', True)]",
        help="Ce que ces parts sont réellement. C'est de lui que le registre "
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
             "toutes les inscriptions : celles qui se réduisent et celle qui "
             "naît.",
    )

    @api.model
    def default_get(self, champs):
        valeurs = super().default_get(champs)
        inscriptions = self.env['livre.police.ligne'].browse(
            self.env.context.get('active_ids') or [])
        inscriptions = inscriptions.exists().filtered(
            lambda l: l.sens == 'entree' and not l.rectifie_id)
        if not inscriptions:
            raise UserError(_(
                "Cet écran reclasse du métal entré. Sélectionnez des "
                "inscriptions d'entrée qui ne sont pas elles-mêmes des "
                "rectifications — une sortie dit ce qui est parti, et cela "
                "ne se requalifie pas."))
        societes = inscriptions.company_id
        if len(societes) > 1:
            raise UserError(_(
                "Ces inscriptions relèvent de plusieurs établissements "
                "(%(societes)s). Un registre est tenu pour chacun (c. pén., "
                "art. R321-6) : le métal se transfère avant de se trier "
                "ensemble.",
                societes=", ".join(societes.mapped('display_name'))))
        # Rien n'est prélevé par défaut : le tri dit lot par lot ce qu'il a
        # sorti, et une ligne laissée à zéro ne retire rien.
        valeurs['ligne_ids'] = [
            (0, 0, {'inscription_id': inscription.id})
            for inscription in inscriptions.sorted('numero_ordre')]
        return valeurs

    @api.depends('ligne_ids.poids_retire')
    def _compute_poids_retire_total(self):
        for wiz in self:
            wiz.poids_retire_total = sum(wiz.ligne_ids.mapped('poids_retire'))

    @api.depends('quantite', 'product_id')
    def _compute_poids(self):
        for wiz in self:
            modele = wiz.product_id.product_tmpl_id
            wiz.poids = metals.derive_weight(
                modele.metal_quantity_mode, modele.metal_unit_weight,
                wiz.quantite) or 0.0

    @api.onchange('product_id', 'poids_retire_total')
    def _onchange_article_au_gramme(self):
        """Propose le poids retiré comme quantité, quand l'article est au gramme.

        Au gramme, la quantité *est* le poids : la recopier à la main
        n'ajoute qu'une occasion de se tromper d'un chiffre. À la pièce, rien
        ne se devine — le tri a compté des objets, pas des grammes.
        """
        for wiz in self:
            if wiz.product_id.product_tmpl_id.metal_quantity_mode == 'gram':
                wiz.quantite = wiz.poids_retire_total

    def _verifier(self):
        self.ensure_one()
        prelevees = self.ligne_ids.filtered('prelevee')
        if not prelevees:
            raise UserError(_(
                "Aucune quantité n'a été retirée : il n'y a rien à "
                "reclasser."))
        for ligne in prelevees:
            if ligne.quantite_retiree < 0:
                raise UserError(_(
                    "L'inscription %(numero)s porte une quantité retirée "
                    "négative : un tri prélève, il ne remet pas.",
                    numero=ligne.numero_ordre))
            if ligne.quantite_retiree > ligne.quantite_inscrite + 0.00005:
                raise UserError(_(
                    "L'inscription %(numero)s ne porte que %(inscrite)s : on "
                    "ne peut pas en retirer %(retiree)s.",
                    numero=ligne.numero_ordre,
                    inscrite=ligne.quantite_inscrite,
                    retiree=ligne.quantite_retiree))
        if self.quantite <= 0:
            raise UserError(_("La quantité reclassée doit être positive."))
        # Le tri sépare, il ne crée pas de matière. Un poids reclassé
        # supérieur au poids retiré ne décrirait aucune opération réelle.
        if self.poids > self.poids_retire_total + 0.00005:
            raise UserError(_(
                "Le poids reclassé (%(poids).4f g) dépasse le poids retiré "
                "des lots (%(retire).4f g). Un tri sépare, il ne crée pas de "
                "matière : reprenez les quantités.",
                poids=self.poids, retire=self.poids_retire_total))
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
        return prelevees

    def action_requalifier(self):
        """Réduit chaque lot trié, et inscrit la part reclassée qui en sort."""
        self.ensure_one()
        prelevees = self._verifier()
        motif = self.motif.strip()
        Registre = self.env['livre.police.ligne']
        societe = prelevees.inscription_id.company_id

        # 1. Chaque origine se réduit — une inscription ne se réécrit pas, la
        #    correction s'inscrit à la suite avec son motif.
        rectifications = Registre
        parts = []
        for ligne in prelevees:
            source = ligne.inscription_id
            courante = source._rectification_finale()
            mentions = {nom: (courante[nom].id
                              if courante._fields[nom].type == 'many2one'
                              else courante[nom])
                        for nom in self.env[
                            'livre.police.rectification']._MENTIONS}
            mentions.update({
                'quantite': courante.quantite - ligne.quantite_retiree,
                'poids': courante.poids - ligne.poids_retire,
            })
            rectifications |= source._inscrire_rectification(mentions, _(
                "Requalification : %(quantite).4f retirés du lot et reclassés "
                "en « %(article)s ». %(motif)s",
                quantite=ligne.quantite_retiree,
                article=self.product_id.display_name, motif=motif))
            source._ajuster_le_stock(-ligne.quantite_retiree)
            parts.append((source, ligne.quantite_retiree, ligne.poids_retire))

        # 2. Ce qui a été trié naît en un seul lot, sous son propre numéro.
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
            parts, mouvement, self.product_id, self.poids,
            self.description, motif)
        valeurs['numero_ordre'] = numero
        inscription = Registre.sudo().create(valeurs)

        return {
            'type': 'ir.actions.act_window',
            'name': _("Requalification en %s") % self.product_id.display_name,
            'res_model': 'livre.police.ligne',
            'view_mode': 'list,form',
            'domain': [('id', 'in', (rectifications | inscription).ids)],
        }


class LivrePoliceRequalificationLigne(models.TransientModel):
    _name = 'livre.police.requalification.ligne'
    _description = "Livre de police - lot trié"

    wizard_id = fields.Many2one(
        'livre.police.requalification', required=True, ondelete='cascade',
    )
    inscription_id = fields.Many2one(
        'livre.police.ligne', string="Inscription", required=True,
        readonly=True, ondelete='cascade',
    )
    numero_ordre = fields.Char(
        related='inscription_id.numero_ordre', string="N° d'ordre",
        readonly=True,
    )
    designation = fields.Char(
        related='inscription_id.designation', string="Désignation",
        readonly=True,
    )
    date_achat = fields.Date(
        related='inscription_id.date_achat', string="Entré le", readonly=True,
    )
    quantite_inscrite = fields.Float(
        string="Quantité inscrite", digits=(12, 4), readonly=True,
        compute='_compute_etat',
        help="Ce que le registre affirme aujourd'hui de ce lot — la dernière "
             "rectification s'il y en a eu.",
    )
    poids_inscrit = fields.Float(
        string="Poids inscrit (g)", digits=(12, 4), readonly=True,
        compute='_compute_etat',
    )
    quantite_retiree = fields.Float(
        string="Quantité retirée", digits=(12, 4), default=0.0,
        help="Ce que le tri a sorti de ce lot-ci, dans son unité à lui. "
             "Laissée à zéro, la ligne ne retire rien.",
    )
    poids_retire = fields.Float(
        string="Poids retiré (g)", digits=(12, 4), readonly=True,
        compute='_compute_poids_retire',
        help="Déduit à la proportion de l'inscrit, comme pour toute "
             "rectification de quantité.",
    )
    prelevee = fields.Boolean(compute='_compute_poids_retire')

    @api.depends('inscription_id')
    def _compute_etat(self):
        for ligne in self:
            courante = ligne.inscription_id._rectification_finale()
            ligne.quantite_inscrite = courante.quantite
            ligne.poids_inscrit = courante.poids

    @api.depends('quantite_retiree', 'quantite_inscrite', 'poids_inscrit')
    def _compute_poids_retire(self):
        for ligne in self:
            reference = ligne.quantite_inscrite
            ligne.poids_retire = (
                ligne.poids_inscrit * ligne.quantite_retiree / reference
                if reference else 0.0)
            ligne.prelevee = abs(ligne.quantite_retiree) > 0.00005
