# -*- coding: utf-8 -*-
"""Le métal qui change d'établissement, et ce qui le justifie.

« Lorsque les personnes mentionnées à l'article R. 321-1 possèdent plusieurs
établissements ouverts au public, un registre est tenu pour chaque
établissement » (c. pén., art. R321-6). Trois comptoirs, trois registres, trois
suites de numéros d'ordre — le module tenait déjà cela.

Restait le mouvement entre eux. Un sachet part de Metz pour être vendu depuis
Nancy : côté stock, deux bons ; côté registre, rien. La sortie de Metz
s'inscrivait comme une sortie ordinaire, muette sur sa destination, et Nancy
n'inscrivait aucune entrée — le métal disparaissait d'un registre sans
apparaître dans l'autre, et sa revente ultérieure ne s'inscrivait nulle part,
faute d'entrée à laquelle la rattacher.

Ce document tient les deux bouts. Il nomme l'établissement d'arrivée, porte le
**motif** du déplacement, et c'est lui qui crée les deux bons de stock, les
enchaîne et les valide. L'appariement n'est donc pas deviné après coup : il
existe avant que le métal ne bouge.

Le passage se fait par l'emplacement de transit inter-sociétés d'Odoo, qui
n'appartient à aucune société. C'est le seul chemin possible — un emplacement
de stock appartient à un établissement, et aucun mouvement ne va directement
de l'un à l'autre. Entre les deux validations, le métal est en transit : sorti
du registre de Metz, pas encore inscrit à celui de Nancy. Ce n'est pas un trou,
c'est l'état réel de la marchandise, et les deux inscriptions le disent.

Le lot ne change pas de nom au passage
--------------------------------------

Le sachet n'est pas réétiqueté. Il porte le numéro d'ordre que le comptoir de
rachat lui a donné, et il le portera jusqu'à la fonte.

Odoo, lui, exige que le nom d'un lot soit unique pour un article dans une
société — et chaque agence repart de 000001. Le « 000123 » de Metz et celui de
Nancy sont deux lots différents du même article : nommer les deux « 000123 »
serait refusé.

Le lot transféré est donc **qualifié et détaché** au départ : il devient
« METZ/000123 » et cesse d'appartenir à une société. Le numéro du comptoir de
rachat est intact, une recherche sur « 000123 » le retrouve toujours, et
l'établissement qui l'a inscrit est désormais lisible sur le lot lui-même.
Surtout, c'est le **même enregistrement de lot** qui traverse : rien n'est
recréé à l'arrivée, la traçabilité du stock n'est pas coupée, et la quantité
sort d'un côté exactement comme elle entre de l'autre.

Un lot détaché est visible des trois établissements — c'est le prix du
partage, et il ne concerne que les lots réellement partis. Ce qu'il ne montre
pas, c'est le vendeur : `stock_lot.py` refuse de nommer l'avoir d'achat à qui
ne tient pas le registre où il est inscrit.

Ce que l'arrivée inscrit, et ce qu'elle n'inscrit pas
----------------------------------------------------

L'entrée à Nancy prend son propre numéro d'ordre, dans la suite de Nancy. Elle
recopie ce qui décrit la marchandise — la nature, le titre, le poids, les
objets — et **rien de la personne** qui a vendu à Metz. Son nom, son domicile
et sa pièce d'identité restent au registre de Metz : « le registre d'un
établissement n'a pas à montrer les clients d'un autre », et c'est déjà la
règle d'accès du module.

Ce que Nancy inscrit à la place, c'est l'**origine** : l'établissement, le
numéro d'ordre et la date du rachat, figés à l'inscription. La chaîne remonte
donc jusqu'au comptoir qui a acheté, transfert après transfert, et la vente
finale — à un fondeur, par exemple — s'inscrit à Nancy en désignant toujours
Metz comme origine.

Le prix est nul, et ce n'est pas un oubli. Un transfert entre établissements
d'un même titulaire ne paie personne : le prix d'achat vit à l'inscription
d'origine, que la colonne « Origine » désigne nommément. Y recopier un montant
laisserait croire qu'une seconde opération a eu lieu.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class LivrePoliceTransfert(models.Model):
    _name = 'livre.police.transfert'
    _description = "Livre de police - transfert entre etablissements"
    _order = 'id desc'

    name = fields.Char(
        string="Référence", required=True, readonly=True, copy=False,
        default='/', index=True,
    )
    company_id = fields.Many2one(
        'res.company', string="Établissement de départ", required=True,
        default=lambda self: self.env.company, index=True,
        help="L'établissement dont le métal sort. C'est son registre qui "
             "portera l'inscription de sortie.",
    )
    company_destination_id = fields.Many2one(
        'res.company', string="Établissement d'arrivée", required=True,
        index=True,
        help="L'établissement qui reçoit. C'est son registre qui portera "
             "l'inscription d'entrée, sous son propre numéro d'ordre.",
    )
    motif = fields.Text(
        string="Motif du transfert", required=True,
        help="Pourquoi ce métal change d'établissement — regroupement avant "
             "fonte, réassort du comptoir, commande d'un client d'une autre "
             "agence. Le motif est recopié sur les deux inscriptions, celle "
             "de la sortie et celle de l'entrée, et entre dans le chiffre de "
             "contrôle des pages.",
    )
    ligne_ids = fields.One2many(
        'livre.police.transfert.ligne', 'transfert_id', string="Lots à transférer",
    )
    state = fields.Selection(
        [('brouillon', "Brouillon"),
         ('expedie', "Expédié"),
         ('recu', "Reçu"),
         ('annule', "Annulé")],
        string="État", default='brouillon', required=True, readonly=True,
        index=True,
    )

    picking_sortie_id = fields.Many2one(
        'stock.picking', string="Bon de sortie", readonly=True,
        ondelete='restrict',
    )
    picking_entree_id = fields.Many2one(
        'stock.picking', string="Bon d'entrée", readonly=True,
        ondelete='restrict',
    )
    inscription_ids = fields.One2many(
        'livre.police.ligne', 'transfert_id', string="Inscriptions", readonly=True,
        help="Les deux faces du transfert au registre : la sortie chez celui "
             "qui expédie, l'entrée chez celui qui reçoit. Chacun ne voit que "
             "la sienne.",
    )

    date_expedition = fields.Datetime(string="Expédié le", readonly=True)
    expedie_par_id = fields.Many2one('res.users', string="Expédié par", readonly=True)
    date_reception = fields.Datetime(string="Reçu le", readonly=True)
    recu_par_id = fields.Many2one('res.users', string="Reçu par", readonly=True)

    poids_total = fields.Float(
        string="Poids total (g)", digits=(12, 4), compute='_compute_poids_total',
    )
    inscription_domaine = fields.Char(
        compute='_compute_inscription_domaine',
        help="Les numéros d'ordre que l'agence de départ a réellement sous la "
             "main, calculés sur le stock et non sur le registre.",
    )

    _sql_constraints = [
        ('name_unique', 'unique(company_id, name)',
         "Deux transferts ne peuvent pas porter la même référence dans le "
         "même établissement."),
    ]

    @api.depends('company_id')
    def _compute_inscription_domaine(self):
        """Ce qu'on peut choisir, c'est ce que l'agence détient vraiment.

        La tentation était de filtrer sur l'état de sortie du registre —
        « en stock », « sorti en partie ». Mais cet état-là dit ce que le
        *registre* sait : rien n'est sorti de cette inscription. Il ne dit
        pas qu'un lot existe. Un rachat inscrit dont la réception n'a pas
        été validée se lit « en stock » alors qu'aucun métal n'est encore
        entré au coffre, et il s'offrait au transfert.

        Le stock, lui, répond à la bonne question. Il se lit ici, une fois,
        et le résultat prend la forme d'une liste de numéros : le refus
        n'arrive plus à l'expédition, il n'y a simplement rien à choisir.
        """
        for transfert in self:
            disponibles = transfert._stock_par_inscription()
            transfert.inscription_domaine = str(
                [('id', 'in', [ligne.id for ligne in disponibles])])

    def _stock_par_inscription(self):
        """Ce que l'agence de départ a en main, numéro d'ordre par numéro.

        Rend, pour chaque inscription qui a encore du métal au coffre, le lot
        qui le porte et la quantité libre. C'est la source unique du domaine
        de sélection et du bouton qui reprend tout le stock : les deux
        répondent à la même question, et une seule réponse évite qu'ils
        divergent.
        """
        self.ensure_one()
        if not self.company_id:
            return {}
        Registre = self.env['livre.police.ligne'].sudo()
        candidates = Registre.search([
            ('sens', '=', 'entree'), ('company_id', '=', self.company_id.id),
        ]).filtered(lambda l: l.etat_sortie in ('en_stock', 'partiel'))
        if not candidates:
            return {}

        # Un nom de lot désigne une inscription et une seule : la suite des
        # numéros d'ordre est unique dans l'établissement.
        par_nom = {}
        for ligne in candidates:
            for nom in ligne._noms_de_lot():
                par_nom.setdefault(nom, ligne)
        lots = self.env['stock.lot'].sudo().search([
            ('name', 'in', list(par_nom)),
            ('company_id', 'in', [self.company_id.id, False]),
        ])
        if not lots:
            return {}
        groupes = self.env['stock.quant'].sudo()._read_group(
            [('lot_id', 'in', lots.ids),
             ('location_id.usage', '=', 'internal'),
             ('company_id', '=', self.company_id.id)],
            ['lot_id'], ['quantity:sum', 'reserved_quantity:sum'])
        libre = {lot: total - reserve for lot, total, reserve in groupes}

        resultat = {}
        for lot in lots:
            quantite = libre.get(lot, 0.0)
            ligne = par_nom.get(lot.name)
            if ligne and quantite > 0.00005:
                resultat[ligne] = (lot, quantite)
        return resultat

    def action_ajouter_tout_le_stock(self):
        """Reprend d'un coup tout ce que l'agence de départ détient.

        Un regroupement avant fonte vide le coffre : les désigner un à un
        serait long et, surtout, en oublier un ne se verrait pas. Ce qui est
        déjà sur le transfert n'est pas repris deux fois.
        """
        self.ensure_one()
        if self.state != 'brouillon':
            raise UserError(_(
                "Ce transfert est déjà parti : ses lots ne se complètent "
                "plus. Établissez-en un second."))
        deja = self.ligne_ids.inscription_id
        ajouts = [
            (0, 0, {'inscription_id': ligne.id, 'quantite': quantite})
            for ligne, (_lot, quantite) in sorted(
                self._stock_par_inscription().items(),
                key=lambda paire: paire[0].numero_ordre)
            if ligne not in deja
        ]
        if not ajouts:
            raise UserError(_(
                "L'agence de %(societe)s n'a plus de métal au coffre qui ne "
                "soit déjà sur ce transfert.",
                societe=self.company_id.display_name))
        self.ligne_ids = ajouts
        return True

    @api.depends('ligne_ids.poids')
    def _compute_poids_total(self):
        for transfert in self:
            transfert.poids_total = sum(transfert.ligne_ids.mapped('poids'))

    @api.constrains('company_id', 'company_destination_id')
    def _check_etablissements_distincts(self):
        for transfert in self:
            if transfert.company_id == transfert.company_destination_id:
                raise ValidationError(_(
                    "Un transfert va d'un établissement à un autre. Choisissez "
                    "une agence d'arrivée différente de celle de départ ; un "
                    "déplacement à l'intérieur d'un même établissement ne "
                    "s'inscrit pas au registre, qui consigne les entrées et "
                    "les sorties, pas les rangements."))

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
        """Suite des références de transfert, propre à chaque établissement."""
        Sequence = self.env['ir.sequence'].sudo()
        suite = Sequence.search([('code', '=', 'livre.police.transfert'),
                                 ('company_id', '=', societe.id)], limit=1)
        if not suite:
            suite = Sequence.create({
                'name': "Livre de police, transferts - %s" % societe.name,
                'code': 'livre.police.transfert',
                'company_id': societe.id,
                'prefix': 'TRF/',
                'implementation': 'standard',
                'padding': 5,
                'number_next': 1,
            })
        return suite

    # ------------------------------------------------------------------
    # Les deux établissements, et le droit d'agir sur les deux
    # ------------------------------------------------------------------

    def _societes(self):
        self.ensure_one()
        return self.company_id | self.company_destination_id

    def _deux_etablissements(self):
        """Le même enregistrement, vu des deux établissements à la fois.

        Le mouvement touche deux registres et deux stocks. Sans cela, Odoo
        n'appliquerait que les règles de l'établissement actif, et la
        réservation du lot en transit échouerait sans dire pourquoi.

        Le droit se vérifie sur l'utilisateur, jamais sur son sélecteur de
        société : déplacer du métal d'un comptoir à l'autre suppose d'en
        répondre aux deux, et c'est une décision d'habilitation, pas un
        réglage d'écran.
        """
        self.ensure_one()
        societes = self._societes()
        manquantes = societes - self.env.user.company_ids
        if manquantes:
            raise UserError(_(
                "Vous n'avez pas accès à l'établissement %(societes)s.\n\n"
                "Un transfert sort du registre d'un comptoir et entre dans "
                "celui d'un autre : il ne se fait que par quelqu'un qui "
                "répond des deux. Demandez l'accès à cet établissement, ou "
                "faites établir le transfert par quelqu'un qui l'a.",
                societes=", ".join(manquantes.mapped('display_name'))))
        return self.with_context(allowed_company_ids=societes.ids)

    def _entrepot(self, societe):
        entrepot = self.env['stock.warehouse'].sudo().search(
            [('company_id', '=', societe.id)], limit=1)
        if not entrepot:
            raise UserError(_(
                "L'établissement %(societe)s n'a pas d'entrepôt : le métal "
                "n'a nulle part d'où partir ni où arriver.",
                societe=societe.display_name))
        return entrepot

    def _transit(self):
        """L'emplacement de transit inter-sociétés, seul passage possible.

        Un emplacement de stock appartient à une société ; aucun mouvement ne
        va donc directement du stock de Metz à celui de Nancy. Odoo réserve
        pour cela un emplacement qui n'appartient à personne, et le livre
        archivé tant qu'on ne s'en sert pas.
        """
        transit = self.env.ref('stock.stock_location_inter_company',
                               raise_if_not_found=False)
        if not transit or not transit.sudo().active:
            raise UserError(_(
                "L'emplacement « Inter-company transit » n'est pas actif.\n\n"
                "C'est par lui que le métal passe d'un établissement à "
                "l'autre : les emplacements de stock appartiennent chacun à "
                "une société, et rien ne relie directement deux entrepôts. "
                "Activez-le dans Inventaire > Configuration > Emplacements, "
                "puis reprenez ce transfert."))
        return transit

    # ------------------------------------------------------------------
    # Expédier
    # ------------------------------------------------------------------

    def action_expedier(self):
        """Sort le métal du registre de départ, et le met en route."""
        self.ensure_one()
        if self.state != 'brouillon':
            raise UserError(_(
                "Ce transfert a déjà été expédié : la sortie est inscrite au "
                "registre de %(societe)s et ne se refait pas.",
                societe=self.company_id.display_name))
        if not self.ligne_ids:
            raise UserError(_(
                "Aucun lot à transférer. Un transfert sans lot n'inscrirait "
                "rien nulle part."))
        self.ligne_ids._verifier()

        transfert = self._deux_etablissements()
        transfert.ligne_ids._qualifier_les_lots()
        sortie, entree = transfert._creer_les_bons()
        transfert._valider(sortie)
        transfert.write({
            'picking_sortie_id': sortie.id,
            'picking_entree_id': entree.id,
            'state': 'expedie',
            'date_expedition': fields.Datetime.now(),
            'expedie_par_id': self.env.user.id,
        })
        return True

    def _creer_les_bons(self):
        """Deux bons enchaînés : le départ vers le transit, l'arrivée depuis lui.

        Ils naissent ensemble, avant que rien ne bouge. C'est ce qui rend
        l'appariement certain : l'arrivée existe déjà, en attente, quand la
        sortie s'inscrit — personne n'a à se souvenir de la créer.
        """
        self.ensure_one()
        transit = self._transit()
        depart = self._entrepot(self.company_id)
        arrivee = self._entrepot(self.company_destination_id)

        Picking = self.env['stock.picking'].sudo()
        sortie = Picking.create({
            'picking_type_id': depart.out_type_id.id,
            'location_id': depart.lot_stock_id.id,
            'location_dest_id': transit.id,
            'company_id': self.company_id.id,
            'origin': self.name,
            'police_transfert_id': self.id,
            'move_ids': [(0, 0, valeurs) for valeurs in self._valeurs_mouvements(
                depart.out_type_id, depart.lot_stock_id, transit,
                self.company_id)],
        })
        entree = Picking.create({
            'picking_type_id': arrivee.in_type_id.id,
            'location_id': transit.id,
            'location_dest_id': arrivee.lot_stock_id.id,
            'company_id': self.company_destination_id.id,
            'origin': self.name,
            'police_transfert_id': self.id,
            'move_ids': [(0, 0, valeurs) for valeurs in self._valeurs_mouvements(
                arrivee.in_type_id, transit, arrivee.lot_stock_id,
                self.company_destination_id)],
        })
        # Chaque arrivée attend son départ. Odoo lui passe la main à la
        # validation de la sortie, avec les lots qu'elle a réellement
        # emportés : c'est ce chaînage qui interdit à l'arrivée d'en porter
        # d'autres.
        departs = {mouvement.product_id: mouvement
                   for mouvement in sortie.move_ids}
        for mouvement_entree in entree.move_ids:
            mouvement_entree.write({
                'procure_method': 'make_to_order',
                'move_orig_ids': [
                    (6, 0, departs[mouvement_entree.product_id].ids)],
            })
        sortie.action_confirm()
        entree.action_confirm()
        return sortie, entree

    def _valeurs_mouvements(self, type_operation, source, destination, societe):
        """Un mouvement par article, et non par lot.

        Le lot n'est pas une caractéristique du mouvement : c'est ce que porte
        la ligne de mouvement. Un mouvement par lot le faisait croire, et
        Odoo tranchait à sa façon — il fusionne à la confirmation les
        mouvements que rien ne distingue, et deux sachets d'or 18k au gramme,
        partant du même endroit vers le même endroit sur le même bon, ne se
        distinguent par rien. Le second disparaissait dans le premier, dont
        la quantité s'écrivait alors sur les deux lignes : le registre
        inscrivait deux fois le poids du plus gros, et faisait sortir du
        métal qui n'existait pas.
        """
        valeurs = []
        for produit, lignes in self.ligne_ids.grouped('product_id').items():
            valeurs.append({
                'name': ", ".join(
                    lignes.mapped('inscription_id.numero_ordre')),
                'product_id': produit.id,
                'product_uom': produit.uom_id.id,
                'product_uom_qty': sum(lignes.mapped('quantite')),
                'location_id': source.id,
                'location_dest_id': destination.id,
                'picking_type_id': type_operation.id,
                'company_id': societe.id,
            })
        return valeurs

    def _valider(self, bon):
        """Valide un bon dont les quantités sont déjà celles voulues.

        On désigne les lots à la main plutôt que de laisser Odoo réserver : le
        registre ne transfère pas « 20 g d'or 18k », il transfère le lot
        000123 et lui seul. Sans reliquat possible, la validation ne pose
        aucune question.
        """
        self.ensure_one()
        Ligne = self.env['stock.move.line'].sudo()
        par_produit = {mouvement.product_id: mouvement
                       for mouvement in bon.move_ids}
        for ligne in self.ligne_ids:
            mouvement = par_produit[ligne.product_id]
            existante = mouvement.move_line_ids.filtered(
                lambda ml: ml.lot_id == ligne.lot_id)[:1]
            if existante:
                existante.write({'quantity': ligne.quantite, 'picked': True})
                continue
            Ligne.create({
                'move_id': mouvement.id,
                'picking_id': bon.id,
                'product_id': mouvement.product_id.id,
                'product_uom_id': mouvement.product_uom.id,
                'location_id': mouvement.location_id.id,
                'location_dest_id': mouvement.location_dest_id.id,
                'lot_id': ligne.lot_id.id,
                'quantity': ligne.quantite,
                'picked': True,
            })
        # Odoo réserve de lui-même à la confirmation, et prend les lots qui
        # lui tombent sous la main. Le transfert, lui, désigne les siens : ce
        # qu'il n'a pas nommé ne part pas.
        intrus = bon.move_ids.move_line_ids.filtered(
            lambda ml: ml.lot_id not in self.ligne_ids.lot_id)
        if intrus:
            intrus.unlink()
        bon.move_ids.picked = True
        bon.with_context(skip_backorder=True,
                         picking_ids_not_to_backorder=bon.ids).button_validate()

    # ------------------------------------------------------------------
    # Réceptionner
    # ------------------------------------------------------------------

    def action_receptionner(self):
        """Fait entrer le métal au registre de l'établissement d'arrivée."""
        self.ensure_one()
        if self.state != 'expedie':
            raise UserError(_(
                "Seul un transfert expédié se réceptionne. Celui-ci est "
                "« %(etat)s ».",
                etat=dict(self._fields['state'].selection)[self.state]))
        transfert = self._deux_etablissements()
        transfert._valider(transfert.picking_entree_id)
        return True

    def _marquer_recu(self, bons):
        """Constate l'arrivée, d'où qu'elle vienne.

        Le bouton de ce document n'est pas le seul chemin : l'agence
        d'arrivée peut valider son bon depuis l'inventaire, comme n'importe
        quelle réception, et c'est même ce qu'elle fera le jour où le métal
        arrive sans que personne ne rouvre le transfert. L'entrée s'inscrit
        alors de toute façon — `_action_done` s'en charge — mais le document
        resterait « expédié » et donnerait à croire que du métal est encore
        en route.
        """
        for transfert in self:
            if (transfert.state == 'expedie'
                    and transfert.picking_entree_id in bons
                    and transfert.picking_entree_id.state == 'done'):
                transfert.sudo().write({
                    'state': 'recu',
                    'date_reception': fields.Datetime.now(),
                    'recu_par_id': self.env.user.id,
                })

    def action_annuler(self):
        """Un transfert ne s'annule que tant qu'il n'a rien inscrit."""
        self.ensure_one()
        if self.state != 'brouillon':
            raise UserError(_(
                "Ce transfert a déjà inscrit une sortie au registre de "
                "%(societe)s, et une inscription ne se retire pas.\n\n"
                "Si le métal ne doit pas partir, réceptionnez-le puis "
                "établissez un transfert en sens inverse : le registre dira "
                "l'aller et le retour, ce qui s'est réellement passé. Si "
                "l'inscription elle-même est fautive, rectifiez-la depuis le "
                "registre, avec son motif.",
                societe=self.company_id.display_name))
        self.state = 'annule'
        return True

    def unlink(self):
        """Un transfert se jette tant qu'il n'a rien inscrit.

        En brouillon ou annulé, il ne désigne que des intentions : aucun
        numéro d'ordre n'a été pris, aucun bon de stock n'existe, et le
        registre l'ignore. Le jeter ne perd donc rien — pas plus que de
        déchirer un bon de commande qu'on n'a pas passé.

        Expédié, c'est l'inverse : il porte le motif recopié sur deux
        inscriptions, celle de la sortie et celle de l'entrée, et ces
        inscriptions le désignent. La base elle-même refuserait de le retirer
        — autant le dire en clair, et dire quoi faire à la place.
        """
        engages = self.filtered(lambda t: t.state not in ('brouillon', 'annule'))
        if engages:
            raise UserError(_(
                "Le transfert %(references)s a déjà inscrit au registre : il "
                "ne se supprime pas.\n\n"
                "Une inscription ne se retire pas (c. pén., art. R321-6-1), "
                "et celles-ci portent son motif. Si le métal ne devait pas "
                "partir, réceptionnez-le puis établissez un transfert en sens "
                "inverse : le registre dira l'aller et le retour, ce qui s'est "
                "réellement passé.",
                references=", ".join(engages.mapped('name'))))
        return super().unlink()

    def action_voir_inscriptions(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Inscriptions du transfert %s" % self.name,
            'res_model': 'livre.police.ligne',
            'view_mode': 'list,form',
            'domain': [('transfert_id', '=', self.id)],
        }


class LivrePoliceTransfertLigne(models.Model):
    _name = 'livre.police.transfert.ligne'
    _description = "Livre de police - lot d'un transfert entre etablissements"
    _order = 'transfert_id, id'

    transfert_id = fields.Many2one(
        'livre.police.transfert', string="Transfert", required=True,
        ondelete='cascade', index=True,
    )

    _sql_constraints = [
        # Un numero d'ordre ne figure qu'une fois. C'est ce qui permet
        # d'apparier chaque mouvement de stock a sa ligne par ce numero, sans
        # parier sur l'ordre dans lequel Odoo a cree les mouvements. Deux
        # departs d'un meme lot se font en deux transferts, ce qui est aussi
        # ce que le registre inscrira : deux sorties.
        ('inscription_unique', 'unique(transfert_id, inscription_id)',
         "Ce numéro d'ordre figure déjà sur ce transfert."),
    ]
    company_id = fields.Many2one(
        related='transfert_id.company_id', string="Établissement de départ",
    )
    # Odoo ne sait pas lire un domaine porte par le document depuis la ligne :
    # `parent.` ne vaut que pour les conditions d'affichage. Le domaine se
    # relit donc ici, sur la ligne elle-meme, ou la vue peut le nommer.
    inscription_domaine = fields.Char(
        related='transfert_id.inscription_domaine', readonly=True,
    )
    inscription_id = fields.Many2one(
        'livre.police.ligne', string="N° d'ordre", required=True,
        ondelete='restrict', index=True,
        help="L'inscription d'entrée du métal à l'établissement de départ. "
             "C'est elle qui décrit ce qui part, et c'est à elle que la "
             "sortie se rattachera.",
    )
    lot_id = fields.Many2one(
        'stock.lot', string="Lot", compute='_compute_lot_id', store=True,
        readonly=True, ondelete='restrict',
        help="Le lot en stock que cette inscription désigne, retrouvé par le "
             "nom qu'il porte.",
    )
    product_id = fields.Many2one(
        related='lot_id.product_id', string="Article", readonly=True,
    )
    quantite_disponible = fields.Float(
        string="Disponible", digits=(12, 4), compute='_compute_disponible',
        aggregator=False,
    )
    quantite = fields.Float(
        string="Quantité", digits=(12, 4), required=True, default=0.0,
        aggregator=False,
        help="Ce qui part. Par défaut tout ce qui reste du lot ; un lot peut "
             "se scinder, chaque part prenant sa propre inscription.",
    )
    poids = fields.Float(
        string="Poids (g)", digits=(12, 4), compute='_compute_poids',
        help="Le poids qui part, déduit de celui de l'inscription au prorata "
             "de la quantité — c'est le calcul que fait déjà toute sortie.",
    )
    description = fields.Text(
        related='inscription_id.description', string="Objets", readonly=True,
    )
    numero_ordre = fields.Char(
        string="N° d'ordre", compute='_compute_numero_ordre', store=True,
        readonly=True,
        help="Recopié de l'inscription. L'établissement d'arrivée peut ainsi "
             "lire le transfert sans avoir accès au registre de l'autre.",
    )
    vendeur_nom = fields.Char(
        string="Vendeur", compute='_compute_identite',
        help="Qui a apporté ce métal au comptoir. « Vendeur » et non "
             "« client » : sur un rachat, le tiers de la pièce est celui qui "
             "a vendu.",
    )
    avoir_id = fields.Many2one(
        'account.move', string="Avoir d'origine", compute='_compute_identite',
        help="La pièce comptable du rachat. Vide sur un métal déjà reçu d'un "
             "autre établissement : c'est là-bas qu'elle a été passée, et la "
             "colonne « Comptoir de rachat » dit où la chercher.",
    )
    origine = fields.Char(
        string="Comptoir de rachat", compute='_compute_identite',
        help="L'établissement qui a acheté ce métal, et son numéro d'ordre "
             "de l'époque. Il ne change pas au fil des transferts.",
    )

    @api.depends('inscription_id')
    def _compute_numero_ordre(self):
        for ligne in self:
            ligne.numero_ordre = ligne.inscription_id.sudo().numero_ordre

    @api.depends('inscription_id')
    def _compute_identite(self):
        """Le vendeur et l'avoir, à qui tient le registre où ils sont inscrits.

        Le document se lit des deux établissements — celui qui expédie doit
        suivre son métal, celui qui reçoit doit le voir venir. Mais « le
        registre d'un établissement n'a pas à montrer les clients d'un
        autre » : la lecture passe en `sudo` pour que le document s'ouvre, et
        ces trois colonnes se taisent devant qui ne tient pas ce registre-là.

        L'origine, elle, se dit toujours : elle nomme un comptoir, pas une
        personne, et c'est justement ce que l'arrivée doit savoir.
        """
        for ligne in self:
            inscription = ligne.inscription_id.sudo()
            origine = inscription.origine_id or inscription
            ligne.origine = "%s %s" % (
                origine.company_id.display_name, origine.numero_ordre
            ) if inscription else False
            tenu = inscription.company_id in self.env.companies
            ligne.vendeur_nom = inscription.vendeur_nom if tenu else False
            ligne.avoir_id = inscription.move_id if tenu else False

    @api.depends('inscription_id', 'transfert_id.company_id')
    def _compute_lot_id(self):
        """Retrouve le lot par le nom que l'inscription lui connaît.

        Le nom d'un lot est unique par article dans une société, et la suite
        des numéros d'ordre est unique dans l'établissement : un nom désigne
        donc un lot et un seul. Un lot déjà transféré n'appartient plus à
        aucune société — il se cherche aussi de ce côté-là.
        """
        Lot = self.env['stock.lot'].sudo()
        for ligne in self:
            inscription = ligne.inscription_id
            if not inscription.numero_lot:
                ligne.lot_id = False
                continue
            societe = ligne.transfert_id.company_id
            ligne.lot_id = Lot.search([
                ('name', 'in', list(inscription._noms_de_lot())),
                ('company_id', 'in', [societe.id, False]),
            ], limit=1)

    @api.depends('lot_id', 'transfert_id.company_id')
    def _compute_disponible(self):
        Quant = self.env['stock.quant'].sudo()
        for ligne in self:
            if not ligne.lot_id:
                ligne.quantite_disponible = 0.0
                continue
            quants = Quant.search([
                ('lot_id', '=', ligne.lot_id.id),
                ('location_id.usage', '=', 'internal'),
                ('company_id', '=', ligne.transfert_id.company_id.id),
            ])
            ligne.quantite_disponible = sum(
                quants.mapped('quantity')) - sum(
                quants.mapped('reserved_quantity'))

    @api.depends('quantite', 'inscription_id')
    def _compute_poids(self):
        for ligne in self:
            inscription = ligne.inscription_id
            ligne.poids = (
                inscription.poids * ligne.quantite / inscription.quantite
                if inscription.quantite else 0.0)

    @api.onchange('inscription_id')
    def _onchange_inscription_id(self):
        """Tout ce qui reste part, sauf à dire le contraire."""
        for ligne in self:
            ligne.quantite = ligne.quantite_disponible

    def _verifier(self):
        """Refuse ce qui ne peut pas partir, avant que rien ne soit inscrit."""
        for ligne in self:
            if not ligne.lot_id:
                raise UserError(_(
                    "L'inscription %(numero)s n'a pas de lot en stock.\n\n"
                    "Un transfert déplace du métal étiqueté : tant que la "
                    "réception du rachat n'est pas validée, le lot n'existe "
                    "pas et il n'y a rien à déplacer.",
                    numero=ligne.inscription_id.numero_ordre))
            if ligne.quantite <= 0:
                raise UserError(_(
                    "La quantité à transférer de %(numero)s est nulle.",
                    numero=ligne.inscription_id.numero_ordre))
            if ligne.quantite > ligne.quantite_disponible + 0.00005:
                raise UserError(_(
                    "Il ne reste que %(dispo)s de %(numero)s en stock à "
                    "%(societe)s, et le transfert en demande %(demande)s.",
                    dispo="%g" % ligne.quantite_disponible,
                    numero=ligne.inscription_id.numero_ordre,
                    societe=ligne.transfert_id.company_id.display_name,
                    demande="%g" % ligne.quantite))
            if ligne.inscription_id.company_id != ligne.transfert_id.company_id:
                raise UserError(_(
                    "L'inscription %(numero)s appartient au registre de "
                    "%(autre)s, pas à celui de %(societe)s.",
                    numero=ligne.inscription_id.numero_ordre,
                    autre=ligne.inscription_id.company_id.display_name,
                    societe=ligne.transfert_id.company_id.display_name))

    def _qualifier_les_lots(self):
        """Détache le lot de sa société et lui donne le nom du comptoir.

        Le sachet ne bouge pas : il porte « 000123 » et continuera de le
        porter. C'est le nom en base qui se qualifie, parce qu'un même
        « 000123 » existe dans chaque agence et qu'Odoo refuserait le second.
        « METZ/000123 » dit le même numéro et dit d'où il vient.

        Le lot cesse ensuite d'appartenir à une société, et c'est ce qui
        permet au **même** enregistrement de traverser : rien n'est recréé à
        l'arrivée, la quantité sort d'un côté comme elle entre de l'autre, et
        la traçabilité du stock n'est pas coupée en deux.
        """
        for ligne in self:
            lot = ligne.lot_id.sudo()
            nom = ligne.inscription_id._nom_lot_partage()
            if lot.name != nom or lot.company_id:
                lot.write({'name': nom, 'company_id': False})
