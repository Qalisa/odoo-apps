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

Qui vend, lorsque le vendeur est une société
--------------------------------------------

Les trois mentions ci-dessus décrivent l'objet. Une quatrième décrit celui qui
l'apporte, et elle change de forme quand le vendeur est une personne morale.

CE QUE LE DROIT EXIGE — l'art. R321-3 2° du code pénal veut au registre,
« lorsqu'il s'agit d'une personne morale, la dénomination et le siège de
celle-ci ainsi que les nom, prénoms, qualité et domicile du représentant ».

Une société ne se présente pas au comptoir : quelqu'un vient pour elle. Le
registre ne se contente donc pas de la raison sociale, il veut savoir **qui**
a remis les objets, et **à quel titre** il engageait la société. Sans cette
personne, la ligne du registre désigne une abstraction.

Le client d'un tel rachat reste la société : c'est elle qui a vendu, elle qui
est payée, et c'est sa dénomination que l'avoir doit porter. Le représentant
prend donc un champ à part, et sa qualité se lit sur sa propre fiche.

**Cette qualité est le champ « Poste »** (``function``), et non la liste
``police_qualite_id`` du vendeur particulier. Odoo y range déjà la fonction
d'un contact dans sa société — gérant, mandataire, salarié — et c'est
exactement ce que le 2° appelle la qualité du représentant. La liste
administrable, elle, sert à une profession (« Retraité(e) », « Sans
profession »), qui ne dit rien du lien avec une personne morale.

**Ce poste devient bloquant**, alors que la qualité ne l'est pas d'un vendeur
particulier. Ce n'est pas une inégalité de traitement : d'une personne
physique, la qualité complète une identité que la pièce d'identité établit
déjà ; du représentant, elle *est* le lien avec la société, et rien d'autre
au document ne l'établit. Le comptoir peut avancer sans savoir qu'un vendeur
est retraité ; il ne peut pas consigner qu'une société a vendu sans dire qui
l'engageait.
"""

from odoo import models, fields, api, Command, _
from odoo.exceptions import UserError
from odoo.tools import float_compare

from ..tools.description import description_ajoutee
from ..tools.reglement import MODES_REGLEMENT


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

    def action_police_reprendre_stock(self):
        """Relais depuis la barre sous les lignes, qui appartient à la liste.

        La barre « Ajouter un produit / Catalogue » est le `<control>` de la
        liste des lignes : ses boutons appellent donc `sale.order.line`, et
        le devis se retrouve par le contexte. C'est le chemin que prend déjà
        `action_add_from_catalog`.
        """
        devis = self.env['sale.order'].browse(self.env.context.get('order_id'))
        return devis.action_police_reprendre_stock()


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    police_registre_concerne = fields.Boolean(
        string="Document soumis au registre",
        compute='_compute_police_registre_concerne',
        help="Vrai dès qu'une ligne porte un article inscrit au registre. "
             "Commande l'affichage de la colonne « Provenance ».",
    )

    police_reglement = fields.Selection(
        MODES_REGLEMENT, string="Mode de règlement",
        help="Comment le vendeur sera payé.\n\n"
             "Mention obligatoire du registre, que le modèle officiel range "
             "avec le prix : c'est une caractéristique de l'opération, "
             "arrêtée devant le vendeur, et non un événement comptable "
             "postérieur.\n\n"
             "La liste ne propose que les deux moyens que la loi admet : "
             "« lorsqu'un professionnel achète des métaux à un particulier ou "
             "à un autre professionnel, le paiement est effectué par chèque "
             "barré ou par virement à un compte ouvert au nom du vendeur » "
             "(code monétaire et financier, art. L112-6). Les espèces sont "
             "exclues quel que soit le montant.",
    )
    police_representant_id = fields.Many2one(
        'res.partner', string="Représentant",
        compute='_compute_police_representant_id', store=True, readonly=False,
        ondelete='restrict', index='btree_not_null',
        help="Personne physique qui a remis les objets au nom de la société.\n\n"
             "Mention obligatoire du registre : « lorsqu'il s'agit d'une "
             "personne morale, la dénomination et le siège de celle-ci ainsi "
             "que les nom, prénoms, qualité et domicile du représentant » "
             "(art. R321-3 2° du code pénal).\n\n"
             "Une société ne se présente pas au comptoir : quelqu'un vient "
             "pour elle, et le registre veut savoir qui.",
    )
    # « Poste » (`function`), et non la liste `police_qualite_id`. Ce champ
    # standard d'Odoo dit deja la fonction d'un contact dans sa societe :
    # c'est exactement ce que le registre appelle la qualite du representant.
    # La liste administrable reste celle du vendeur particulier, dont la
    # qualite est une profession et non une fonction.
    police_representant_poste = fields.Char(
        related='police_representant_id.function', readonly=True,
        string="Poste du représentant",
        help="Poste occupé dans la société, au sens du champ « Poste » de la "
             "fiche contact : gérant(e), mandataire, salarié(e)…\n\n"
             "C'est la « qualité » que le registre exige du représentant "
             "(art. R321-3 2° du code pénal).\n\n"
             "Simple report de sa fiche, non modifiable ici : le poste "
             "appartient à la personne et vaut pour tous ses rachats. Le "
             "corriger depuis un devis le changerait rétroactivement pour "
             "les autres.",
    )
    police_representant_expected = fields.Boolean(
        string="Vendeur rattaché à une société",
        compute='_compute_police_representant_expected',
        help="Vrai lorsque le client est une personne morale, ou une personne "
             "qui lui est rattachée, et que le document porte un article "
             "inscrit au registre. Ouvre la zone du représentant sans "
             "attendre que le sens de l'opération soit connu.",
    )
    police_representant_required = fields.Boolean(
        string="Représentant exigé",
        compute='_compute_police_representant_required',
        help="Vrai lorsque le document fait entrer au registre un objet remis "
             "au nom d'une société.",
    )
    police_representant_missing = fields.Boolean(
        string="Représentant non désigné",
        compute='_compute_police_representant_missing',
        help="Aucune personne physique n'est nommée, et le registre en veut "
             "une.",
    )
    police_poste_missing = fields.Boolean(
        string="Poste manquant",
        compute='_compute_police_poste_missing',
        help="Le représentant est nommé, mais sa fiche ne dit pas à quel "
             "titre il engage la société.",
    )

    @api.depends('order_line.police_origin_required')
    def _compute_police_registre_concerne(self):
        """Un rachat, et non toute commande qui touche au métal.

        `police_origin_expected` dit qu'un article relève du registre ;
        `police_origin_required` dit que la ligne l'y fait entrer, ce qui
        suppose une quantité négative. Seul le second convient ici : vendre de
        l'or n'inscrit rien au registre des entrées, et réclamer un mode de
        règlement à une vente invente une obligation. Le CMF L112-6 vise le
        professionnel qui achète, pas celui qui vend.

        C'est déjà la règle du côté de l'avoir, qui lit
        `invoice_line_ids.police_origin_required` : les deux disent désormais
        la même chose.
        """
        for commande in self:
            commande.police_registre_concerne = any(
                commande.order_line.mapped('police_origin_required'))

    @api.depends('partner_id')
    def _compute_police_representant_id(self):
        """Un contact choisi comme client est déjà la personne attendue.

        Le comptoir est censé saisir la société comme client, puis la
        personne juste en dessous. Mais il arrive qu'on saisisse directement
        le contact : la personne est alors déjà nommée, et la redésigner
        n'aurait aucun sens. Le champ reste modifiable — c'est un point de
        départ, pas une conclusion.
        """
        for commande in self:
            vendeur = commande.partner_id
            commande.police_representant_id = (
                vendeur if vendeur and not vendeur.is_company
                and vendeur.commercial_partner_id.is_company else False)

    @api.onchange('partner_id')
    def _onchange_police_societe_comme_client(self):
        """Choisir un contact de société, c'est vendre pour cette société.

        Le comptoir cherche la personne qu'il a devant lui, et la trouve par
        son nom. Mais celle qui vend est la société : c'est elle qui est
        payée, et c'est sa dénomination que l'avoir doit porter. Le client
        bascule donc sur elle, et la personne rejoint le champ que le registre
        lui réserve — la saisie reste celle du comptoir, l'enregistrement
        devient le bon.

        L'ordre des deux affectations compte. ``police_representant_id`` se
        recalcule sur tout changement de ``partner_id`` : le poser avant
        reviendrait à le voir effacé aussitôt.
        """
        for commande in self:
            personne = commande.partner_id
            societe = personne.commercial_partner_id
            if personne and not personne.is_company and societe != personne:
                commande.partner_id = societe
                commande.police_representant_id = personne

    @api.depends('partner_id.commercial_partner_id.is_company',
                 'order_line.police_origin_expected')
    def _compute_police_representant_expected(self):
        for commande in self:
            commande.police_representant_expected = bool(
                commande.partner_id.commercial_partner_id.is_company
                and any(commande.order_line.mapped('police_origin_expected')))

    @api.depends('partner_id.commercial_partner_id.is_company',
                 'order_line.police_origin_required')
    def _compute_police_representant_required(self):
        """Ce qui compte est la société, pas le contact par lequel on la joint.

        Le vendeur du registre est la personne morale dès que le document lui
        est rattaché — que le comptoir ait saisi la société ou l'un de ses
        contacts. Ne regarder que ``partner_id`` laisserait passer, sans
        qualité, tout rachat enregistré sur un contact.
        """
        for commande in self:
            commande.police_representant_required = bool(
                commande.partner_id.commercial_partner_id.is_company
                and any(commande.order_line.mapped('police_origin_required')))

    @api.depends('police_representant_required', 'police_representant_id')
    def _compute_police_representant_missing(self):
        for commande in self:
            commande.police_representant_missing = bool(
                commande.police_representant_required
                and not commande.police_representant_id)

    @api.depends('police_representant_required', 'police_representant_id',
                 'police_representant_id.function')
    def _compute_police_poste_missing(self):
        for commande in self:
            commande.police_poste_missing = bool(
                commande.police_representant_required
                and commande.police_representant_id
                and not commande.police_representant_id.function)

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

    def _police_check_reglement(self):
        """Refuse un rachat dont on ne sait pas comment il sera payé.

        Le contrôle est posé à la confirmation, avec les autres : c'est le
        moment où le prix se fixe, et le mode de règlement se convient dans la
        même phrase. Le constater après le paiement reviendrait à enregistrer
        au registre un fait déjà accompli — et, s'il était irrégulier, à n'en
        prendre acte qu'une fois l'argent parti.
        """
        for commande in self:
            if commande.police_registre_concerne and not commande.police_reglement:
                raise UserError(_(
                    "Le registre veut savoir comment ce rachat est payé : le "
                    "modèle officiel porte « le prix d'achat et le mode de "
                    "règlement » dans la même colonne (arrêté du 15 mai "
                    "2020, annexe I).\n\n"
                    "Indiquez le mode de règlement sous le client. Seuls le "
                    "chèque barré et le virement sont proposés : « lorsqu'un "
                    "professionnel achète des métaux à un particulier ou à un "
                    "autre professionnel, le paiement est effectué par chèque "
                    "barré ou par virement à un compte ouvert au nom du "
                    "vendeur » (code monétaire et financier, art. L112-6). "
                    "Les espèces sont exclues quel que soit le montant."))

    def _police_check_representant(self):
        """Refuse un rachat à une société que personne n'est venu engager.

        Le contrôle est posé à la confirmation, comme celui des objets : c'est
        le dernier moment où la personne est encore devant le comptoir. Une
        fois repartie, on ne saura plus qui elle était.
        """
        for commande in self:
            societe = commande.partner_id.commercial_partner_id
            if commande.police_representant_missing:
                raise UserError(_(
                    "« %(societe)s » est une personne morale : le devis ne "
                    "pourra pas être transformé en avoir tant que personne "
                    "n'est nommé.\n\n"
                    "Le registre comporte, pour une société, « la dénomination "
                    "et le siège de celle-ci ainsi que les nom, prénoms, "
                    "qualité et domicile du représentant » (art. R321-3 2° du "
                    "code pénal). Indiquez, sous le client, la personne "
                    "rattachée à cette société qui a remis les objets.",
                    societe=societe.display_name))
            if commande.police_poste_missing:
                representant = commande.police_representant_id
                raise UserError(_(
                    "La fiche de « %(personne)s » ne dit pas quel poste elle "
                    "occupe, et le devis ne pourra pas être transformé en "
                    "avoir.\n\n"
                    "Le registre veut « les nom, prénoms, qualité et domicile "
                    "du représentant » de la personne morale (art. R321-3 2° "
                    "du code pénal). Ouvrez sa fiche contact et renseignez "
                    "« Poste » : à quel titre engage-t-elle « %(societe)s » — "
                    "gérant(e), mandataire, salarié(e) ?",
                    personne=representant.display_name,
                    societe=societe.display_name))

    def _prepare_invoice(self):
        """L'avoir s'adresse à la société ; le registre, lui, nomme la personne.

        Le client de l'avoir est la société : c'est elle qui a vendu, c'est
        elle qui est payée, et c'est sa dénomination que la pièce doit porter.
        La personne physique, elle, n'intéresse que le registre — elle voyage
        donc à part.

        Le représentant suit donc le devis jusqu'à la pièce, sans quoi il
        serait saisi au comptoir puis perdu à la facturation, et le contrôle
        posé au ``_post`` refuserait une pièce que rien ne permettrait plus de
        compléter.

        Reste le cas où le comptoir a saisi le contact comme client plutôt que
        la société. L'avoir porterait alors le nom de la personne : le client
        bascule sur la société, qui est celle qui a vendu.

        La position fiscale n'est pas retouchée : Odoo l'a déduite du contact,
        et un contact sans position propre hérite déjà de celle de sa société.
        """
        valeurs = super()._prepare_invoice()
        if self.police_reglement:
            valeurs['police_reglement'] = self.police_reglement
        if self.police_representant_id:
            valeurs['police_representant_id'] = self.police_representant_id.id
        # Filet pour l'autre chemin de saisie : quand le contact a ete choisi
        # comme client, l'avoir porterait son nom. C'est la societe qui a
        # vendu et qui est payee — le client bascule sur elle, la personne
        # reste nommee par le champ ci-dessus.
        vendeur = self.partner_id
        if self.police_representant_required and not vendeur.is_company:
            valeurs['partner_id'] = vendeur.commercial_partner_id.id
        return valeurs

    def action_confirm(self):
        self._police_check_representant()
        self._police_check_registre()
        self._police_check_reglement()
        return super().action_confirm()

    def action_police_reprendre_stock(self):
        """Remplace les lignes du devis par tout le stock disponible.

        Vendre le stock d'une agence à un fondeur, c'est reprendre au devis
        ce que le coffre contient — article par article, et fautif au premier
        oubli. Le devis se remplit donc d'un coup, depuis les quantités
        réellement présentes dans son entrepôt.

        **Disponible**, et non « en stock » : ce qui est déjà réservé par une
        autre livraison partira ailleurs, et le proposer deux fois ferait
        sortir deux fois le même numéro d'ordre.

        **Une ligne par article**, et non par lot : une ligne de devis ne
        porte pas de lot, et lui en faire nommer un mentirait — c'est la
        livraison qui choisit, lot par lot, et c'est là que le choix se lit.

        Les lignes existantes sont remplacées, jamais complétées : un cumul
        doublerait les quantités au second clic.
        """
        self.ensure_one()
        if self.state not in ('draft', 'sent'):
            raise UserError(_(
                "Le stock ne se reprend que sur un devis : celui-ci est déjà "
                "confirmé, et ses lignes ont produit des mouvements."))
        if self.police_registre_concerne:
            raise UserError(_(
                "Ce devis est un rachat : il fait entrer du métal. Le remplir "
                "du stock déjà détenu n'aurait pas de sens."))
        entrepot = self.warehouse_id
        if not entrepot:
            raise UserError(_("Ce devis n'est rattaché à aucun entrepôt."))

        disponible = {}
        quants = self.env['stock.quant'].search([
            ('company_id', '=', self.company_id.id),
            ('location_id', 'child_of', entrepot.view_location_id.id),
            ('location_id.usage', '=', 'internal'),
        ])
        for quant in quants:
            libre = quant.available_quantity
            if float_compare(libre, 0.0,
                             precision_rounding=quant.product_uom_id.rounding) > 0:
                disponible[quant.product_id] = (
                    disponible.get(quant.product_id, 0.0) + libre)
        if not disponible:
            raise UserError(_(
                "Aucun stock disponible à %(entrepot)s. Le métal déjà "
                "réservé par une autre livraison n'est pas repris.",
                entrepot=entrepot.code))

        self.order_line = [Command.clear()] + [
            Command.create({'product_id': produit.id, 'product_uom_qty': quantite})
            for produit, quantite in sorted(disponible.items(),
                                            key=lambda couple: couple[0].display_name)
        ]
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _(
                    "Stock de %(entrepot)s repris : %(articles)s article(s). "
                    "Le métal déjà réservé par une autre livraison en est "
                    "exclu.",
                    entrepot=entrepot.code, articles=len(disponible)),
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }
