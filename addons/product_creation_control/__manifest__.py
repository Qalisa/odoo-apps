{
    "name": "Articles - Pas de création à la volée",
    "summary": "Supprime la création d'articles depuis les lignes de devis, de "
               "facture et d'avoir. Activable ou non depuis les paramètres.",
    "description": """
Pourquoi
========

Un article n'est pas une simple ligne de catalogue : dès lors qu'il s'agit d'un
bien, il porte les mentions exigées par le livre de police (nature, description,
art. R321-3 3° du code pénal) et par le registre des métaux précieux (nature du
métal, titre, poids, art. 56 J quindecies de l'annexe IV au CGI). Aucune de ces
mentions ne peut être saisie depuis la combobox d'un devis ou d'un avoir, où
seul le nom est renseigné : un article créé à la volée naît incomplet, et c'est
la ligne du registre qui s'en trouve fautive.

Ce que fait le module
=====================

Une fois installé, et tant que l'option reste décochée :

- les entrées « Créer "…" » et « Créer et modifier… » disparaissent des lignes
  de devis, de facture et d'avoir ;
- ``name_create`` est refusé côté serveur pour ``product.template`` et
  ``product.product``, ce qui couvre aussi les autres écrans et les imports.

Un article se crée alors depuis sa fiche complète (Ventes ▸ Articles), où les
contraintes de complétude s'appliquent.

Réglage
=======

Ventes ▸ Configuration ▸ Paramètres ▸ Catalogue de produits ▸ « Autoriser la
création d'articles à la volée ». Décoché par défaut. Cocher la case réactive
le comportement standard d'Odoo ; les utilisateurs déjà connectés doivent
recharger leur page pour que les vues soient reprises.

Rappel : ce module dit *comment* un article se crée, pas *qui* peut le créer.
Le second point relève des habilitations (groupe Comptabilité ▸ Administrateur,
Ventes ▸ Administrateur, Inventaire ▸ Administrateur et « Création de produits »,
qui accordent chacun le droit de création).
""",
    "version": "18.0.1.0.0",
    "author": "Qalisa",
    "depends": ["sale", "account"],
    "license": "AGPL-3",
    "website": "https://odoo-docs.qalisa.fr/",
    "category": "Sales/Sales",
    "data": [
        "views/sale_order_views.xml",
        "views/account_move_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
