{
    'name': "Avoirs - Affichage du compte destinataire",
    'category': "Sales/Credit",
    'summary': "Permet l'affichage d'un compte bancaire destinataire du montant de l'avoir sur la preuve du client",
    'description': """
Permet l'affichage d'un compte bancaire destinataire du montant de l'avoir sur la preuve du client
    """,
    'author': "Qalisa",
    'website': "https://www.qalisa.fr",
    'license': "AGPL-3",
    'version': "1.0.0",
    'depends': ['account'],
    'data': [
        'views/report_views.xml'
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