# -*- coding: utf-8 -*-
"""Le registre lui-même : une ligne par lot entré, figée à l'inscription.

Jusqu'ici, les mentions du registre vivaient sur l'avoir — la provenance sur
la ligne, le représentant sur la pièce, l'identité sur la fiche contact. Cela
suffit pour *recueillir* les mentions ; cela ne suffit pas pour *tenir* un
registre, et pour deux raisons.

La première est l'intangibilité. Le code pénal exige d'un registre tenu par
traitement automatisé qu'il garantisse « l'intégrité, l'intangibilité et la
sécurité des données enregistrées » (art. R321-6-1). Or un registre qui lit
la fiche contact en direct change quand la fiche change : renommer un vendeur
ou corriger son adresse réécrit rétroactivement toutes ses ventes passées,
sans trace et sans intention. Ce n'est pas une faille de sécurité, c'est une
lecture — et c'est justement ce qu'un registre ne doit pas faire.

La seconde est le numéro d'ordre. « Chaque objet exposé à la vente ou détenu
en stock est affecté d'un numéro d'ordre. […] Le numéro d'ordre est porté sur
le registre et figure de manière apparente sur chaque objet ou lot d'objets »
(art. R321-4). Un numéro continu suppose une suite, donc des enregistrements
qui existent par eux-mêmes — pas une vue calculée sur des avoirs qu'on peut
annuler.

D'où ce modèle : une **copie**, écrite à la comptabilisation de l'avoir, qui
ne relit plus rien ensuite. Les colonnes suivent le modèle officiel du
registre (arrêté du 15 mai 2020, annexe I) dans son ordre, puis viennent les
mentions propres aux métaux précieux (CGI, ann. IV, art. 56 J quindecies) que
ce modèle-là ne porte pas : le poids, le titre et la date de sortie.

La maille est le **lot**, non l'objet : l'art. R321-4 admet « un numéro
d'ordre commun » et un numéro « apparent sur chaque objet **ou lot
d'objets** ». Un sachet de 34,3 g d'or 18k est un lot ; une ligne d'avoir en
est un. En contrepartie, le comptoir doit porter le numéro sur le sachet.

Une inscription ne se modifie pas. « Les modifications éventuelles doivent
être justifiées par création d'un nouvel enregistrement informatique avec
indication de son motif » (CGI, ann. IV, art. 56 J sexdecies, 1° c) — et le
2° c, celui des ouvrages d'occasion, exige que les enregistrements « ne
puissent être modifiés que par création d'un nouvel enregistrement avec
indication de son motif ». Une rectification est donc une **inscription de
plus**, qui porte son motif et renvoie à celle qu'elle corrige ; l'originale
reste lisible, telle qu'elle a été écrite.

Ce module-ci pose le registre et son affichage. Ce qu'il ne pose pas encore,
et qui viendra :

* la page quotidienne et son chiffre de contrôle chaîné ;
* l'édition quotidienne, qui reprendra les intitulés officiels du modèle ;
* le journal des consultations (arrêté du 15 mai 2020, art. 3, 2°).

Les libellés de colonnes employés ici sont des libellés d'écran, en français
courant. Les intitulés exacts du modèle officiel — majuscules et ponctuation
comprises — n'entreront qu'avec l'édition imprimée, une fois relus sur
l'annexe.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class LivrePoliceLigne(models.Model):
    _name = 'livre.police.ligne'
    _description = "Livre de police - ligne du registre"
    # Le registre se lit dans l'ordre où il s'écrit, société par société.
    _order = 'company_id, numero_ordre'
    _rec_name = 'numero_ordre'

    # -- colonne 1 : le numéro d'ordre ------------------------------------
    sens = fields.Selection(
        [('entree', "Entrée"), ('sortie', "Sortie")],
        string="Sens", required=True, default='entree', readonly=True,
        index=True,
        help="Le registre des métaux précieux réclame « la date d'entrée et "
             "de sortie » (CGI, ann. IV, art. 56 J quindecies). Une sortie ne "
             "modifie pas l'entrée — rien ne se modifie ici — elle s'inscrit "
             "à sa suite et s'y rattache.",
    )
    entree_id = fields.Many2one(
        'livre.police.ligne', string="Sort de l'inscription", readonly=True,
        index=True, ondelete='restrict',
        help="L'inscription d'entrée dont ce métal provient. Un lot peut "
             "sortir en plusieurs fois : chaque départ a sa propre "
             "inscription, et toutes désignent la même entrée.",
    )
    sortie_ids = fields.One2many(
        'livre.police.ligne', 'entree_id', string="Sorties", readonly=True,
    )
    numero_ordre = fields.Char(
        string="N° d'ordre", required=True, index=True, readonly=True,
        help="Numéro continu, propre à chaque société. Il doit figurer de "
             "manière apparente sur le lot lui-même (art. R321-4 du code "
             "pénal) : c'est lui qui relie l'objet au registre.",
    )

    # -- colonne 2 : la date ----------------------------------------------
    date_achat = fields.Date(
        string="Date de l'achat", required=True, index=True, readonly=True,
        help="Date de l'opération, telle que la porte l'avoir.",
    )

    # -- colonne 3 : description et provenance ----------------------------
    # Le texte tient les deux dans la même phrase (art. R321-3 3°) et le
    # modèle officiel dans la même colonne. Elles restent deux champs : elles
    # ne se saisissent pas au même endroit et ne manquent pas de la même
    # façon (voir le manifeste).
    description = fields.Text(
        string="Description de l'objet", readonly=True,
        help="Description précise des objets, telle qu'elle a été recueillie "
             "au comptoir sur la ligne de l'avoir.",
    )
    provenance = fields.Char(
        string="Provenance", readonly=True,
        help="Provenance déclarée par le vendeur, recopiée à l'inscription. "
             "Renommer l'entrée du référentiel ne la changera plus ici.",
    )

    # -- colonne 4 : le vendeur -------------------------------------------
    vendeur_nom = fields.Char(
        string="Nom du vendeur", index=True, readonly=True,
        help="Nom, prénom ou dénomination sociale du vendeur au jour de "
             "l'opération.",
    )
    vendeur_qualite = fields.Char(
        string="Qualité ou profession", readonly=True,
    )
    vendeur_domicile = fields.Text(
        string="Domicile ou siège social", readonly=True,
    )
    representant_nom = fields.Char(
        string="Représentant", readonly=True,
        help="Personne physique qui s'est présentée au nom d'une société "
             "(art. R321-3 2° du code pénal). Vide pour un particulier.",
    )
    representant_qualite = fields.Char(
        string="Qualité du représentant", readonly=True,
    )

    # -- colonne 5 : la pièce d'identité -----------------------------------
    piece_nature = fields.Char(string="Nature de la pièce", readonly=True)
    piece_numero = fields.Char(string="N° de la pièce", readonly=True)
    piece_autorite = fields.Char(string="Autorité de délivrance", readonly=True)
    piece_delivrance = fields.Date(string="Date de délivrance", readonly=True)

    # -- colonne 6 : le prix et le règlement -------------------------------
    prix = fields.Monetary(
        string="Prix d'achat", currency_field='currency_id', readonly=True,
        help="Montant effectivement versé au vendeur, taxe sur les métaux "
             "précieux déduite lorsqu'elle s'applique.",
    )
    currency_id = fields.Many2one('res.currency', readonly=True)
    mode_reglement = fields.Char(
        string="Mode de règlement", readonly=True,
        help="Chèque barré ou virement, convenu au comptoir et porté sur le "
             "devis de rachat.\n\n"
             "La mention se recueille avant l'opération, et non après le "
             "paiement : c'est ainsi qu'elle est connue à l'inscription, et "
             "que le registre n'a jamais à être complété ensuite."
    )

    # -- colonne 7 : la protection au titre du code du patrimoine ----------
    protection_patrimoine = fields.Char(
        string="Protection (code du patrimoine)", readonly=True,
        help="Le cas échéant, mesure de protection du bien culturel. Sans "
             "objet pour un rachat de métal au poids.",
    )

    # -- mentions propres au registre des métaux précieux -------------------
    # « la nature, le nombre, le poids, le titre, la date d'entrée et de
    # sortie et l'origine » (CGI, ann. IV, art. 56 J quindecies).
    metal_nature = fields.Char(string="Nature du métal", readonly=True)
    quantite = fields.Float(
        # Une colonne ne s'additionne que si sa somme veut dire quelque
        # chose. Celle-ci mêle des pièces et des grammes selon l'article :
        # leur total n'est ni un poids ni un nombre d'objets. Le poids et le
        # prix, eux, s'additionnent.
        string="Quantité", digits=(12, 4), readonly=True, aggregator=False,
        help="Quantité portée sur la ligne. Selon l'article, elle compte des "
             "pièces ou des grammes — la colonne « Régime » dit lequel, car "
             "un poids saisi au gramme n'est pas un nombre d'objets.",
    )
    regime_quantite = fields.Char(string="Régime", readonly=True)
    poids = fields.Float(
        string="Poids (g)", digits=(12, 4), readonly=True,
    )
    titre = fields.Float(
        # Odoo somme les nombres par défaut dans un regroupement. Additionner
        # des millièmes ne produit rien : 750 + 900 + 999 n'est pas un titre.
        string="Titre (millièmes)", digits=(5, 1), readonly=True,
        aggregator=False,
    )
    titre_lot = fields.Boolean(
        string="Lot de titres", readonly=True,
        help="L'article désignait un ensemble de titres différents, dont "
             "aucun titre unique ne serait exact.",
    )
    titre_texte = fields.Char(
        string="Titre", compute='_compute_titre_texte',
        help="Le titre tel qu'il se lit au registre : le nombre de millièmes "
             "quand il y en a un, « lot de titres » quand l'article n'en "
             "porte pas, et rien du tout sinon.",
    )
    date_mouvement = fields.Date(
        string="Date du mouvement", readonly=True,
        help="La date du départ, sur une inscription de sortie. Une entrée "
             "porte sa date à la colonne « date de l'achat ».",
    )
    poids_sorti = fields.Float(
        string="Poids sorti (g)", digits=(12, 4), readonly=True,
        compute='_compute_sorties', aggregator=False,
    )
    poids_restant = fields.Float(
        string="Poids restant (g)", digits=(12, 4), readonly=True,
        compute='_compute_sorties', aggregator=False,
        help="Ce qui n'est pas encore reparti. Tant qu'il en reste, le numéro "
             "d'ordre doit demeurer apparent sur le métal en stock (c. pén., "
             "art. R321-4).",
    )
    etat_sortie = fields.Selection(
        [('en_stock', "En stock"),
         ('partiel', "Sorti en partie"),
         ('sorti', "Sorti")],
        string="État", readonly=True, compute='_compute_sorties',
        search='_search_etat_sortie',
        help="Où en est ce numéro d'ordre. « Sorti en partie » est le cas "
             "qu'aucune date ne sait dire : du métal est parti, il en reste, "
             "et le numéro doit demeurer apparent sur ce qui reste (c. pén., "
             "art. R321-4).",
    )
    date_sortie = fields.Date(
        string="Date de sortie", readonly=True, compute='_compute_sorties',
        help="La date à laquelle l'inscription s'est vidée. Elle reste vide "
             "tant qu'il reste du métal : un lot sorti pour moitié n'est pas "
             "sorti. Le détail des départs successifs figure aux inscriptions "
             "de sortie, chacune sous son propre numéro d'ordre.\n\n"
             "Calculée, et hors du chiffre de contrôle : une inscription ne "
             "se réécrit pas, et celle-ci changerait après coup.",
    )

    # -- rattachements et traçabilité --------------------------------------
    company_id = fields.Many2one(
        'res.company', string="Société", required=True, index=True,
        readonly=True,
    )
    move_id = fields.Many2one(
        'account.move', string="Avoir", readonly=True, index=True,
        ondelete='restrict',
    )
    move_line_id = fields.Many2one(
        'account.move.line', string="Ligne de l'avoir", readonly=True,
        index=True, ondelete='restrict',
    )
    mouvement_stock_id = fields.Many2one(
        'stock.move.line', string="Mouvement de sortie", readonly=True,
        index=True, ondelete='restrict',
        help="Le départ de stock qui a produit cette inscription de sortie.",
    )
    facture_vente_ids = fields.Many2many(
        'account.move', string="Factures de vente", readonly=True,
        compute='_compute_facture_vente_ids',
        help="Les factures qui ont accompagné ce départ. Elles ne sont pas "
             "une mention du registre — ni le prix de revente ni l'acheteur "
             "n'y figurent — mais elles disent où retrouver la pièce "
             "justificative, que le I de l'art. L102 B du LPF fait conserver.",
    )

    @api.depends('mouvement_stock_id')
    def _compute_facture_vente_ids(self):
        """Retrouve la facture par le chemin de la marchandise.

        Calculé, et non figé à l'inscription : la livraison précède souvent la
        facturation, et une inscription ne se réécrit pas. Le lien apparaît
        donc le jour où la facture existe, sans que rien du registre n'ait
        bougé — et il reste, pour la même raison, hors du chiffre de contrôle.
        """
        for ligne in self:
            vente = ligne.mouvement_stock_id.move_id.sale_line_id
            ligne.facture_vente_ids = vente.invoice_lines.move_id

    contrepartie_nom = fields.Char(
        string="Vendeur ou acheteur", compute='_compute_contrepartie',
        help="Qui est en face. Le registre n'inscrit que le vendeur ; sur "
             "une sortie, cette colonne lit le client de la facture de "
             "vente. C'est un confort d'écran, pas une mention du registre.",
    )
    contrepartie_qualite = fields.Char(
        string="Qualité de la contrepartie", compute='_compute_contrepartie',
    )
    contrepartie_domicile = fields.Text(
        string="Domicile ou siège de la contrepartie",
        compute='_compute_contrepartie',
    )

    @api.depends('sens', 'vendeur_nom', 'vendeur_qualite', 'vendeur_domicile',
                 'facture_vente_ids')
    def _compute_contrepartie(self):
        """Qui est en face, dans un sens comme dans l'autre.

        L'acheteur n'est une mention d'aucun des deux registres — ni le
        modèle officiel (c. pén., art. R321-3), ni les colonnes propres aux
        métaux (CGI, ann. IV, art. 56 J quindecies) ne demandent à qui l'on
        revend. Une sortie laisse donc ses colonnes de vendeur vides, et
        l'écran ne dit plus où le métal est parti, alors que la facture le
        sait.

        Ces trois lectures comblent l'écran sans rien inscrire : calculées,
        hors du chiffre de contrôle, et l'édition quotidienne continue de ne
        porter que le vendeur.
        """
        for ligne in self:
            if ligne.sens == 'entree':
                ligne.contrepartie_nom = ligne.vendeur_nom
                ligne.contrepartie_qualite = ligne.vendeur_qualite
                ligne.contrepartie_domicile = ligne.vendeur_domicile
                continue
            client = ligne.facture_vente_ids[:1].partner_id
            if not client:
                ligne.contrepartie_nom = False
                ligne.contrepartie_qualite = False
                ligne.contrepartie_domicile = False
                continue
            ligne.contrepartie_nom = client.display_name
            ligne.contrepartie_qualite = (
                client.police_qualite_id.display_name or client.function
                or False)
            ligne.contrepartie_domicile = "\n".join(
                l.strip() for l in
                client._display_address(without_company=True).splitlines()
                if l.strip()) or False
    rectifie_id = fields.Many2one(
        'livre.police.ligne', string="Rectifie l'inscription",
        readonly=True, index='btree_not_null', ondelete='restrict',
        help="Renseigné sur une inscription de rectification. L'inscription "
             "d'origine n'est pas touchée : elle reste lisible telle qu'elle "
             "a été écrite.",
    )
    motif_rectification = fields.Text(
        string="Motif de la rectification", readonly=True,
        help="Pourquoi l'inscription d'origine devait être corrigée. Le "
             "registre ne se modifie que « par création d'un nouvel "
             "enregistrement avec indication de son motif » (CGI, ann. IV, "
             "art. 56 J sexdecies, 2° c).",
    )
    rectifiee_par_ids = fields.One2many(
        'livre.police.ligne', 'rectifie_id', string="Rectifiée par",
        readonly=True,
    )
    rectifiee = fields.Boolean(
        string="Rectifiée", compute='_compute_rectifiee',
        search='_search_rectifiee',
        help="Une inscription postérieure corrige celle-ci. Les deux "
             "demeurent : le registre montre ce qui a été écrit, et ce qui "
             "l'a corrigé.",
    )

    page_id = fields.Many2one(
        'livre.police.page', string="Page", readonly=True, required=True,
        index=True, ondelete='restrict',
        help="Page quotidienne sur laquelle cette inscription est portée. "
             "Elle est fixée à l'inscription : une ligne ne change pas de "
             "page, sinon le chiffre de contrôle de la page ne voudrait plus "
             "rien dire.",
    )
    page_scellee = fields.Boolean(
        related='page_id.scellee', string="Page scellée", readonly=True,
    )

    date_inscription = fields.Datetime(
        string="Inscrit le", required=True, readonly=True,
    )
    inscrit_par_id = fields.Many2one(
        'res.users', string="Inscrit par", required=True, readonly=True,
    )

    _sql_constraints = [
        ('mouvement_stock_unique', 'unique(mouvement_stock_id)',
         "Ce départ de stock est déjà inscrit au registre."),
        ('numero_ordre_unique', 'unique(company_id, numero_ordre)',
         "Deux lignes du registre ne peuvent pas porter le même numéro "
         "d'ordre dans la même société."),
        ('move_line_unique', 'unique(move_line_id)',
         "Cette ligne d'avoir est déjà inscrite au registre."),
    ]

    @api.depends('titre', 'titre_lot')
    def _compute_titre_texte(self):
        """Un titre absent se lit vide, jamais « 0 ».

        Zéro millième, ce serait un métal sans or : la colonne dirait le
        contraire de ce qu'elle veut dire. Un article vendu en lot de titres
        n'en a pas un seul qui soit exact, et le registre le dit avec des
        mots ; un titre simplement inconnu ne dit rien.
        """
        for ligne in self:
            if ligne.titre:
                ligne.titre_texte = "%g" % ligne.titre
            elif ligne.titre_lot:
                ligne.titre_texte = "lot de titres"
            else:
                ligne.titre_texte = False

    @api.depends('sortie_ids.poids', 'sortie_ids.date_mouvement', 'poids',
                 'sens')
    def _compute_sorties(self):
        """Ce qui est reparti, ce qui reste, et le jour où il n'en reste plus.

        Trois lectures d'une même chose, qu'aucune inscription ne porte : le
        registre dit les mouvements, pas leur solde. Le solde se recalcule, et
        c'est pour cela qu'il n'entre pas dans le chiffre de contrôle.
        """
        for ligne in self:
            sorties = ligne.sortie_ids
            ligne.poids_sorti = sum(sorties.mapped('poids'))
            ligne.poids_restant = ligne.poids - ligne.poids_sorti
            dates = [s.date_mouvement for s in sorties if s.date_mouvement]
            solde = ligne.poids_restant <= 0.00005
            ligne.date_sortie = max(dates) if dates and solde else False
            if ligne.sens != 'entree':
                ligne.etat_sortie = False
            elif not sorties:
                ligne.etat_sortie = 'en_stock'
            else:
                ligne.etat_sortie = 'sorti' if solde else 'partiel'

    @api.model
    def _search_etat_sortie(self, operateur, valeur):
        """L'état se recalcule ; il se cherche donc en le recalculant.

        Un solde ne s'exprime pas en domaine SQL — « il en reste » compare une
        somme de sorties au poids d'entrée. On trie donc les entrées en
        mémoire. C'est tenable tant que le registre se compte en milliers de
        lignes ; au-delà, il faudra stocker l'état, et se souvenir qu'il ne
        doit pas entrer dans l'empreinte.
        """
        if operateur not in ('=', '!=', 'in', 'not in'):
            raise UserError(_("L'état de sortie ne se cherche que par égalité."))
        cherches = valeur if isinstance(valeur, (list, tuple)) else [valeur]
        entrees = self.search([('sens', '=', 'entree')])
        retenues = entrees.filtered(lambda l: l.etat_sortie in cherches)
        if operateur in ('!=', 'not in'):
            retenues = entrees - retenues
        return [('id', 'in', retenues.ids)]

    @api.depends('rectifiee_par_ids')
    def _compute_rectifiee(self):
        for ligne in self:
            ligne.rectifiee = bool(ligne.rectifiee_par_ids)

    def _search_rectifiee(self, operator, value):
        if operator not in ('=', '!=') or not isinstance(value, bool):
            raise UserError(_("Filtre non supporté sur « Rectifiée »."))
        rectifiees = self.sudo().search(
            [('rectifie_id', '!=', False)]).rectifie_id
        positif = (operator == '=') == value
        return [('id', 'in' if positif else 'not in', rectifiees.ids)]

    def _empreinte_donnees(self):
        """Ce que le chiffre de contrôle de la page couvre, sur cette ligne.

        Toutes les mentions du registre y entrent, et rien d'autre : ni les
        identifiants techniques, ni les liens vers la comptabilité, qui ne
        sont pas ce que le registre atteste. L'ordre est fixe — un dictionnaire
        sérialisé par clés triées donne la même chaîne à chaque calcul, faute
        de quoi l'empreinte changerait sans que rien n'ait changé.
        """
        self.ensure_one()
        return {
            'numero_ordre': self.numero_ordre,
            'date_achat': fields.Date.to_string(self.date_achat),
            'description': self.description or '',
            'provenance': self.provenance or '',
            'vendeur_nom': self.vendeur_nom or '',
            'vendeur_qualite': self.vendeur_qualite or '',
            'vendeur_domicile': self.vendeur_domicile or '',
            'representant_nom': self.representant_nom or '',
            'representant_qualite': self.representant_qualite or '',
            'piece_nature': self.piece_nature or '',
            'piece_numero': self.piece_numero or '',
            'piece_autorite': self.piece_autorite or '',
            'piece_delivrance': fields.Date.to_string(self.piece_delivrance),
            'prix': '%.2f' % self.prix,
            'mode_reglement': self.mode_reglement or '',
            'protection_patrimoine': self.protection_patrimoine or '',
            'metal_nature': self.metal_nature or '',
            'quantite': '%.4f' % self.quantite,
            'regime_quantite': self.regime_quantite or '',
            'poids': '%.4f' % self.poids,
            'titre': '%.1f' % self.titre,
            'titre_lot': self.titre_lot,
            'sens': self.sens,
            'date_mouvement': fields.Date.to_string(self.date_mouvement),
            'entree': self.entree_id.numero_ordre or '',
            'rectifie': self.rectifie_id.numero_ordre or '',
            'motif_rectification': self.motif_rectification or '',
        }

    # ------------------------------------------------------------------
    # Ce qui est inscrit ne se réécrit pas
    # ------------------------------------------------------------------

    def write(self, vals):
        """Le registre n'accepte aucune modification, d'aucun champ.

        Il n'y a pas d'exception à ménager : toutes les mentions sont connues
        à l'inscription, y compris le mode de règlement, convenu au comptoir
        avant l'opération. Une exception ici serait une exception à expliquer
        devant un contrôle.
        """
        if self:
            raise UserError(_(
                "Une inscription au registre ne se modifie pas.\n\n"
                "« Les enregistrements informatiques créés pour les ouvrages "
                "d'occasion ne peuvent être modifiés que par création d'un "
                "nouvel enregistrement avec indication de son motif » (CGI, "
                "ann. IV, art. 56 J sexdecies, 2° c).\n\n"
                "Utilisez le bouton « Rectifier » : l'inscription d'origine "
                "reste, et la correction s'inscrit à sa suite en disant "
                "pourquoi.\n\n"
                "Inscription concernée : %(numeros)s",
                numeros=", ".join(self.mapped('numero_ordre'))))
        return super().write(vals)

    def unlink(self):
        """Un registre ne perd pas de ligne : il en gagne.

        Supprimer romprait la suite des numéros d'ordre, que rien ne
        permettrait ensuite de justifier — et c'est précisément la continuité
        qu'un contrôle vérifie.
        """
        if self:
            raise UserError(_(
                "Une inscription au registre ne se supprime pas : elle se "
                "rectifie.\n\n"
                "La suite des numéros d'ordre doit rester continue (c. pén., "
                "art. R321-4). Une ligne manquante ne se justifie pas.\n\n"
                "Inscription concernée : %(numeros)s",
                numeros=", ".join(self.mapped('numero_ordre'))))
        return super().unlink()

    def action_rectifier(self):
        """Ouvre l'assistant de rectification sur cette inscription."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': "Rectifier l'inscription %s" % self.numero_ordre,
            'res_model': 'livre.police.rectification',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_ligne_id': self.id},
        }

    # ------------------------------------------------------------------
    # Inscription
    # ------------------------------------------------------------------

    @api.model
    def _sequence(self, societe):
        """Suite des numéros d'ordre de la société, créée au premier besoin.

        ``no_gap`` verrouille la séquence le temps de la transaction : deux
        comptoirs qui comptabilisent en même temps n'obtiendront pas le même
        numéro, et la suite ne saute pas. Un registre dont la numérotation
        saute se justifie mal devant un contrôle.
        """
        Sequence = self.env['ir.sequence'].sudo()
        suite = Sequence.search([('code', '=', 'livre.police.ligne'),
                                 ('company_id', '=', societe.id)], limit=1)
        if not suite:
            suite = Sequence.create({
                'name': "Livre de police - %s" % societe.name,
                'code': 'livre.police.ligne',
                'company_id': societe.id,
                'implementation': 'no_gap',
                'padding': 6,
                'number_next': 1,
            })
        return suite

    @api.model
    def _valeurs_depuis_ligne(self, ligne):
        """Copie figée d'une ligne d'avoir, au moment où elle est inscrite."""
        piece = ligne.move_id
        personne = piece._police_personne()
        vendeur = piece.partner_id
        representant = piece.police_representant_id
        produit = ligne.product_id.product_tmpl_id

        # La nature de la pièce d'identité est une sélection : on inscrit son
        # libellé, pas sa clé technique. Un registre se lit sans le code.
        natures = dict(
            personne._fields['id_doc_type'].selection) if personne else {}
        regimes = dict(
            produit._fields['metal_quantity_mode'].selection) if produit else {}
        reglements = dict(piece._fields['police_reglement'].selection)

        return {
            'date_achat': piece.invoice_date or piece.date,
            'description': ligne._police_description(),
            'provenance': ligne.police_origin_id.display_name or False,
            'vendeur_nom': vendeur.display_name,
            'vendeur_qualite': (personne.police_qualite_id.display_name
                                or False),
            'vendeur_domicile': "\n".join(
                l.strip() for l in
                vendeur._display_address(without_company=True).splitlines()
                if l.strip()) or False,
            # `name`, non `display_name` : celui d'un contact rattaché
            # reprend la société, déjà nommée dans la colonne du vendeur.
            'representant_nom': representant.name or False,
            'representant_qualite': representant.function or False,
            'piece_nature': natures.get(personne.id_doc_type) or False,
            'piece_numero': personne.id_doc_number or False,
            'piece_autorite': personne.id_doc_authority or False,
            'piece_delivrance': personne.id_doc_issue_date or False,
            # `price_total`, et non `price_subtotal` : la taxe sur les
            # métaux précieux est retenue sur le prix (taxe négative, incluse
            # dans le prix, en mode « division »). Le sous-total reconstitue
            # un montant avant retenue que personne n'a versé ; le registre
            # doit porter ce que le vendeur a reçu.
            'prix': abs(ligne.price_total),
            'currency_id': piece.currency_id.id,
            'mode_reglement': reglements.get(piece.police_reglement) or False,
            'metal_nature': produit.metal_nature.display_name or False,
            'quantite': ligne.quantity,
            'regime_quantite': regimes.get(produit.metal_quantity_mode) or False,
            'poids': ligne.metal_weight,
            'titre': produit.metal_fineness,
            'titre_lot': produit.metal_mixed_fineness,
            'company_id': piece.company_id.id,
            'move_id': piece.id,
            'move_line_id': ligne.id,
            'page_id': self.env['livre.police.page']._page_courante(
                piece.company_id).id,
            'date_inscription': fields.Datetime.now(),
            'inscrit_par_id': self.env.user.id,
        }

    @api.model
    def _inscrire(self, pieces):
        """Inscrit au registre les lignes des pièces qui y entrent.

        Appelé après la comptabilisation, jamais avant : tant que l'avoir est
        au brouillon il n'a ni numéro ni date arrêtée, et le comptoir peut
        encore le reprendre. Une pièce déjà inscrite ne l'est pas deux fois —
        une contrainte d'unicité le garantit, mais on évite d'y arriver.
        """
        a_inscrire = pieces.invoice_line_ids.filtered('police_origin_required')
        deja = self.sudo().search(
            [('move_line_id', 'in', a_inscrire.ids)]).move_line_id
        a_inscrire -= deja
        if not a_inscrire:
            return self.browse()

        valeurs = []
        # L'ordre d'inscription suit celui des lignes de la pièce : deux
        # objets rachetés ensemble se suivent au registre.
        for ligne in a_inscrire.sorted(lambda l: (l.move_id.id, l.sequence, l.id)):
            vals = self._valeurs_depuis_ligne(ligne)
            vals['numero_ordre'] = self._sequence(
                ligne.move_id.company_id).next_by_id()
            valeurs.append(vals)
        return self.sudo().create(valeurs)

    @api.model
    def _valeurs_depuis_sortie(self, entree, mouvement):
        """Fige ce qu'une sortie inscrit.

        Elle ne recopie de l'entrée que ce qui décrit la marchandise : la
        nature du métal, son titre, les objets. Le vendeur, sa pièce
        d'identité, le prix d'achat n'ont rien à faire là — ils appartiennent
        à l'entrée, qui reste, et les répéter donnerait à croire qu'une
        seconde opération a eu lieu avec la même personne.

        L'acheteur n'y figure pas davantage. Le registre des objets mobiliers
        décrit l'entrée (c. pén., art. R321-3) et le registre des métaux
        réclame les dates d'entrée et de sortie (CGI, ann. IV, art. 56 J
        quindecies) : aucun des deux ne demande à qui l'on revend. Cela vit
        dans la facturation, que l'art. L102 B du LPF fait conserver.
        """
        quantite = mouvement.quantity
        # Le poids suit la quantité : un lot homogène sorti pour un tiers
        # laisse deux tiers de son poids. Sur les articles pesés au gramme,
        # les deux se confondent.
        poids = (entree.poids * quantite / entree.quantite) if entree.quantite else 0.0
        return {
            'sens': 'sortie',
            'entree_id': entree.id,
            # La date de l'achat est reprise de l'entrée : c'est bien ce
            # jour-là que ce métal a été acheté, et la colonne du modèle
            # officiel la réclame sur chaque ligne. La date du départ, elle,
            # se lit à la colonne « sortie ».
            'date_achat': entree.date_achat,
            'date_mouvement': fields.Datetime.context_timestamp(
                mouvement, mouvement.date).date(),
            'description': entree.description,
            'metal_nature': entree.metal_nature,
            'quantite': quantite,
            'regime_quantite': entree.regime_quantite,
            'poids': poids,
            'titre': entree.titre,
            'titre_lot': entree.titre_lot,
            'prix': 0.0,
            'currency_id': entree.currency_id.id,
            'company_id': mouvement.company_id.id,
            'mouvement_stock_id': mouvement.id,
            'page_id': self.env['livre.police.page']._page_courante(
                mouvement.company_id).id,
            'date_inscription': fields.Datetime.now(),
            'inscrit_par_id': self.env.user.id,
        }

    @api.model
    def _inscrire_sorties(self, transferts):
        """Inscrit le métal qui s'en va, lot par lot.

        Un lot sort en une ou plusieurs fois. Chaque départ prend son propre
        numéro d'ordre dans la suite de l'agence : la série est continue, et
        c'est cette continuité que le contrôle d'intégrité vérifie.

        Le lot porte le numéro d'ordre de son entrée — c'est tout ce qu'il
        faut pour retrouver d'où le métal vient.
        """
        departs = transferts.move_line_ids.filtered(
            lambda ml: ml.state == 'done' and ml.lot_id
            and ml.move_id.picking_code == 'outgoing')
        deja = self.sudo().search(
            [('mouvement_stock_id', 'in', departs.ids)]).mouvement_stock_id
        departs -= deja
        if not departs:
            return self.browse()

        valeurs = []
        for mouvement in departs.sorted('id'):
            entree = self.sudo().search([
                ('sens', '=', 'entree'),
                ('numero_ordre', '=', mouvement.lot_id.name),
                ('company_id', '=', mouvement.company_id.id),
            ], limit=1)
            if not entree:
                # Un lot qui ne vient pas du registre — du stock antérieur,
                # un article hors champ. On ne devine pas une entrée.
                continue
            vals = self._valeurs_depuis_sortie(entree, mouvement)
            vals['numero_ordre'] = self._sequence(
                mouvement.company_id).next_by_id()
            valeurs.append(vals)
        return self.sudo().create(valeurs) if valeurs else self.browse()
