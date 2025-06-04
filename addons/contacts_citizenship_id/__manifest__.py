# -*- coding: utf-8 -*-

{
    'name': "Contacts - Identification civile",
    'version': '1.1.1',
    'summary': """
Ajoute des informations supplémentaires aux contacts (Date et lieu de naissance, Justificatif d'identité),
et les affiche si présents sur les documents générés par Odoo.
""",
    'description': """
Champs Supplémentaires pour Contacts
====================================
Ce module ajoute les champs suivants aux contacts:
- Date de Naissance
- Lieu de Naissance
- Justificatif d'identité (nature, et numéro associé)

Ces informations sont également affichées sur les avoirs, factures et commandes.
""",
    'category': 'Contacts',
    'author': 'Qalisa',
    'license': "AGPL-3",
    'website': 'https://www.qalisa.fr',
    'depends': ['base', 'contacts'],
    'data': [
        'views/report_views.xml',
        'views/views.xml'
    ],
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}