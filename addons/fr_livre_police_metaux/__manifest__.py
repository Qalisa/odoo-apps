# -*- coding: utf-8 -*-

{
    'name': "Livre de police - metaux precieux",
    'version': '18.0.1.2.0',
    'summary': """
Description obligatoire des objets rachetes, article par article.
""",
    'description': """
Livre de police - metaux precieux
=================================

Le registre d'objets mobiliers exige de chaque objet acquis « la nature, la
provenance et la description » (art. R321-3 3° du code pénal). Le modèle
officiel du registre intitule la colonne « DESCRIPTION PRÉCISE de l'objet
(nature, dimensions, style, signature et éventuellement signes distinctifs) et
indication de sa provenance » (arrêté du 15 mai 2020, annexe I, colonne 3).

Cette description n'existe nulle part ailleurs : elle ne se déduit ni de
l'article, ni du montant, ni du poids. Elle se recueille au comptoir, devant
les objets, et une fois le vendeur reparti elle est perdue.

Ce module la rend **obligatoire**, sur les seuls articles qui la réclament.
Le choix se fait article par article, dans sa fiche : un rachat d'or au
gramme désigne des objets à décrire, une remise ou un arrondi n'en désigne
aucun.

Deux mentions, deux portées
---------------------------

L'article R321-3 3° tient la provenance et la description dans la même
phrase, et le modèle officiel du registre dans la même colonne. Elles ne
manquent pourtant pas de la même façon.

La **provenance** n'est jamais donnée par la désignation de l'article : elle
est déclarée par le vendeur, et rien d'autre ne la fournit. Elle est donc due
de **tout article inscrit au registre**, et suit la case « Soumis au livre de
police » de fr_numismatics_metals. Elle ne s'écrit nulle part aujourd'hui :
elle prend une colonne, remplie depuis une liste administrable — « Bijoux
personnels », « Héritage ou succession », « Achat antérieur »… Le comptoir
peut en créer une à la volée, mais pas une simple variante d'écriture d'une
valeur existante : « héritage » serait renvoyé vers « Héritage ou
succession ».

La **description** est déjà donnée par la désignation dès que l'article
désigne un type catalogué : « 20 FRANCS OR » dit la nature, le diamètre, le
millésime et l'effigie mieux qu'une phrase saisie au comptoir. Elle n'est
donc exigée que là où l'article ne dit rien de l'objet — or au gramme, lot de
pièces, argent en vrac — et c'est ce que déclare la case sur la fiche. Elle
se met là où le comptoir la met déjà (voir plus bas).

Une provenance déjà portée par une pièce comptabilisée ne se renomme plus.
Elle s'archive — les pièces passées gardent la leur (art. R321-6 et
R321-6-1).

Le sens de la quantité désigne le rachat
----------------------------------------

Un rachat se saisit ici comme une **ligne de quantité négative** sur un devis :
l'établissement ne vend pas, il achète. Selon le solde du document, cette
ligne devient soit une ligne d'avoir en quantité positive, soit une ligne de
facture en quantité négative. Les deux font entrer un objet, et les deux sont
donc contrôlées.

Une quantité négative sur un avoir, à l'inverse, ne fait entrer aucun objet :
c'est une correction, et elle n'est pas contrôlée.

Pas de champ dédié
------------------

La description se met là où le comptoir la met déjà : dans le champ
« Description » de la ligne, sous la désignation de l'article — « 18k Or
750 ‰(gr) ⏎ 1 BAGUE ». Ce champ est pré-rempli par Odoo avec le nom de
l'article, donc jamais vide : ce qui est contrôlé, c'est ce que le libellé
**ajoute** à cette désignation.

Une ligne renommée sans être décrite ne passe pas : « 20 FRANCS OR
(Non-Scellé) » nomme une variante, il ne désigne aucun objet particulier.

Les deux mentions sont exigées deux fois : à la confirmation du devis et à
la comptabilisation de la pièce. La ligne incomplète passe en rouge pendant
la saisie, pour que le manque se voie avant le refus.

La qualité du vendeur
---------------------

Le registre comporte aussi « les nom, prénoms, qualité et domicile de chaque
personne qui a vendu » (art. R321-3 1°), et « les nom, prénoms, qualité et
domicile du représentant » lorsque le vendeur est une personne morale (2°).
Le modèle officiel intitule la colonne « NOM, PRENOM ou dénomination sociale
du vendeur […], qualité ou profession, domicile ou siège social » (arrêté du
15 mai 2020, annexe I, colonne 2).

Cette qualité prend elle aussi une liste administrable — « Retraité(e) »,
« Salarié(e) », « Gérant(e) »… — et se saisit sur la fiche contact, avec
l'état civil et la pièce d'identité.

**Le champ n'est pas obligatoire.** La mention l'est au registre, le champ ne
l'est pas dans Odoo : rien ne bloque l'enregistrement d'un contact ni la
confirmation d'un devis. C'est un choix d'exploitation — le comptoir doit
pouvoir avancer sur une fiche incomplète — et l'obligation est rappelée sous
le champ, là où la saisie se fait.
""",

    'category': 'Accounting/Localizations',
    'author': 'Qalisa',
    'license': "AGPL-3",
    'website': 'https://odoo-docs.qalisa.fr/',
    # `contacts_citizenship_id` porte deja l'etat civil et la piece
    # d'identite du vendeur : la qualite se saisit dans le meme groupe, au
    # meme moment, et non dans un bloc concurrent.
    # `fr_numismatics_metals` porte « Soumis au livre de police », qui dit
    # quels articles entrent au registre : la provenance suit cette case et
    # n'en reclame pas une seconde.
    'depends': ['sale', 'account', 'contacts_citizenship_id',
                'fr_numismatics_metals'],
    'data': [
        'security/ir.model.access.csv',
        'data/livre_police_provenance_data.xml',
        'data/livre_police_qualite_data.xml',
        'views/livre_police_provenance_views.xml',
        'views/livre_police_qualite_views.xml',
        'views/res_partner_views.xml',
        'views/product_views.xml',
        'views/sale_order_views.xml',
        'views/account_move_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fr_livre_police_metaux/static/src/description_toujours_visible.js',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
