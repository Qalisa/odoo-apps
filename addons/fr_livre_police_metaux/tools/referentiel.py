# -*- coding: utf-8 -*-
"""Deux libellés désignent-ils la même valeur de référence ?

Les vocabulaires du registre — provenance de l'objet, qualité du vendeur — se
saisissent au comptoir, parfois dans l'urgence. Laissés en texte libre, ils
cessent d'être une information : « Succession », « succession », « héritage »
et « SUCC. » ne se retrouvent, ne se contrôlent et ne se totalisent plus.

La liste est donc fermée à la variante d'écriture, sans l'être aux valeurs
nouvelles : le comptoir peut créer ce qu'il n'avait pas prévu, mais pas une
deuxième orthographe de ce qui existe déjà.

Aucun ``import odoo`` ici : la règle se teste en isolation.
"""

import re
import unicodedata


# Mots qui relient sans désigner. « Héritage ou succession », « Héritage /
# succession » et « Héritage et succession » nomment la même provenance : les
# retenir ferait entrer trois libellés pour une seule information.
LIAISONS = frozenset((
    'a', 'au', 'aux', 'd', 'de', 'des', 'du', 'en', 'et', 'l', 'la', 'le',
    'les', 'ou', 'par', 'pour', 'sur', 'un', 'une',
))

# Terminaison féminine mise entre parenthèses — « Salarié(e) »,
# « Vendeur(euse) ». Elle accorde le libellé, elle ne le désigne pas : deux
# qualités ne se distinguent jamais par elle.
PARENTHESES = re.compile(r'\([^)]*\)')


def cle_de_comparaison(libelle):
    """Forme normalisée d'un libellé, pour ne pas créer deux fois le même.

    Ni la casse, ni les accents, ni la ponctuation, ni les mots de liaison, ni
    l'accord ne distinguent deux valeurs. Ce qui reste est l'ensemble des mots
    porteurs, trié : « HÉRITAGE / SUCCESSION » et « Héritage ou succession »
    donnent la même clé et ne peuvent pas coexister au registre.

    L'écriture inclusive tombe deux fois. Sa forme entre parenthèses part
    avant le découpage — « Salarié(e) » et « Salarié » ont la même clé ; sa
    forme suffixée laisse une lettre isolée, qu'on écarte comme les mots de
    liaison : « salarié-e », « salarié·e » et « Salarié (e) » ne créent pas
    quatre professions. Aucune valeur du registre ne se nomme d'une lettre.

    La comparaison reste orthographique. Elle ne connaît ni les synonymes ni
    l'accord porté par le mot lui-même : « Legs » passera à côté de
    « Héritage ou succession », « Retraitée » à côté de « Retraité », et c'est
    au responsable de l'arbitrer depuis la liste de configuration.
    """
    texte = PARENTHESES.sub(' ', libelle or '')
    texte = unicodedata.normalize('NFKD', texte)
    texte = ''.join(c for c in texte if not unicodedata.combining(c))
    mots = ''.join(c if c.isalnum() else ' ' for c in texte.lower()).split()
    porteurs = [mot for mot in mots
                if len(mot) > 1 and mot not in LIAISONS]
    return ' '.join(sorted(porteurs or mots))
