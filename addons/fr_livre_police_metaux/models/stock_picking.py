# -*- coding: utf-8 -*-
"""Le lot du stock porte le numéro d'ordre du registre.

« Chaque objet exposé à la vente ou détenu en stock est affecté d'un numéro
d'ordre. […] Le numéro d'ordre est porté sur le registre et figure de manière
apparente sur chaque objet ou lot d'objets » (c. pén., art. R321-4).

Odoo sait déjà étiqueter un lot, le suivre en stock et le retrouver à la
sortie ; il le nomme seulement d'après sa propre séquence. Deux numéros pour
une même chose, c'en est un de trop : l'étiquette du comptoir et la ligne du
registre finiraient par diverger, et c'est l'étiquette qu'un contrôle a sous
les yeux. Le lot reprend donc le numéro d'ordre, et rien d'autre.

Reste que les deux ne naissent pas au même instant. Le numéro d'ordre est
attribué à la comptabilisation de l'avoir ; Odoo réclame le lot à la
validation de la réception. L'ordre est donc imposé, et il ne l'est pas pour
la commodité du logiciel : on ne fait pas entrer en stock un métal dont
l'achat n'est pas encore arrêté. Le refus est explicite parce que
l'alternative — nommer le lot provisoirement puis le renommer — laisse une
fenêtre pendant laquelle l'étiquette ment.

Le même fichier tient l'autre bout : le métal qui change d'établissement.
Il ne passe que par un document de transfert (`livre_police_transfert.py`),
et le bon de stock refuse de partir ou d'arriver sans lui — sans quoi le
métal quitterait un registre sans entrer dans l'autre, et sa revente
ultérieure ne s'inscrirait nulle part.
"""

from collections import defaultdict

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.mail import plaintext2html


class StockMove(models.Model):
    _inherit = 'stock.move'

    police_ligne_id = fields.Many2one(
        'livre.police.ligne', string="Inscription au registre",
        compute='_compute_police_ligne_id',
        help="L'inscription née de l'avoir qui a acheté ce métal. Elle "
             "n'existe qu'une fois l'avoir comptabilisé : c'est elle qui "
             "porte le numéro d'ordre dont le lot prendra le nom.",
    )
    police_numero_ordre = fields.Char(
        string="N° d'ordre", related='police_ligne_id.numero_ordre',
        readonly=True,
    )
    police_description = fields.Text(
        # Et non `description_picking`, qui est un champ libre rempli a la
        # creation du mouvement, depuis l'article : a cet instant la
        # description du registre n'existe pas encore. Celle-ci se lit, elle
        # ne s'ecrit pas, et elle apparait des que l'avoir est comptabilise.
        string="Description au registre",
        related='police_ligne_id.description', readonly=True,
        help="Les objets tels que le registre les a decrits. « 1 collier "
             "maille gourmette, 1 bague sertie, or jaune 18k » dit ce que "
             "« 18k Or 750 ‰(gr) » ne dira jamais.",
    )

    @api.depends('sale_line_id', 'sale_line_id.invoice_lines')
    def _compute_police_ligne_id(self):
        """Remonte du mouvement à l'inscription, par la facture.

        Le chemin est celui de la marchandise : un mouvement naît d'une ligne
        de devis, la ligne de devis se facture, et c'est la ligne de facture
        que le registre a recopiée. Rien ne relie directement le stock au
        registre, et c'est tant mieux — le registre atteste l'achat, pas le
        rangement.
        """
        Ligne = self.env['livre.police.ligne'].sudo()
        for mouvement in self:
            lignes_facture = mouvement.sale_line_id.invoice_lines
            mouvement.police_ligne_id = Ligne.search(
                [('move_line_id', 'in', lignes_facture.ids)], limit=1,
            ) if lignes_facture else False

    def _police_entrees_de_rachat(self):
        """Les mouvements d'entrée nés d'un rachat, qui doivent un numéro."""
        return self.filtered(
            lambda mouvement: mouvement.picking_code == 'incoming'
            and mouvement.sale_line_id.police_origin_required)

    @api.constrains('quantity', 'product_uom_qty', 'state')
    def _police_check_demande_respectee(self):
        """On ne sort pas plus de métal que le mouvement n'en demande.

        La sortie s'inscrit au registre, et le registre est confronté à la
        vente : 184,30 g partis pour 177,50 vendus, et rien ne dit lequel des
        deux a raison. Le remède est du côté de la vente, qui dit ce qui part.
        """
        if self.env.context.get('police_validation'):
            return
        ecarts = []
        for mouvement in self:
            if mouvement.state in ('done', 'cancel'):
                continue
            if not mouvement.product_id.product_tmpl_id.metal_regulated:
                continue
            # Un rachat traverse un etat que ce controle ne doit pas lire. La
            # regle de flux cree d'abord le mouvement tel que le devis le dit
            # — demande negative, source encore interne — puis le retourne en
            # une entree du client vers le coffre. Entre les deux, « 0 saisi
            # pour -1 demande » est arithmetiquement un depassement et ne
            # decrit rien : aucun metal ne sort d'un rachat.
            if mouvement.product_uom_qty < 0:
                continue
            if mouvement.location_id.usage != 'internal':
                continue
            if mouvement.quantity <= mouvement.product_uom_qty + 0.00005:
                continue
            ecarts.append(_(
                "%(article)s : %(saisi)s saisis, %(demande)s demandés",
                article=mouvement.product_id.display_name,
                saisi=mouvement.quantity, demande=mouvement.product_uom_qty))
        if ecarts:
            raise UserError(_(
                "Ce bon ferait sortir plus de métal que la vente n'en "
                "porte.\n\n"
                "La sortie s'inscrit au registre : elle dirait qu'un métal "
                "est parti que rien ne justifie, et une inscription ne se "
                "retire pas.\n\n"
                "%(ecarts)s\n\n"
                "Si le client emporte davantage, c'est la vente qu'il faut "
                "reprendre — la quantité sur la ligne de devis — puis "
                "revenir au bon.",
                ecarts="\n".join(ecarts)))


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _prepare_new_lot_vals(self):
        """Le lot naît décrit.

        Le nom du lot dit lequel ; la description dit lequel c'est. Au moment
        de choisir ce qui sort du stock, « 000004 — 21,6 g » ne se distingue
        pas de son voisin, quand « 1 lot de chaînes et pendentifs, titres
        mêlés » se reconnaît sans hésiter.

        Elle est portée à la naissance du lot, et pas après : c'est le seul
        instant où l'inscription d'origine est certaine — le livrable qui
        nomme le lot a déjà refusé toute réception sans elle.
        """
        valeurs = super()._prepare_new_lot_vals()
        inscription = self.move_id.police_ligne_id
        if not inscription:
            return valeurs
        valeurs['note'] = plaintext2html(inscription.description or '')
        # Le lot appartient à l'agence qui l'a inscrit. Sans société, Odoo
        # exige que le nom soit unique pour l'article dans toute la base — et
        # chaque agence repart de 000001. Le second « 000004 » sur le même
        # article serait refusé, et la réception avec lui.
        valeurs['company_id'] = inscription.company_id.id
        return valeurs

    def _police_manques_par_lot(self):
        """Ce qui manquerait au stock si ces lignes sortaient telles quelles.

        Le total se fait **par lot**, pas par ligne : deux lignes de 5 sur un
        lot qui en porte 6 sont chacune innocente et le couple ne l'est pas.
        Odoo permet le même lot sur deux lignes — c'est ainsi qu'on répartit
        un lot entre deux colis — et rien ici ne l'interdit ; seul le total
        est plafonné.
        """
        Quant = self.env['stock.quant'].sudo()
        preleve = defaultdict(float)
        for ligne in self:
            if not ligne.lot_id or ligne.state in ('done', 'cancel'):
                continue
            if not ligne.product_id.product_tmpl_id.metal_regulated:
                continue
            if ligne.location_id.usage != 'internal':
                continue
            preleve[(ligne.lot_id, ligne.location_id,
                     ligne.company_id)] += ligne.quantity

        manques = []
        for (lot, emplacement, societe), quantite in preleve.items():
            detenu = sum(Quant.search([
                ('lot_id', '=', lot.id),
                ('location_id', 'child_of', emplacement.id),
                ('company_id', '=', societe.id),
            ]).mapped('quantity'))
            if quantite > detenu + 0.00005:
                manques.append(_(
                    "%(lot)s : %(demande)s demandés, %(detenu)s détenus",
                    lot=lot.name, demande=quantite, detenu=detenu))
        return manques

    def _police_refus_stock(self, manques):
        """Le refus, dit d'une seule façon où qu'il tombe."""
        return _(
            "Ce bon ferait sortir plus de métal qu'il n'y en a.\n\n"
            "La sortie s'inscrit au registre à la validation : elle "
            "affirmerait qu'un métal est parti alors qu'il n'a jamais "
            "été là, et une inscription ne se retire pas.\n\n"
            "%(manques)s\n\n"
            "Corrigez la quantité. Si c'est le stock qui est faux, "
            "c'est lui qu'il faut reprendre — « Rectifier les "
            "quantités » ou « Régulariser une arrivée » — avant de "
            "faire sortir quoi que ce soit.",
            manques="\n".join(manques))

    @api.constrains('quantity', 'lot_id', 'location_id')
    def _police_check_stock_a_la_saisie(self):
        """Le plafond s'oppose à la saisie, et non à la seule validation.

        Refuser au bout laissait la réservation dépasser le détenu — 50
        réservés sur 30 — sous un écran qui annonçait « Disponible » en vert.

        Le contrôle porte sur tout le bon : le même lot peut se retrouver sur
        deux mouvements, et c'est leur somme qui compte.
        """
        if self.env.context.get('police_validation'):
            return
        lignes = self | self.picking_id.move_line_ids | self.move_id.move_line_ids
        manques = lignes._police_manques_par_lot()
        if manques:
            raise UserError(lignes._police_refus_stock(manques))


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    police_transfert_id = fields.Many2one(
        'livre.police.transfert', string="Transfert entre établissements",
        readonly=True, index='btree_not_null', ondelete='restrict',
        copy=False,
        help="Le document qui justifie ce déplacement d'un établissement à "
             "l'autre et porte son motif. C'est lui qui a créé ce bon.",
    )

    #: Les chemins par lesquels un metal reglemente peut legitimement bouger.
    #: Tout le reste est refuse — voir `_police_check_mouvement_justifie`.
    _POLICE_DROIT_CORRECTION = 'fr_livre_police_metaux.group_livre_police_correction'

    def button_validate(self):
        self._police_check_inscription()
        self._police_check_transfert()
        self._police_check_reception()
        self._police_check_mouvement_justifie()
        self._police_check_stock_suffisant()
        # Et non la seule contrainte : un bon deja excedentaire avant ce
        # correctif n'a plus a etre ecrit pour etre valide, et passerait.
        self.move_ids._police_check_demande_respectee()
        self._police_nommer_les_lots()
        return super().button_validate()

    def _police_check_stock_suffisant(self):
        """Un lot ne sort pas plus qu'il n'en contient.

        Le registre affirmerait qu'un metal est parti alors qu'il n'a jamais
        ete la, et une inscription ne se retire pas. Aucun droit n'en dispense.

        Double avec `StockMoveLine._police_check_stock_a_la_saisie` : le stock
        a pu bouger ailleurs entre la saisie et la validation.
        """
        for bon in self:
            manques = bon.move_line_ids._police_manques_par_lot()
            if manques:
                raise UserError(bon.move_line_ids._police_refus_stock(manques))

    def _police_check_mouvement_justifie(self):
        """Un metal reglemente ne bouge que par un chemin qui laisse une trace.

        Un bon cree a la main ne rattache le mouvement a aucune operation : le
        registre dit que le metal est parti sans pouvoir dire ou ni a qui.

        Trois chemins restent ouverts — le transfert entre etablissements, la
        vente par sa ligne de devis, l'achat par son avoir — plus le droit de
        correction, qui dispense de justifier le mouvement par un document,
        non d'inscrire.
        """
        if self.env.user.has_group(self._POLICE_DROIT_CORRECTION):
            return
        for bon in self:
            if bon.police_transfert_id:
                continue
            orphelins = bon.move_ids.filtered(
                lambda m: m.state not in ('done', 'cancel')
                and m.product_id.product_tmpl_id.metal_regulated
                and not m.sale_line_id)
            if not orphelins:
                continue
            entrant = bon.picking_type_code == 'incoming'
            raise UserError(_(
                "Ce bon fait %(sens)s du métal soumis au registre sans qu'aucun "
                "document ne le justifie.\n\n"
                "%(chemins)s\n\n"
                "Le registre s'écrit à partir des mouvements de stock : un "
                "mouvement que rien ne rattache à une opération y inscrit un "
                "départ ou une arrivée que personne ne peut expliquer.\n\n"
                "Articles concernés : %(articles)s",
                sens=_("entrer") if entrant else _("sortir"),
                chemins=(_("Une entrée passe par un avoir de rachat, ou par un "
                           "transfert entre établissements.") if entrant
                         else _("Une sortie passe par un devis — vente ou "
                                "expédition au fondeur — ou par un transfert "
                                "entre établissements.")),
                articles=", ".join(orphelins.mapped('product_id.name'))))

    def _police_check_reception(self):
        """Le bouton du document n'est pas le seul chemin vers la réception.

        L'agence d'arrivée peut valider son bon depuis l'inventaire, comme
        n'importe quelle réception — c'est même ce qu'elle fera le jour où le
        métal arrive sans que personne ne rouvre le transfert. Le droit se
        vérifie donc ici aussi, sans quoi la garde posée sur le document
        s'esquiverait d'un clic ailleurs.
        """
        for bon in self.filtered('police_transfert_id'):
            transfert = bon.police_transfert_id
            if transfert.picking_entree_id == bon:
                transfert._verifier_le_droit_de_receptionner()

    def _action_done(self):
        """Le métal qui part s'inscrit, une fois le transfert réellement fait.

        Et non dans `button_validate`, qui peut rendre un assistant — reliquat,
        transfert immédiat — et rendre la main sans que rien ne soit sorti.
        `_action_done` est le moment où le stock a bougé.
        """
        # Pendant la validation, les quants se debitent : les controles de
        # saisie compareraient la ligne a un stock deja diminue, et refuseraient
        # la sortie qu'ils viennent d'autoriser. Ils ont eu lieu avant, dans
        # `button_validate`.
        resultat = super(
            StockPicking, self.with_context(police_validation=True),
        )._action_done()
        Registre = self.env['livre.police.ligne']
        Registre._inscrire_sorties(self)
        Registre._inscrire_entrees_transfert(self)
        self.police_transfert_id._marquer_recu(self)
        return resultat

    def _police_check_inscription(self):
        """Refuse de réceptionner un métal dont l'achat n'est pas inscrit."""
        sans_inscription = self.move_ids._police_entrees_de_rachat().filtered(
            lambda mouvement: not mouvement.police_ligne_id)
        if not sans_inscription:
            return
        raise UserError(_(
            "Ce métal n'est pas encore inscrit au registre.\n\n"
            "Le lot prend le numéro d'ordre de l'inscription, et "
            "l'inscription naît à la comptabilisation de l'avoir. "
            "Comptabilisez l'avoir, puis revenez valider la réception : le "
            "numéro se posera seul.\n\n"
            "Sans cela, le lot recevrait un numéro de séquence sans rapport "
            "avec le registre, et l'étiquette apposée sur le métal ne "
            "désignerait plus rien (c. pén., art. R321-4).\n\n"
            "Articles concernés : %(articles)s",
            articles=", ".join(sans_inscription.mapped('product_id.name'))))

    def _police_check_transfert(self):
        """Refuse un passage par le transit qui ne serait pas justifié.

        L'emplacement de transit est le seul chemin entre deux établissements,
        et il n'appartient à aucun d'eux. Un métal qui y entre a donc quitté
        un registre ; un métal qui en sort entre dans un autre. Laisser faire
        cela sans document, ce serait rendre au registre le trou qu'on vient
        de boucher : une sortie muette d'un côté, aucune entrée de l'autre, et
        une revente que plus rien ne rattache à un rachat.

        La vérification porte sur les seuls articles soumis au livre de police
        — un emballage, un consommable peuvent circuler librement.
        """
        sans_document = self.filtered(lambda bon: not bon.police_transfert_id)
        concernes = sans_document.move_ids.filtered(
            lambda mouvement: mouvement.product_id.product_tmpl_id.metal_regulated
            and 'transit' in (mouvement.location_id.usage,
                              mouvement.location_dest_id.usage))
        if not concernes:
            return
        raise UserError(_(
            "Ce bon fait passer du métal par le transit sans transfert "
            "déclaré.\n\n"
            "Un registre est tenu pour chaque établissement (c. pén., "
            "art. R321-6) : le métal qui passe de l'un à l'autre doit sortir "
            "du premier et entrer dans le second, avec le motif du "
            "déplacement. Établissez un « Transfert entre établissements » "
            "depuis le livre de police — il crée lui-même les deux bons et "
            "les inscrit.\n\n"
            "Articles concernés : %(articles)s",
            articles=", ".join(concernes.mapped('product_id.name'))))

    def _police_nommer_les_lots(self):
        """Pose le numéro d'ordre comme nom de lot, avant la validation.

        On écrase ce qui aurait été saisi : le nom du lot n'est pas un choix
        d'opérateur, c'est une donnée du registre. Odoo créera le lot lui-même
        à partir de ce nom, comme il le fait pour toute réception.
        """
        for mouvement in self.move_ids._police_entrees_de_rachat():
            if mouvement.product_id.tracking == 'none':
                continue
            numero = mouvement.police_ligne_id.numero_ordre
            lignes = mouvement.move_line_ids.filtered(
                lambda ligne: not ligne.lot_id)
            if numero and lignes:
                lignes.lot_name = numero
