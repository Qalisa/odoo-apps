# -*- coding: utf-8 -*-

{
    'name': "Livre de police - metaux precieux",
    'version': '18.0.1.0.0',
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

Deux mentions, une seule case
-----------------------------

L'article R321-3 3° tient la provenance et la description dans la même
phrase, et le modèle officiel du registre dans la même colonne. Elles sont
donc exigées ensemble, par la même case sur la fiche de l'article.

La description se met là où le comptoir la met déjà (voir plus bas). La
provenance ne s'écrit nulle part aujourd'hui : elle prend une colonne, remplie
depuis une liste administrable — « Bijoux personnels », « Héritage ou
succession », « Achat antérieur »… Le comptoir peut en créer une à la volée,
mais pas une simple variante d'écriture d'une valeur existante : « héritage »
serait renvoyé vers « Héritage ou succession ».

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
""",

    'category': 'Accounting/Localizations',
    'author': 'Qalisa',
    'license': "AGPL-3",
    'website': 'https://odoo-docs.qalisa.fr/',
    'depends': ['sale', 'account'],
    'data': [
        'security/ir.model.access.csv',
        'data/livre_police_provenance_data.xml',
        'views/livre_police_provenance_views.xml',
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
