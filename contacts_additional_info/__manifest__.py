# -*- coding: utf-8 -*-

{
    'name': 'Contacts - Informations Supplémentaires',
    'version': '1.0',
    'summary': 'Ajoute des informations supplémentaires aux contacts',
    'description': """
Champs Supplémentaires pour Contacts
====================================
Ce module ajoute les champs suivants aux contacts:
- Date de Naissance
- Lieu de Naissance
- Numéro CNI (Carte Nationale d'Identité)

Ces informations sont également affichées sur les avoirs, factures et commandes.
    """,
    'category': 'Contacts',
    'author': 'Qalisa',
    'website': 'https://www.qalisa.fr',
    'depends': ['base', 'contacts'],
    'data': [
        # 'views/report_views.xml',
        'views/views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}