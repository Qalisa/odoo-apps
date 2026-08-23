{
    'name': "Cerfa 2093-SD - Déclaration d'achat au détail de métaux",
    'category': "Accounting/Localizations",
    'summary': "Cerfa 2093-SD : déclaration annuelle d'achats au détail de métaux ferreux et non ferreux (CGI art. 1649 bis), génération du fichier et dépôt par la procédure DGFiP TD/bilatéral",
    'description': """
Comment s'appelle cette déclaration
-----------------------------------

Son nom officiel est la **déclaration d'achats au détail de métaux ferreux et
non ferreux**, formulaire **n° 2093**, due au titre de l'**article 1649 bis du
CGI** (contenu fixé par le décret n° 2012-1322 et l'art. 344 GE de l'annexe III
au CGI). Elle se dépose via le service « Tiers déclarants » de l'espace
professionnel d'impots.gouv.fr, **avant le 31 janvier de l'année qui suit**
celle des achats.

`DMET` n'est pas le nom de la déclaration : c'est la **valeur fixe en tête du
nom de fichier** imposée par la procédure de transfert, qui identifie la nature
des informations transmises —
``DMET_<millésime>_<SIREN>_<ordre>_<horodatage>.txt.gz.gpg``. Le préfixe est
conservé dans le code (modèles, champs, méthodes) et dans le nom du fichier
produit, parce qu'il y désigne exactement ce qu'il nomme. Partout où
l'utilisateur lit, c'est **Cerfa 2093-SD** qui s'affiche.

Note de millésime : l'administration a publié les formulaires sous les
références `2093-T-SD` et `2093-I-SD` jusqu'au millésime 2024, et `2093-T` /
`2093-I` pour 2025. Le libellé retenu ici, « Cerfa 2093-SD », suit celui du
Cerfa 2091-SD voisin pour que les deux écrans se lisent ensemble.

Ce que fait le module
---------------------

Génère le fichier conforme au cahier des charges DGFiP **TD/bilatéral** —
« procédure bilatérale de transfert des déclarations d'achats au détail de
métaux par procédé informatique » : enregistrements séquentiels E/Q/T à format
fixe de 550 caractères, encodage UTF-8, nommage réglementaire, compression
GZIP puis chiffrement GPG.

Inclut un écran de pré-contrôle rejouant les anomalies bloquantes et non
bloquantes du cahier des charges avant transmission.
    """,
    'author': "Qalisa",
    'website': "https://odoo-docs.qalisa.fr/",
    'license': "AGPL-3",
    'version': "1.3.0",
    # `contacts_citizenship_id` (1.2.0) apporte l'identité structurée et dépend
    # lui-même de `partner_firstname` (OCA) pour l'éclatement nom/prénom (Q 014/015).
    # `l10n_fr_account` apporte le SIRET (res.partner) et le code APE (res.company).
    # `fr_numismatics_reports` porte le menu « Aide à la déclaration », où
    # cette déclaration se range à côté du Cerfa 2091-SD.
    'depends': ['l10n_fr_account', 'contacts_citizenship_id',
                'fr_numismatics_reports'],
    'data': [
        'security/ir.model.access.csv',
        'views/dmet_declaration_views.xml',
        'views/menu.xml',
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
