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
    'author': 'Votre Nom',
    'website': 'https://www.votresite.com',
    'depends': ['base', 'contacts', 'account', 'sale'],
    'data': [
        'views/report_templates.xml',
        'views/upgraded_views.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}