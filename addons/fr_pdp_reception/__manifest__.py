{
    "name": "Facturation électronique - Réception",
    "summary": "Garde le détail des lignes des factures reçues par la "
               "plateforme agréée.",
    "description": """
Pourquoi
========

Une facture Factur-X ou CII porte, pour chaque ligne, un intitulé et une
description. Odoo 18 ne garde que l'intitulé dès qu'il existe : le détail de la
prestation reste dans le PDF joint et n'atteint pas la ligne de la facture
fournisseur. Odoo a inversé cet ordre à partir de la version saas-19.4
(odoo/odoo#276030), sans le reporter en 18.0.

Ce que fait le module
=====================

Quand une ligne reçue porte les deux, son libellé devient l'intitulé suivi de
la description, à la ligne. Une ligne qui n'en porte qu'un garde celui-là.

À retirer au passage à une version d'Odoo qui intègre la correction.
""",
    "version": "18.0.1.0.0",
    "author": "Qalisa",
    "depends": ["l10n_fr_pdp"],
    "license": "AGPL-3",
    "website": "https://odoo-docs.qalisa.fr/",
    "category": "Accounting/Localizations/EDI",
    "installable": True,
}
