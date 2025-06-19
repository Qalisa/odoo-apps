{
    'name': "Numismatique - Rapports de Taxes",
    'category': "Accounting/Taxes",
    'summary': "Permet la génération de rapports de taxes pour aider à la saisie des documents Cerfa",
    'description': "Permet la génération de rapports de taxes pour aider à la saisie des documents Cerfa",
    'author': "Qalisa",
    'website': "https://odoo-docs.qalisa.fr/",
    'license': "AGPL-3",
    'version': "1.1.2",
    'depends': ['account'],
    'data': [
        'security/ir.model.access.csv',
        'views/cerfa_report_wizard.xml',
        'views/menu.xml',
        'views/cerfa_report_action.xml',
        'reports/report_2091_sd.xml',
        'views/settings.xml'
    ],
    'installable': True,
    'application': True, 
    'auto_install': False, 
    'external_dependencies': {
        'python': [],
    },
    'images': ['static/description/icon.png'],
    'odoo_version': '18.0', # Ceci n'est pas un paramètre standard, mais peut être utile pour indiquer la version
}