{
    'name': "Forcer la langue française",
    'summary': "Force la langue française comme langue par défaut pour les utilisateurs et les sociétés.",
    'description': "Force la langue française comme langue par défaut pour les utilisateurs et les sociétés.",
    'author': "Qalisa",
    'website': "https://www.qalisa.fr",
    'license': "AGPL-3",
    'version': "1.0.0",
    'depends': ['l10n_fr'],
    'data': [
        'data/company_settings.xml'
    ],
    'post_init_hook': 'post_configure_french_lang',
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': [],
    },
    'odoo_version': '18.0', # Ceci n'est pas un paramètre standard, mais peut être utile pour indiquer la version
}