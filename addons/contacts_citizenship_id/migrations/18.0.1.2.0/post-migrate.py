# -*- coding: utf-8 -*-
"""Reprise du champ historique `id_proof` vers la zone structurée `id_doc_number`.

Exécutée lors de la montée de version 1.1.x -> 1.2.0. Ne touche que les fiches
dont le numéro structuré est encore vide, pour rester idempotente.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE res_partner
           SET id_doc_number = id_proof
         WHERE id_proof IS NOT NULL
           AND btrim(id_proof) <> ''
           AND (id_doc_number IS NULL OR btrim(id_doc_number) = '')
    """)
