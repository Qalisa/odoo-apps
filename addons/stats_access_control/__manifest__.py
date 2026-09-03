{
    "name": "Chiffres consolides - acces restreint",
    "summary": "Reserve les ecrans d'analyse — ventes par vendeur, analyse des "
               "factures, tableau de bord — a un groupe dedie.",
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
- Facturation / Tableau de bord.

Les etats comptables ne sont pas touches — bilan, compte de resultat, grand
livre, balances, rapport de taxe, livres de caisse et de banque restent
accessibles a qui tient les comptes. Ce sont des documents de tenue, pas des
statistiques de performance.

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

Les menus vises appartiennent a `sale` et `account` : une mise a jour de ces
modules reecrirait leurs groupes et rendrait les ecrans a tout le monde. Il
faut alors remettre a jour ce module. L'initContainer `upgrade-addons`, qui
met a jour nos modules a chaque demarrage du pod, le ferait de lui-meme.
    """,
    "version": "18.0.1.2.0",
    "category": "Sales/Sales",
    "author": "Qalisa",
    "website": "https://odoo-docs.qalisa.fr/",
    "license": "AGPL-3",
    "depends": ["sale", "account"],
    "data": [
        "security/stats_security.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
}
