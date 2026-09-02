# -*- coding: utf-8 -*-
"""Le métal qui était déjà là quand le registre informatisé s'ouvre.

Les comptoirs ont tenu leur registre à la main jusqu'ici. Le jour où le
registre informatisé prend la suite, le coffre n'est pas vide : il contient du
métal racheté sous l'ancien registre, dont les acquisitions sont consignées
là-bas, page après page.

Ce métal doit entrer quelque part. S'il n'entre pas, il n'existe pas — et sa
revente ne s'inscrira nulle part, faute d'entrée à laquelle la rattacher.
C'est le trou que ce document ferme.

Ce que ce document n'est pas
----------------------------

**Ce n'est pas un achat.** Personne n'a vendu quoi que ce soit à
l'établissement ce jour-là. Les colonnes du vendeur — nom, qualité, domicile,
pièce d'identité — restent donc vides, et le prix est nul. Les remplir avec un
vendeur fictif ferait dire au registre qu'une opération a eu lieu, ce qui
serait faux, et masquerait justement ce qui doit se voir : que ces objets
viennent d'ailleurs.

**C'est un report de stock.** Ce que la colonne « provenance » porte, c'est le
renvoi au registre où l'acquisition est consignée : « Reprise de stock agence —
voir livre de police manuscrit ». Le modèle officiel réserve cette colonne à
« l'indication de sa provenance » (arrêté du 15 mai 2020, annexe I, colonne 3),
et un imprimé doit se lire seul : un contrôleur qui a la page sous les yeux doit
comprendre, sans rien demander, pourquoi ces lignes n'ont pas de vendeur.

Le renvoi vaut dans les deux sens. Le registre manuscrit doit porter, à sa
clôture, la mention inverse — le stock reporté, la date, et les numéros d'ordre
sous lesquels il l'a été. Sans cette mention-là, qui s'écrit à la main et que ce
module ne peut pas produire, la chaîne est coupée d'un côté.

La maille est le lot
--------------------

« Chaque objet exposé à la vente ou détenu en stock est affecté d'un numéro
d'ordre. […] Le numéro d'ordre est porté sur le registre et figure de manière
apparente sur chaque objet ou lot d'objets » (c. pén., art. R321-4).

Le même article admet donc expressément le lot, et c'est ce qui rend la reprise
praticable : le stock d'ouverture n'est pas détaillé objet par objet — il est
pesé par nature et par titre, « argent », « or titres divers », « 18k ». Chaque
ligne de reprise est un lot, reçoit un numéro d'ordre, et ce numéro doit figurer
sur le contenant dès la reprise faite.

Un lot unique se vide ensuite par vente successives, et le registre le suit :
chaque départ s'inscrit sous son propre numéro, l'entrée reste « sortie en
partie » tant qu'il reste du métal, et le numéro doit demeurer apparent sur ce
qui reste.

Une reprise par établissement
-----------------------------

« Lorsque les personnes mentionnées à l'article R. 321-1 possèdent plusieurs
établissements ouverts au public, un registre est tenu pour chaque
établissement » (c. pén., art. R321-6). Trois coffres, trois reprises, trois
suites de numéros d'ordre. Un document ne reprend jamais le stock d'un autre
comptoir.

Le stock et le registre naissent ensemble
-----------------------------------------

Le document fait les trois choses d'un seul geste : il inscrit au registre,
crée le lot au numéro d'ordre inscrit, et pose la quantité en stock par
ajustement d'inventaire. C'est ce qui les empêche de diverger — un ajustement
d'inventaire fait à part remplirait le stock sans rien inscrire, et les reventes
de ce métal ne s'inscriraient nulle part, silencieusement.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from odoo.addons.fr_numismatics_metals.tools import metals


class LivrePoliceReprise(models.Model):
    _name = 'livre.police.reprise'
    _description = "Livre de police - reprise de stock d'ouverture"
    _order = 'id desc'

    name = fields.Char(
        string="Référence", required=True, readonly=True, copy=False,
        default='/', index=True,
    )
    company_id = fields.Many2one(
        'res.company', string="Établissement", required=True,
        default=lambda self: self.env.company, index=True,
        help="Le comptoir dont on reprend le coffre. C'est son registre qui "
             "portera les inscriptions, dans sa propre suite de numéros "
             "d'ordre (c. pén., art. R321-6).",
    )
    date_arrete = fields.Date(
        string="Date de l'arrêté", required=True,
        default=fields.Date.context_today,
        help="Le jour où le stock a été arrêté et pesé. C'est la date que "
             "les inscriptions porteront.\n\n"
             "Elle doit être celle d'un coffre réellement compté : un état "
             "vieilli d'une semaine ne décrit plus le stock, et la reprise "
             "inscrirait du métal déjà vendu.",
    )
    libelle = fields.Text(
        string="Libellé de la reprise", required=True,
        default="Reprise de stock agence - voir livre de police manuscrit",
        help="Ce que la colonne « provenance » portera, sur chaque "
             "inscription. C'est la seule chose qui explique, à la lecture de "
             "l'imprimé, pourquoi ces lignes n'ont pas de vendeur — et où "
             "l'acquisition est consignée.",
    )
    registre_papier = fields.Char(
        string="Renvoi au registre manuscrit",
        help="Le registre repris : sa désignation, son ouverture, la page où "
             "il se clôt. Recopié sur les inscriptions qui ne portent pas "
             "leur propre renvoi.\n\n"
             "Le registre manuscrit doit porter la mention inverse à sa "
             "clôture — stock reporté le tant, sous les numéros d'ordre tant "
             "à tant. Elle s'écrit à la main ; ce module ne peut pas la "
             "produire.",
    )
    ligne_ids = fields.One2many(
        'livre.police.reprise.ligne', 'reprise_id', string="Lots repris",
    )
    state = fields.Selection(
        [('brouillon', "Brouillon"),
         ('inscrit', "Inscrit")],
        string="État", default='brouillon', required=True, readonly=True,
        index=True,
    )
    inscription_ids = fields.One2many(
        'livre.police.ligne', 'reprise_id', string="Inscriptions",
        readonly=True,
    )
    poids_total = fields.Float(
        string="Poids total (g)", digits=(12, 4), compute='_compute_poids_total',
    )
    date_inscription = fields.Datetime(string="Inscrit le", readonly=True)
    inscrit_par_id = fields.Many2one(
        'res.users', string="Inscrit par", readonly=True,
    )

    @api.depends('ligne_ids.poids')
    def _compute_poids_total(self):
        for reprise in self:
            reprise.poids_total = sum(reprise.ligne_ids.mapped('poids'))

    @api.model_create_multi
    def create(self, valeurs_liste):
        for valeurs in valeurs_liste:
            if valeurs.get('name', '/') == '/':
                societe = self.env['res.company'].browse(
                    valeurs.get('company_id')) or self.env.company
                valeurs['name'] = self._sequence(societe).next_by_id()
        return super().create(valeurs_liste)

    @api.model
    def _sequence(self, societe):
        """Suite des références de reprise, propre à chaque établissement."""
        Sequence = self.env['ir.sequence'].sudo()
        suite = Sequence.search([('code', '=', 'livre.police.reprise'),
                                 ('company_id', '=', societe.id)], limit=1)
        if not suite:
            suite = Sequence.create({
                'name': "Livre de police, reprises - %s" % societe.name,
                'code': 'livre.police.reprise',
                'company_id': societe.id,
                'prefix': 'REP/',
                'implementation': 'standard',
                'padding': 5,
                'number_next': 1,
            })
        return suite

    def unlink(self):
        """Un brouillon se jette ; une reprise inscrite, non."""
        inscrites = self.filtered(lambda r: r.state != 'brouillon')
        if inscrites:
            raise UserError(_(
                "La reprise %(references)s a inscrit au registre, et une "
                "inscription ne se retire pas (c. pén., art. R321-6-1).\n\n"
                "Si elle est fautive, rectifiez les inscriptions une à une "
                "depuis le registre, avec leur motif.",
                references=", ".join(inscrites.mapped('name'))))
        return super().unlink()

    def _entrepot(self):
        self.ensure_one()
        entrepot = self.env['stock.warehouse'].sudo().search(
            [('company_id', '=', self.company_id.id)], limit=1)
        if not entrepot:
            raise UserError(_(
                "L'établissement %(societe)s n'a pas d'entrepôt : le métal "
                "repris n'a nulle part où entrer.",
                societe=self.company_id.display_name))
        return entrepot

    # ------------------------------------------------------------------
    # Inscrire
    # ------------------------------------------------------------------

    def action_inscrire(self):
        """Inscrit le coffre au registre et le pose en stock, ligne par ligne.

        L'ordre est imposé et il compte : le numéro d'ordre d'abord, le lot
        ensuite — qui en prend le nom —, le stock enfin. Un lot nommé avant
        que l'inscription n'existe porterait un numéro que le registre ne
        connaît pas, et l'étiquette du coffre mentirait.
        """
        self.ensure_one()
        if self.state != 'brouillon':
            raise UserError(_(
                "La reprise %(reference)s est déjà inscrite au registre de "
                "%(societe)s. Une inscription ne se refait pas.",
                reference=self.name, societe=self.company_id.display_name))
        if not self.ligne_ids:
            raise UserError(_(
                "Aucun lot à reprendre. Une reprise sans lot n'inscrirait "
                "rien."))
        self.ligne_ids._verifier()

        reprise = self.with_company(self.company_id)
        emplacement = reprise._entrepot().lot_stock_id
        Registre = self.env['livre.police.ligne']
        Lot = self.env['stock.lot'].sudo()
        Quant = self.env['stock.quant'].sudo()

        for ligne in reprise.ligne_ids:
            numero = Registre._sequence(reprise.company_id).next_by_id()
            lot = Lot.with_company(reprise.company_id).create({
                'name': numero,
                'product_id': ligne.product_id.id,
                'company_id': reprise.company_id.id,
            })
            # L'ajustement d'inventaire est le chemin d'Odoo pour du stock qui
            # apparait sans venir de nulle part — ce qui est exactement le cas
            # ici : ce metal n'a ete achete par aucun document de cette base.
            quant = Quant.with_company(reprise.company_id).with_context(
                inventory_mode=True).create({
                    'product_id': ligne.product_id.id,
                    'location_id': emplacement.id,
                    'lot_id': lot.id,
                    'inventory_quantity': ligne.quantite,
                })
            quant.action_apply_inventory()
            mouvement = self.env['stock.move.line'].sudo().search(
                [('lot_id', '=', lot.id), ('state', '=', 'done')],
                order='id desc', limit=1)

            valeurs = Registre._valeurs_depuis_reprise(ligne, mouvement)
            valeurs['numero_ordre'] = numero
            valeurs['numero_lot'] = numero
            inscription = Registre.sudo().create(valeurs)
            ligne.write({'inscription_id': inscription.id, 'lot_id': lot.id})

        reprise.write({
            'state': 'inscrit',
            'date_inscription': fields.Datetime.now(),
            'inscrit_par_id': self.env.user.id,
        })
        return True

    def action_voir_inscriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Inscriptions de la reprise %s" % self.name,
            'res_model': 'livre.police.ligne',
            'view_mode': 'list,form',
            'domain': [('reprise_id', '=', self.id)],
        }


class LivrePoliceRepriseLigne(models.Model):
    _name = 'livre.police.reprise.ligne'
    _description = "Livre de police - lot d'une reprise de stock"
    _order = 'reprise_id, id'

    reprise_id = fields.Many2one(
        'livre.police.reprise', string="Reprise", required=True,
        ondelete='cascade', index=True,
    )
    company_id = fields.Many2one(
        related='reprise_id.company_id', string="Établissement",
    )
    product_id = fields.Many2one(
        'product.product', string="Article", required=True,
        domain="[('metal_regulated', '=', True)]",
        help="L'article dit la nature du métal, son titre et le régime de la "
             "quantité — au gramme ou à la pièce. Ces trois mentions sont "
             "celles du registre des métaux précieux (CGI, ann. IV, art. 56 J "
             "quindecies) : elles se lisent sur l'article, elles ne se "
             "saisissent pas ici.",
    )
    quantite = fields.Float(
        string="Quantité", digits=(12, 4), required=True, default=0.0,
        help="Ce que le coffre contient, dans l'unité de l'article : des "
             "grammes sur un article au gramme, des pièces sur un article à "
             "l'unité.",
    )
    poids = fields.Float(
        string="Poids (g)", digits=(12, 4), compute='_compute_poids',
        store=True,
        help="Déduit de l'article et de la quantité, jamais saisi : au "
             "gramme la quantité est le poids, à la pièce elle se multiplie "
             "par le poids unitaire du type.",
    )
    description = fields.Text(
        string="Description des objets",
        help="Ce que le contenant renferme, décrit comme le registre le "
             "demande (arrêté du 15 mai 2020, annexe I, colonne 3). Exigée là "
             "où la désignation de l'article ne décrit aucun objet — l'or au "
             "gramme, l'argent en vrac — et là où l'objet porte une "
             "identification propre, comme le numéro unique d'un lingot.\n\n"
             "Une reprise d'ouverture est l'exception : ce détail est "
             "précisément ce que l'agrégation du stock a perdu, et il reste "
             "consigné au registre manuscrit. « Voir livre de police "
             "manuscrit » y est donc une description recevable — elle dit où "
             "le détail se trouve, ce qu'une phrase inventée ne ferait pas.",
    )
    registre_papier = fields.Char(
        string="Renvoi au registre manuscrit",
        help="La page, le numéro ou la cote sous laquelle ce lot figure au "
             "registre manuscrit, lorsqu'il est connu. À défaut, celui du "
             "document s'applique.",
    )
    metal_nature = fields.Char(
        string="Nature", compute='_compute_mentions',
    )
    titre_texte = fields.Char(
        string="Titre", compute='_compute_mentions',
    )
    inscription_id = fields.Many2one(
        'livre.police.ligne', string="Inscription", readonly=True,
        ondelete='restrict', index='btree_not_null',
    )
    numero_ordre = fields.Char(
        related='inscription_id.numero_ordre', string="N° d'ordre",
        readonly=True,
    )
    lot_id = fields.Many2one(
        'stock.lot', string="Lot", readonly=True, ondelete='restrict',
        help="Le lot créé au numéro d'ordre. C'est ce numéro qui doit "
             "figurer sur le contenant (c. pén., art. R321-4).",
    )

    @api.depends('product_id', 'quantite')
    def _compute_poids(self):
        for ligne in self:
            modele = ligne.product_id.product_tmpl_id
            ligne.poids = metals.derive_weight(
                modele.metal_quantity_mode, modele.metal_unit_weight,
                ligne.quantite) or 0.0

    @api.depends('product_id')
    def _compute_mentions(self):
        """Ce que l'article dit du métal, montré avant d'inscrire.

        Le registre le lira sur l'article de toute façon ; l'afficher ici
        laisse voir une erreur de choix avant qu'elle ne soit inscrite, et une
        inscription ne se corrige que par une autre.
        """
        for ligne in self:
            modele = ligne.product_id.product_tmpl_id
            ligne.metal_nature = modele.metal_nature.display_name or False
            if modele.metal_fineness:
                ligne.titre_texte = "%g" % modele.metal_fineness
            elif modele.metal_mixed_fineness:
                ligne.titre_texte = "lot de titres"
            else:
                ligne.titre_texte = False

    @api.constrains('quantite')
    def _check_quantite(self):
        for ligne in self:
            if ligne.quantite <= 0:
                raise ValidationError(_(
                    "La quantité reprise doit être positive. Une ligne à "
                    "zéro n'inscrirait rien et ferait exister un numéro "
                    "d'ordre sans objet."))

    def _verifier(self):
        """Ce qui doit être vrai de chaque ligne avant d'inscrire."""
        for ligne in self:
            modele = ligne.product_id.product_tmpl_id
            if not modele.metal_regulated:
                raise UserError(_(
                    "L'article « %(article)s » n'est pas soumis au livre de "
                    "police. Le registre n'a pas à le connaître, et le "
                    "reprendre ici lui donnerait un numéro d'ordre qui ne "
                    "désigne rien.",
                    article=ligne.product_id.display_name))
            if not ligne.product_id.active or not modele.active:
                raise UserError(_(
                    "L'article « %(article)s » est archivé.\n\n"
                    "Du stock repris sur un article archivé serait bloqué : "
                    "aucun devis ne peut plus le désigner, donc ce métal ne "
                    "pourrait plus ressortir par la vente — et son "
                    "inscription resterait ouverte au registre sans que rien "
                    "ne puisse la solder.\n\n"
                    "Reprenez ce métal sur l'article qui a pris la suite, ou "
                    "désarchivez celui-ci s'il est encore le bon.",
                    article=ligne.product_id.display_name))
            if not modele.is_storable or modele.tracking == 'none':
                raise UserError(_(
                    "L'article « %(article)s » n'est pas suivi par lot, ou "
                    "n'est pas stockable.\n\n"
                    "Un lot repris doit porter un numéro d'ordre « de manière "
                    "apparente » (c. pén., art. R321-4), et ce numéro est le "
                    "nom du lot. Sans suivi par lot, le métal entrerait en "
                    "stock sans numéro, et sa revente ne se rattacherait à "
                    "aucune entrée.\n\n"
                    "Corrigez la fiche de l'article — « Suivi » sur « Par "
                    "lot », et l'article stockable — puis reprenez.",
                    article=ligne.product_id.display_name))
            if modele.police_description_required and not (
                    ligne.description or '').strip():
                raise UserError(_(
                    "L'article « %(article)s » ne décrit aucun objet : la "
                    "description est due.\n\n"
                    "Le modèle officiel réclame en colonne 3 une "
                    "« description précise de l'objet » (arrêté du 15 mai "
                    "2020, annexe I). Sur un lot d'ouverture, elle dit ce que "
                    "le contenant renferme — « débris et bijoux cassés, "
                    "titres mêlés ».",
                    article=ligne.product_id.display_name))
