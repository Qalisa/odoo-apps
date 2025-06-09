{
    'name': "Taxes - TFOP et Plus-values mobilières",
    'category': "Accounting/Taxes",
    'summary': "Localisation Fiscale `France` installée requise ! Taxes, comptes et groupes de taxes pour la gestion de la TFOP et de la TPV",
    'description': """
Ce module crée automatiquement les taxes, comptes et groupes de taxes nécessaires pour gérer la fiscalité 
liée à la revente d'objets précieux en France, selon la législation en vigueur.
    """,
    'author': "Qalisa",
    'website': "https://www.qalisa.fr",
    'license': "AGPL-3",
    'version': "1.1.0",
    'depends': ['l10n_fr_account'],
    'data': ["data/gold_accounts.xml"],
    'post_init_hook': 'create_gold_tax_groups',
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': [],
    },
    'images': ['static/description/icon.png'],
    'odoo_version': '18.0', # Ceci n'est pas un paramètre standard, mais peut être utile pour indiquer la version
}