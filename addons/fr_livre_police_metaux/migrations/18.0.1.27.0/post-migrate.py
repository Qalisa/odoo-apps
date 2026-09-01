"""Donne son nom de lot aux inscriptions ecrites avant les transferts.

`numero_lot` dit sous quel nom le lot d'une inscription existe en stock.
C'est par lui, et non plus par le numero d'ordre, qu'une sortie retrouve
l'entree a laquelle se rattacher — les deux coincident au comptoir de rachat
et divergent des qu'un metal a change d'etablissement.

Les inscriptions anterieures n'ont pas la colonne. Sans cette reprise, la
vente d'un metal rachete avant la mise a jour ne trouverait aucune entree et
ne s'inscrirait pas : elle sortirait du stock sans sortir du registre.

La reprise ne vaut que pour les entrees. Une sortie tient son nom de lot du
mouvement de stock, et les sorties deja inscrites ont deja produit leur effet.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE livre_police_ligne
           SET numero_lot = numero_ordre
         WHERE numero_lot IS NULL
           AND sens = 'entree'
    """)
