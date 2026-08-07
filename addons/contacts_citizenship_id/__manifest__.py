# -*- coding: utf-8 -*-

{
    'name': "Contacts - Identification civile",
    'version': '1.3.0',
    'summary': """
Ajoute des informations d'état civil aux contacts (naissance structurée, pièce d'identité détaillée),
requises pour le livre de police et la déclaration DMET. Affichées sur les documents générés par Odoo.
""",
    'description': """
Champs Supplémentaires pour Contacts
====================================
Ce module ajoute aux contacts les champs d'état civil suivants:
- Date de naissance
- Naissance structurée : pays, département, code INSEE et libellé de la commune
- Justificatif d'identité détaillé (art. R321-3 du code pénal) :
  nature, numéro, date de délivrance et autorité émettrice

L'éclatement nom / prénom est fourni par la dépendance `partner_firstname` (OCA),
requis pour la déclaration d'achats de métaux (zones vendeur Q 014 / Q 015).

Ces informations sont également affichées sur les avoirs, factures et commandes.
""",
    'category': 'Contacts',
    'author': 'Qalisa',
    'license': "AGPL-3",
    'website': 'https://odoo-docs.qalisa.fr/',
    'depends': ['base', 'contacts', 'partner_firstname'],
    'data': [
        'views/report_views.xml',
        'views/views.xml'
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}