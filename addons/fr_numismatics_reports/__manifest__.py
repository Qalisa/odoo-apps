{
    'name': "Numismatique - Rapports de Taxes",
    'category': "Accounting/Taxes",
    'summary': "Permet la génération de rapports de taxes pour aider à la saisie des documents Cerfa",
    'description': "Permet la génération de rapports de taxes pour aider à la saisie des documents Cerfa",
    'author': "Qalisa",
    'website': "https://www.qalisa.fr",
    'license': "AGPL-3",
    'version': "1.0.0",
    'depends': ['l10n_fr_account'],
    'data': [
        'report/report_2091_sd.xml',
        'views/menu.xml',
        'views/financial_report.xml',
        'wizard/account_report_common_view.xml',
        'wizard/tax_report.xml'
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