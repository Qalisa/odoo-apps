# -*- coding: utf-8 -*-

{
    'name': "Numismatique - Caractéristiques métal des articles",
    'version': '18.0.1.1.0',
    'summary': """
Nature, titre et poids unitaire sur les articles ; poids en grammes sur les lignes
d'achat. Socle de données du livre de police (art. 537 du CGI, ann. IV art. 56 J quindecies).
""",
    'description': """
Caractéristiques métal des articles
===================================

Le livre de police exige, pour chaque objet acheté, sa désignation et — pour les
métaux précieux — son poids. Ce module porte ces caractéristiques :

- sur l'article : nature du métal — un référentiel que le client complète
  librement —, titre en millièmes, régime de quantité (au gramme / à la
  pièce / au lot) et poids unitaire en grammes ;
- sur la ligne d'achat : le poids en grammes, déduit de l'article quand c'est
  possible, saisi sinon, et figé dès l'écriture comptabilisée ;
- un écran de contrôle : articles à caractériser, lignes sans poids, et prix
  au gramme constaté pour repérer les saisies aberrantes.

L'article est le référentiel : le module ne contient aucune donnée de
catalogue. L'amorçage des caractéristiques et la reprise des poids sur
l'historique relèvent de scripts de reprise, exécutés une fois.

Seules les cinq natures usuelles — or, argent, platine, palladium, rhodium —
sont créées à l'installation. Elles appartiennent ensuite au client : la
liste se complète, se renomme et s'archive depuis Comptabilité >
Configuration > Métaux précieux, sans qu'une mise à jour du module ne les
réécrive. Aucun cours ni fourchette de prix n'est paramétré : le prix au
gramme se déduit de l'article et de la saisie du vendeur.

La dérivation du poids et le prix au gramme vivent dans ``tools/`` sans
dépendance Odoo, et se testent en isolation ::

    cd addons && python3 -m unittest fr_numismatics_metals.tests.test_metals_tools
""",

    'category': 'Accounting/Localizations',
    'author': 'Qalisa',
    'license': "AGPL-3",
    'website': 'https://odoo-docs.qalisa.fr/',
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'data/metal_nature.xml',
        'views/metal_nature_views.xml',
        'views/product_views.xml',
        'views/account_move_views.xml',
        'views/menu.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
