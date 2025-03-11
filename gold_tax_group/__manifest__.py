{
    'name': "Gestion des taxes pour la revente d'or physique",
    'category': "Accounting",
    'summary': "Création automatique de groupes de taxes associés à la revente d'or physique",
    'description': "Création automatique de groupes de taxes associés à la revente d'or physique",
    'author': "Qalisa",
    'license': "AGPL-3",
    'version': "1.0",
    'depends': ['account'],
    'post_init_hook': 'create_gold_tax_groups',
    'installable': True,
    'application': False,
}