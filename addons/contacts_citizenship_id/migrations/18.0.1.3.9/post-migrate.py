# -*- coding: utf-8 -*-
"""Suppression du champ `id_doc_issue_place` (lieu de délivrance).

Le lieu de délivrance n'est exigé par aucun des textes applicables :
  - **C. pén. art. R321-3** (registre des objets mobiliers) : « la nature, le
    numéro et la date de délivrance de la pièce d'identité produite […] avec
    l'indication de l'autorité qui l'a établie » — le *lieu* n'y figure pas ;
  - **CGI ann. IV art. 56 J quindecies** (registre métaux précieux) : se limite
    aux nom, prénoms et adresse, sur justification de l'identité ;
  - **DMET** : le dessin d'enregistrement Q ne comporte aucune zone « pièce
    d'identité ».

Le champ imposait donc une saisie sans fondement, et bloquait la validation des
rachats (il entrait dans `id_doc_complete`).

Trois opérations, dans cet ordre :
  1. **repli non destructif** du lieu dans `id_doc_authority` (champ, lui, exigé)
     lorsqu'il apporte une précision absente de l'autorité — ex. autorité
     « PREFET » + lieu « THIONVILLE » -> « PREFET (THIONVILLE) » ;
  2. suppression de la colonne devenue orpheline ;
  3. **recalcul** de `id_doc_complete` : ce champ est stocké et sa règle change
     (4 mentions au lieu de 5) ; Odoo ne recalcule pas les enregistrements
     existants sur simple changement du `compute`.
"""


def migrate(cr, version):
    if not version:
        return

    cr.execute("""
        SELECT column_name FROM information_schema.columns
         WHERE table_name = 'res_partner' AND column_name = 'id_doc_issue_place'
    """)
    if cr.fetchone():
        # 1. Repli du lieu dans l'autorité (uniquement s'il ajoute de l'info).
        cr.execute("""
            UPDATE res_partner
               SET id_doc_authority = CASE
                       WHEN id_doc_authority IS NULL OR btrim(id_doc_authority) = ''
                       THEN btrim(id_doc_issue_place)
                       ELSE btrim(id_doc_authority) || ' (' || btrim(id_doc_issue_place) || ')'
                   END
             WHERE id_doc_issue_place IS NOT NULL
               AND btrim(id_doc_issue_place) <> ''
               AND (id_doc_authority IS NULL
                    OR position(upper(btrim(id_doc_issue_place)) in upper(coalesce(id_doc_authority, ''))) = 0)
        """)

        # 2. Suppression de la colonne orpheline.
        cr.execute("ALTER TABLE res_partner DROP COLUMN id_doc_issue_place")

    # 3. Recalcul de la complétude R321-3 sur la nouvelle règle (4 mentions).
    cr.execute("""
        UPDATE res_partner
           SET id_doc_complete = (
                   id_doc_type       IS NOT NULL AND btrim(id_doc_type) <> ''
               AND id_doc_number     IS NOT NULL AND btrim(id_doc_number) <> ''
               AND id_doc_issue_date IS NOT NULL
               AND id_doc_authority  IS NOT NULL AND btrim(id_doc_authority) <> ''
               )
    """)
