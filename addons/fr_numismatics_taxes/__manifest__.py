{
    'name': "Numismatique - Taxes (TMP, TPV et TFOP)",
    'category': "Accounting/Taxes",
    'summary': "Localisation Fiscale `France` installée requise ! Taxes, comptes et groupes de taxes spécifiques à l'activité numismatique en France",
    'description': """
Ce module crée automatiquement les taxes, comptes et groupes de taxes nécessaires pour gérer la fiscalité 
liée à la revente d'objets précieux en France, selon la législation en vigueur.
    """,
    'author': "Qalisa",
    'website': "https://www.qalisa.fr",
    'license': "AGPL-3",
    'version': "1.2.0",
    'depends': ['l10n_fr_account'],
    'data': [
        "data/account.account.csv",
        "data_gen/account.tax.group.csv",
        "data_gen/account.tax.csv",
        "data_gen/account.tax.repartition.line.csv"
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