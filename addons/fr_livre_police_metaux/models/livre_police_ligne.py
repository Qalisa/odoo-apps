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

Ce module-ci pose le registre et son affichage. Ce qu'il ne pose pas encore,
et qui viendra :

* le refus d'écriture et la rectification par nouvel enregistrement motivé ;
* la page quotidienne et son chiffre de contrôle chaîné ;
* l'édition quotidienne, qui reprendra les intitulés officiels du modèle ;
* le journal des consultations (arrêté du 15 mai 2020, art. 3, 2°).

Les libellés de colonnes employés ici sont des libellés d'écran, en français
courant. Les intitulés exacts du modèle officiel — majuscules et ponctuation
comprises — n'entreront qu'avec l'édition imprimée, une fois relus sur
l'annexe.
"""

from odoo import api, fields, models


class LivrePoliceLigne(models.Model):
    _name = 'livre.police.ligne'
    _description = "Livre de police - ligne du registre"
    # Le registre se lit dans l'ordre où il s'écrit, société par société.
    _order = 'company_id, numero_ordre'
    _rec_name = 'numero_ordre'

    # -- colonne 1 : le numéro d'ordre ------------------------------------
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
        help="Renseigné depuis le règlement rapproché de l'avoir. Il est "
             "souvent vide à l'inscription : au comptoir, la pièce se "
             "comptabilise avant que le paiement ne soit saisi.",
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
             "aucun titre unique ne serait exact. Sans cette mention, un "
             "titre à zéro se lirait comme un métal sans or.",
    )
    date_sortie = fields.Date(
        string="Date de sortie", readonly=True,
        help="Le registre des métaux précieux réclame la date d'entrée et de "
             "sortie. Elle ne se remplira que le jour où la sortie du métal "
             "sera saisie — aujourd'hui, la revente au fondeur n'est pas "
             "enregistrée.",
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
    date_inscription = fields.Datetime(
        string="Inscrit le", required=True, readonly=True,
    )
    inscrit_par_id = fields.Many2one(
        'res.users', string="Inscrit par", required=True, readonly=True,
    )

    _sql_constraints = [
        ('numero_ordre_unique', 'unique(company_id, numero_ordre)',
         "Deux lignes du registre ne peuvent pas porter le même numéro "
         "d'ordre dans la même société."),
        ('move_line_unique', 'unique(move_line_id)',
         "Cette ligne d'avoir est déjà inscrite au registre."),
    ]

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

        reglements = piece.matched_payment_ids.mapped(
            lambda p: p.payment_method_line_id.display_name
            or p.journal_id.display_name)

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
            'mode_reglement': ", ".join(sorted(set(reglements))) or False,
            'metal_nature': produit.metal_nature.display_name or False,
            'quantite': ligne.quantity,
            'regime_quantite': regimes.get(produit.metal_quantity_mode) or False,
            'poids': ligne.metal_weight,
            'titre': produit.metal_fineness,
            'titre_lot': produit.metal_mixed_fineness,
            'company_id': piece.company_id.id,
            'move_id': piece.id,
            'move_line_id': ligne.id,
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
