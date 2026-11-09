{
    "name": "Numero de cheque sur les paiements",
    "summary": "Demande le numero du cheque a l'enregistrement d'un paiement "
               "et l'imprime sur la facture soldee.",
    "description": """
Pourquoi
========

Odoo n'a pas de champ pour le numero d'un cheque recu ou remis a la main :
celui de l'impression des cheques ne sert qu'aux cheques qu'Odoo imprime.
Le numero restait donc hors du logiciel, et la facture soldee ne disait pas
par quel cheque elle l'avait ete.

Ce que fait le module
=====================

- Une case **« Journal de cheques »** sur les journaux de banque.
- Sur un tel journal, l'enregistrement d'un paiement demande le
  **« N° de cheque »**, obligatoire ; il est recopie dans le memo.
- Le numero s'imprime sur la facture ou l'avoir solde, a cote de la date de
  paiement : « Paye le 05/11/2026 par cheque n° 1234567 ».
- Il se cherche et s'affiche dans la liste des paiements.

Mise en place
=============

Cocher « Journal de cheques » sur chaque journal de banque qui recoit ou
emet des cheques (Comptabilite > Configuration > Journaux).

Limite
======

Quand plusieurs pieces sont reglees en une saisie mais en paiements
separes, la fenetre ne demande pas de numero : ce sont plusieurs cheques. Le
numero se saisit alors sur chaque paiement.
    """,
    "version": "18.0.1.0.0",
    "category": "Accounting/Accounting",
    "author": "Qalisa",
    "website": "https://odoo-docs.qalisa.fr/",
    "license": "AGPL-3",
    "depends": ["account"],
    "data": [
        "views/account_cheque_number_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
}
