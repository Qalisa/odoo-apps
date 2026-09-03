# -*- coding: utf-8 -*-
"""Reattacher au droit « Statistiques » les regles qui ouvrent les chiffres.

Odoo clef ses deux regles « tout voir » sur l'analyse des ventes et des
factures au groupe « Documents des autres » (`group_sale_salesman_all_leads`).
Un vendeur a qui l'on accorde de consulter les devis de ses collegues reçoit
donc, du meme geste, le chiffre d'affaires consolide des trois etablissements.
Ce sont deux droits distincts, et separer les deux est tout l'objet de ce
module.

Cela ne peut pas se faire en XML : ces regles sont declarees `noupdate` par
`sale`, et un `<record>` qui les vise est ignore — sans erreur, ce qui est le
plus traitre. On les reecrit donc par le code.
"""

REGLES = (
    'sale.sale_order_report_see_all',
    'sale.account_invoice_report_rule_see_all',
)


def reattacher_les_regles(env):
    """Fait dependre les regles « tout voir » du seul droit Statistiques."""
    statistiques = env.ref('stats_access_control.group_global_stats')
    for xml_id in REGLES:
        regle = env.ref(xml_id, raise_if_not_found=False)
        if regle:
            regle.write({'groups': [(6, 0, statistiques.ids)]})


def post_init_hook(env):
    reattacher_les_regles(env)
