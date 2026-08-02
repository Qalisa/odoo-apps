{
    'name': "TD/Bilatéral - Achats au détail de métaux (DMET)",
    'category': "Accounting/Localizations",
    'summary': "Génération et télétransmission des déclarations d'achats au détail de métaux ferreux et non ferreux (procédure DGFiP TD/bilatéral, fichier DMET)",
    'description': """
Génère le fichier de déclaration `DMET` (achats au détail de métaux ferreux et non ferreux,
article 1649 bis du CGI) conforme au cahier des charges DGFiP TD/bilatéral :
enregistrements séquentiels E/Q/T à format fixe de 550 caractères, encodage UTF-8,
nommage réglementaire et compression GZIP.

Inclut un écran de pré-contrôle rejouant les anomalies bloquantes et non bloquantes
du cahier des charges avant transmission.
    """,
    'author': "Qalisa",
    'website': "https://odoo-docs.qalisa.fr/",
    'license': "AGPL-3",
    'version': "1.0.0",
    # `partner_firstname` (OCA) requis pour l'éclatement nom/prénom du vendeur (zones Q 014/015).
    'depends': ['account', 'contacts_citizenship_id'],
    'data': [
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'external_dependencies': {
        'python': [],
    },
    'images': ['static/description/icon.png'],
    'odoo_version': '18.0',
}
