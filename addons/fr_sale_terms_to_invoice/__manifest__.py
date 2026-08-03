{
    'name': "Ventes — CGV du devis reportées sur facture/avoir",
    'category': "Accounting/Accounting",
    'summary': "Reporte les conditions générales du devis (sale.order.note) sur "
               "la narration de la facture/avoir quand elle est vide.",
    'description': """
Reporte les CGV du devis sur la facture et l'avoir
==================================================

En Odoo standard, ``sale.order._prepare_invoice`` recopie déjà ``note`` (les
conditions générales du devis) vers ``narration`` de la facture. Mais certains
flux — avoirs de rachat, contre-passations (reversal), imports — créent le
document **sans** passer par ce chemin : la ``narration`` reste alors vide, ou
ne peut être alimentée que par les CGV **société** par défaut
(``account.use_invoice_terms``), ce qui n'est pas souhaité lorsque les CGV sont
portées par des **modèles de devis dédiés** (par agence / société).

Ce module garantit que la ``narration`` d'une facture ou d'un avoir client
reçoit les CGV **du devis à l'origine du document**, en se basant sur :

1. le lien natif ligne de facture → ligne de devis (``sale_line_ids``) ;
2. à défaut, le champ ``invoice_origin`` (nom du devis).

La ``narration`` n'est renseignée **que si elle est vide** : une valeur déjà
posée (recopie d'un reversal, saisie manuelle) n'est jamais écrasée, et les CGV
société par défaut ne sont jamais utilisées.
    """,
    'author': "Qalisa",
    'website': "https://www.qalisa.fr",
    'license': "AGPL-3",
    'version': "18.0.1.0.0",
    'depends': ['sale'],
    'data': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'odoo_version': '18.0',
}
