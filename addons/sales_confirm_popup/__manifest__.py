{
    "name": "Devis - Popup de confirmation",
    "summary": "Ajoute une alerte supplémentaire, lors de la création d'un devis, sur le fait que celui-ci se transforme en avoir, ou en facture.",
    "version": "18.0.1.0.0",
    "author": "Qalisa",
    "depends": ["sale"],
    'license': "AGPL-3",
    'website': 'https://odoo-docs.qalisa.fr/',
    'images': ['static/description/icon.png'],
    "data": [
        "security/ir.model.access.csv",
        "views/sale_confirm_wizard_view.xml",
    ],
    "installable": True,
}