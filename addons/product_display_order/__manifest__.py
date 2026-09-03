{
    "name": "Articles - Ordre d'affichage choisi",
    "summary": "Réveille le champ « séquence » de l'article, qu'Odoo déclare "
               "sans s'en servir, et pose une poignée de glisser-déposer.",
    "description": """
Pourquoi
========

L'ordre alphabétique ne dit rien d'un catalogue de métaux. Il éparpille les
lingots entre les pièces, ignore les tailles et les familles, et place
« 100 FRANCS OR » avant « 10 DOLLARS OR » — la collation de PostgreSQL ignore
l'espace, elle compare ``100FRANCSOR`` à ``10DOLLARSOR``. Le comptoir, lui, a
un ordre en tête : les lingots du plus gros au plus petit, puis les pièces
françaises, puis les étrangères.

Odoo trie les articles sur ``is_favorite desc, name`` — donc sur le nom seul
dès lors que les favoris ne départagent rien, ce qui est le cas quand tout le
catalogue est en favori.

Ce que fait le module
=====================

Le module ``product`` déclare pourtant, sur l'article, un champ ``sequence``
dont l'aide annonce « donne l'ordre d'affichage dans une liste d'articles ».
Colonne réelle, valeur 1 par défaut — et aucun tri ne s'en sert. Il n'apparaît
dans aucune vue de l'article, et aucun module de la distribution ne le réveille.

Ce module lui rend son office :

- la séquence passe en tête du tri des articles et des variantes, les favoris
  et le nom demeurant derrière comme départage ;
- une poignée de glisser-déposer est posée sur deux listes — Inventaire /
  Analyse / Stock, et Ventes / Articles ;
- sur l'écran de stock, la colonne « Article » cesse d'afficher ``display_name``
  au profit de ``name``. La valeur est la même tant qu'aucun article ne porte
  de référence interne, mais ``display_name`` se calcule à la volée : Odoo ne
  rend un en-tête cliquable que pour un champ qu'il sait traduire en SQL, et
  cette colonne-là ne se triait donc pas.

L'ordre ainsi rangé vaut partout : listes, sélecteurs d'une ligne de devis,
rapports qui n'imposent pas leur propre tri.

À l'installation, rien ne bouge
===============================

Toutes les séquences valent 1 tant que personne n'a rien rangé : le tri
retombe sur les favoris puis le nom, c'est-à-dire l'ordre d'avant. L'affichage
ne change qu'au premier glisser-déposer.

Ce qu'il faut savoir
====================

**La séquence appartient au modèle d'article, pas à la variante.** Ranger une
variante range ses sœurs. Un catalogue sans variantes multiples ne voit jamais
la différence.

**Tout ne se trie pas.** ``qty_available`` — la quantité en stock — se
calcule à partir du contexte : établissements cochés, entrepôt, date. Aucune
colonne de base ne peut l'exprimer, donc aucun tri ne peut s'y appliquer, et
il en va de même de tout ce qui en découle. Se trient en revanche l'article,
la catégorie, la référence interne, le poids unitaire et la séquence.

**Le champ est emprunté à Odoo.** Il est déclaré mais inutilisé dans la
version 18 ; rien ne garantit qu'une version suivante le conserve. S'il
disparaissait, la poignée disparaîtrait avec lui et l'ordre retomberait sur le
nom — aucune donnée perdue, mais l'ordre choisi ne s'appliquerait plus. Le
remplacer alors par un champ à nous serait le même travail.
    """,
    "version": "18.0.1.1.0",
    "category": "Sales/Sales",
    "author": "Qalisa",
    "website": "https://odoo-docs.qalisa.fr/",
    "license": "AGPL-3",
    "depends": ["product", "stock"],
    "data": [
        "views/product_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
