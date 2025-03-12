{
    'name': "Gestion des taxes pour la revente d'or physique",
    'category': "Accounting/Taxes",
    'summary': "Création automatique de groupes de taxes pour la revente d'or physique",
    'description': """
Ce module crée automatiquement les groupes de taxes nécessaires pour gérer la fiscalité 
liée à la revente d'or physique en France, selon la législation en vigueur.

Fonctionnalités :
- Création de 21 groupes de taxes pour la plus-value sur l'or (de 0 à 22+ ans de détention)
- Création du groupe de taxe forfaitaire (11,5%)
- Configuration automatique des taux d'imposition et prélèvements sociaux
    """,
    'author': "Qalisa",
    'website': "https://www.qalisa.fr",
    'license': "AGPL-3",
    'version': "1.0.0",
    'depends': ['account'],
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/templates.xml',
    ],
    'images': ['static/description/icon.png'],
    'post_init_hook': 'create_gold_tax_groups',
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': [],
    },
    'odoo_version': '18.0', # Ceci n'est pas un paramètre standard, mais peut être utile pour indiquer la version
}