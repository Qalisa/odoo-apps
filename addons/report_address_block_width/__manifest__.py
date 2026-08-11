{
    "name": "Rapports - Largeur du bloc adresse",
    "summary": "Corrige la troncature de l'adresse du destinataire sur les documents imprimés (mise en page « Bubble »), où la largeur du bloc dépend de la longueur du nom du client.",
    "version": "18.0.1.0.0",
    "depends": ["web"],
    "author": "Qalisa",
    "category": "Customization",
    "license": "AGPL-3",
    "assets": {
        "web.report_assets_common": [
            "report_address_block_width/static/src/scss/report_address_block.scss",
        ],
    },
    "installable": True,
}
