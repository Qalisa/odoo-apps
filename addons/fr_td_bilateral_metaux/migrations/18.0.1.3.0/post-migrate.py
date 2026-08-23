"""Renomme les déclarations déjà enregistrées.

`name` est un champ calculé stocké qui ne dépend que du millésime et de la
société : ni l'un ni l'autre ne changeant à la mise à jour, Odoo ne le
recalcule pas. Les déclarations existantes garderaient donc « DMET 2025 — … »
dans les listes et les fils de discussion, alors que l'écran ne s'appelle plus
ainsi nulle part ailleurs.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE fr_dmet_declaration
           SET name = 'Cerfa 2093-SD ' || substring(name from 6)
         WHERE name LIKE 'DMET %'
    """)
