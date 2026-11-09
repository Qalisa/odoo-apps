{
    "name": "Comptabilite de la societe - acces par groupe",
    "summary": "Ferme la comptabilite de la societe a un comptoir qui garde "
               "ses ventes, ses rachats et leurs paiements.",
    "description": """
Pourquoi
========

Un comptoir facture ses ventes et ses rachats : il lui faut le droit
« Comptabilite : Facturation ». Mais ce droit ouvre aussi, dans Odoo, toutes
les pieces de la societe — factures des fournisseurs, ecritures diverses —
et les releves bancaires. Ce sont deux besoins differents.

Le retirer ne tient pas : le droit cache « Technique : Basique » l'implique,
et le remet aussitot.

Ce que fait le module
=====================

Il cree un groupe **« Comptoir sans comptabilite »**. Ses membres gardent le
droit « Facturation », mais ne voient plus que :

- les factures, avoirs et recus **clients** — ventes et rachats ;
- les paiements cote client, et leurs ecritures.

Ils ne voient plus les factures fournisseurs, les ecritures diverses, les
paiements fournisseurs, les releves et lignes bancaires, ni les menus
Fournisseurs, Comptabilite, Rapports et Configuration de la facturation.

Les autres utilisateurs ne sont pas touches.

Mise en place
=============

Pour chaque compte vise : retirer « Technique : Basique » (mode
developpeur, onglet Droits d'acces), garder « Comptabilite : Facturation », et
ajouter « Comptoir sans comptabilite ».

Note technique
==============

Odoo additionne les regles de groupe : une regle restrictive posee sur un
groupe ne retire rien a qui garde « Facturation », dont la regle laisse tout
voir. Les restrictions sont donc des regles **globales**, qui s'appliquent a
tous mais ne filtrent que les membres du groupe. Pour la meme raison, les
menus se masquent par le code : un menu ouvert a un groupe ne se ferme pas a
un autre.
    """,
    "version": "18.0.1.0.0",
    "category": "Accounting/Accounting",
    "author": "Qalisa",
    "website": "https://odoo-docs.qalisa.fr/",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "security/accounting_access_security.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
