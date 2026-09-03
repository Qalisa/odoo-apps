{
    "name": "Ecrans d'analyse - acces par groupe",
    "summary": "Reserve les chiffres consolides — ventes par vendeur, analyse "
               "des factures, valorisation du stock — a un groupe dedie, et "
               "ouvre l'analyse du stock a tout le comptoir.",
    "description": """
Pourquoi
========

Les ecrans d'analyse d'Odoo repondent a des questions que tout le monde n'a
pas a poser : qui a vendu le plus ce mois-ci, combien l'etablissement a
facture, comment se compare un comptoir a l'autre. Ces chiffres consolides
relevent de la direction, pas du poste de vente.

Ce que fait le module
=====================

Il cree un groupe **« Statistiques et chiffres consolides »** et lui reserve
les menus suivants :

- Ventes / Analyse — et ses quatre ecrans : Ventes, Vendeurs, Clients,
  Produits. C'est la que se lit le classement des vendeurs ;
- Facturation / Gestion / Analyse des factures ;
- Facturation / Gestion / Rapport analytique ;
- Facturation / Tableau de bord ;
- Inventaire / Analyse / Valorisation — la valeur en euros du stock detenu.

Les etats comptables ne sont pas touches — bilan, compte de resultat, grand
livre, balances, rapport de taxe, livres de caisse et de banque restent
accessibles a qui tient les comptes. Ce sont des documents de tenue, pas des
statistiques de performance.

Et dans l'autre sens
====================

Le meme raisonnement ouvre un ecran au lieu de le fermer. **Inventaire /
Analyse / Stock** — la liste des articles stockables et de leurs quantites —
est un ecran de travail : savoir ce qu'on a en vitrine n'est pas lire les
chiffres de la maison. Odoo le reserve pourtant a « Inventaire /
Administrateur », droit qui ouvrirait du meme geste la configuration des
entrepots, les emplacements et les regles de reassort.

Le menu parent est donc etendu au simple utilisateur du stock, et
Valorisation en est retiree — c'est un chiffre, pas un etat.

Ce que le module ne fait pas
============================

**Masquer un menu n'est pas une barriere.** Qui detient encore les droits
« Ventes / Administrateur » ou « Comptabilite / Administrateur » peut
retrouver les memes chiffres autrement : en groupant une liste de commandes
par vendeur, en ouvrant une action par son URL, ou en exportant. Le module
retire l'ecran, il ne retire pas la donnee.

Pour une vraie separation, il faut redescendre les droits eux-memes — passer
les vendeurs de « Administrateur » a « Utilisateur : tous les documents »
cote Ventes, et de « Administrateur » a « Facturation » cote Comptabilite.
Cela touche bien d'autres ecrans, et c'est une decision d'exploitation.

Note technique
==============

Les menus vises appartiennent a `sale`, `account`, `stock` et
`stock_account` : une mise a jour de ces modules reecrirait leurs groupes,
et rendrait les ecrans a tout le monde — ou les reprendrait a ceux a qui on
vient de les ouvrir. Il faut alors remettre a jour ce module. L'initContainer `upgrade-addons`, qui
met a jour nos modules a chaque demarrage du pod, le ferait de lui-meme.
    """,
    "version": "18.0.1.3.0",
    "category": "Sales/Sales",
    "author": "Qalisa",
    "website": "https://odoo-docs.qalisa.fr/",
    "license": "AGPL-3",
    "depends": ["sale", "account", "stock", "stock_account"],
    "data": [
        "security/stats_security.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
