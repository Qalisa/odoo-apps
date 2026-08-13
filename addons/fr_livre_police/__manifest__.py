# -*- coding: utf-8 -*-

{
    'name': "Livre de police - registre des métaux précieux",
    'version': '18.0.1.2.0',
    'summary': """
Registre des achats, ventes, réceptions et livraisons de métaux précieux :
entrées depuis les avoirs de rachat, sorties par bon de relève.
""",
    'description': """
Livre de police
===============

Les professionnels des métaux précieux tiennent un registre de leurs achats,
ventes, réceptions et livraisons (art. 537 du CGI, art. 56 J quaterdecies à
56 J octodecies de l'annexe IV). Il indique, par objet ou lot d'objets, la
nature, le nombre, le poids, le titre, **la date d'entrée et de sortie** et
l'origine, afin d'en permettre l'identification individuelle. S'y ajoutent
l'identité du vendeur, le prix d'achat et le mode de règlement
(art. R321-3 à R321-5 du code pénal).

Le registre est donc tenu **par objet**, pas en journal : une même ligne porte
l'entrée et la sortie. Ce module le matérialise sur le lot de stock
(``stock.lot``), qui est déjà l'objet identifié individuellement dans Odoo :

- **numéro d'ordre** attribué par établissement, apparent sur l'objet ou le lot ;
- **entrée** créée à la comptabilisation d'un avoir de rachat, avec le vendeur,
  sa qualité, la provenance déclarée, le prix et le mode de règlement ;
- **sortie** relevée sur le bon de livraison au fondeur ;
- **édition du registre** par établissement, avec les mentions obligatoires.

Deux mentions ne se déduisent d'aucune donnée comptable et sont tenues dans
des référentiels administrables plutôt qu'en texte libre : la **provenance**
de l'objet (art. R321-3 3°) et la **qualité ou profession** du vendeur
(art. R321-3 1°, colonne du modèle officiel fixé par l'arrêté du 15 mai 2020).
Une valeur déjà portée par une ligne du registre ne peut plus être renommée,
seulement archivée : la renommer réécrirait le passé.

Le **mode de règlement** n'est pas saisi mais **repris du paiement lettré**
avec l'avoir. Tant que le rachat n'est pas payé, la ligne figure à l'écran
« Mentions à compléter », qui nomme ce qui manque ; le lettrage la complète,
et le journal chaîné garde trace de la correction.

Rien ne se déclenche tant que la **date de bascule** de la société n'est pas
renseignée : le registre commence à une date choisie, pas à l'installation.
Un établissement principal peut tenir le registre pour ses magasins à
condition de distinguer ce qu'il détient en propre : chaque société a son
entrepôt et sa séquence de numéros d'ordre.
""",

    'category': 'Accounting/Localizations',
    'author': 'Qalisa',
    'license': "AGPL-3",
    'website': 'https://odoo-docs.qalisa.fr/',
    # `contacts_citizenship_id` porte les mentions de la pièce d'identité
    # (nature, numéro, date et lieu de délivrance, autorité) exigées au
    # registre par l'art. R321-4 du code pénal, et dépend lui-même de
    # `partner_firstname` pour l'éclatement nom / prénoms.
    'depends': ['fr_numismatics_metals', 'stock_account',
                'contacts_citizenship_id'],
    'data': [
        'security/ir.model.access.csv',
        'data/livre_police_referentiel_data.xml',
        'views/res_config_settings_views.xml',
        'views/product_views.xml',
        'views/livre_police_referentiel_views.xml',
        'views/res_partner_views.xml',
        'views/account_move_views.xml',
        'views/stock_lot_views.xml',
        'views/livre_police_evenement_views.xml',
        'report/livre_police_report.xml',
        'report/livre_police_templates.xml',
        'wizard/livre_police_ouverture_views.xml',
        'views/menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'fr_livre_police/static/src/css/livre_police.css',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
}
