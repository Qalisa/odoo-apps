# -*- coding: utf-8 -*-

{
    'name': "Ventes - quantite negative par defaut selon le modele",
    'version': '18.0.1.0.0',
    'summary': """
Un modele de devis peut proposer -1 plutot que 1 a l'ajout d'une ligne.
""",
    'description': """
Quantité négative par défaut
============================

Un négociant qui rachète saisit ses opérations comme des devis à **quantités
négatives** : l'établissement n'y vend rien, il achète. Le devis devient
ensuite un avoir.

Odoo propose 1 à l'ajout d'une ligne. Sur un modèle de rachat, c'est le
contraire de ce qu'il faut, et le signe s'oublie — avec deux conséquences :
un montant faux, et une ligne qui cesse d'être reconnue comme un rachat par
les modules qui s'appuient sur ce signe.

Une case à cocher sur le modèle de devis renverse donc le défaut. Le choix
appartient au modèle, pas au code : un modèle ajouté plus tard se règle depuis
l'écran, sans mise à jour.

Rien n'est imposé à la saisie : la quantité reste modifiable, y compris en
positif sur un devis de rachat — une reprise, une régularisation.
""",

    'category': 'Sales',
    'author': 'Qalisa',
    'license': "AGPL-3",
    'website': 'https://odoo-docs.qalisa.fr/',
    'depends': ['sale_management'],
    'data': [
        'views/sale_order_template_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
