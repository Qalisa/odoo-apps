# -*- coding: utf-8 -*-
"""Normalisation d'adresse au format structuré DGFiP (§6.3 du CDC).

Découpe une rue « à plat » en zones réglementaires :
  - numéro dans la voie (E007/Q020, 4 car. numériques) ;
  - indice de répétition (E008/Q021, 1 car. : B/T/Q pour Bis/Ter/Quater...) ;
  - zone « nature et nom de la voie » (E010/Q023, 26 car.) construite comme :
        code FANTOIR (4, cadré à gauche) + séparateur espace (1) + nom (21).

Le nom de voie est, si nécessaire, tronqué **à gauche** sans jamais amputer le
dernier mot (CDC §6.3.1.2). Le libellé de commune, lui, est tronqué à droite.
"""

import re

from .ascii_tools import to_ascii, digits_only
from .fantoir import match_voie_type

VOIE_ZONE_LEN = 26
_NOM_LEN = VOIE_ZONE_LEN - 5  # 4 (code) + 1 (séparateur) => 21 restants pour le nom

_INDICE_WORDS = {"BIS": "B", "TER": "T", "QUATER": "Q", "QUINQUIES": "C"}


def _fit_left(nom, n):
    """Troncature à gauche : retire les mots de tête, garde le dernier mot entier."""
    if len(nom) <= n:
        return nom
    words = nom.split()
    while len(words) > 1 and len(" ".join(words)) > n:
        words.pop(0)
    res = " ".join(words)
    return res[-n:] if len(res) > n else res


def parse_street(raw):
    """Décompose une rue en zones DGFiP.

    Retourne un dict : num_voie(4), indice_rep(1), voie_code, nom_voie, voie_zone(26).
    """
    out = {
        "num_voie": "0000", "indice_rep": "", "voie_code": "",
        "nom_voie": "", "voie_zone": " " * VOIE_ZONE_LEN,
    }
    s = to_ascii(raw).strip()
    if not s:
        return out

    # 1) Numéro de voie en tête (+ indice de répétition éventuel).
    num = ""
    m = re.match(r"^(\d+)\s*(.*)$", s)
    if m:
        # La virgule qui suit le numéro — « 19, RUE MAURICE BARRES », soit un
        # tiers des fiches du fichier client — doit disparaître ici. Laissée en
        # tête, elle occupe le premier jeton : le type de voie FANTOIR n'est
        # plus reconnu, et la zone déclarée part avec la virgule. Le tiret est
        # épargné, il porte l'indice de répétition (« 5-1 RUE … »).
        num, s = m.group(1), m.group(2).lstrip(" ,;").strip()

    indice = ""
    if num:
        m2 = re.match(r"^-\s*(\d+)\s+(.*)$", s)        # cas "5-1 RUE ..."
        if m2:
            indice, s = m2.group(1)[:1], m2.group(2).strip()
        else:                                            # cas "25 BIS RUE ..."
            first = s.split(" ", 1)[0] if s else ""
            if first in _INDICE_WORDS:
                indice = _INDICE_WORDS[first]
                s = s.split(" ", 1)[1].strip() if " " in s else ""

    # Numéro > 4 chiffres : la zone numérique est neutralisée et le numéro
    # est reporté dans le nom de la voie (CDC §6.3.1.2).
    prepend = ""
    if num and len(num) > 4:
        prepend, num = num + " ", ""
    out["num_voie"] = num.rjust(4, "0")[-4:] if num else "0000"
    if indice:
        out["indice_rep"] = indice[:1]

    # 2) Type de voie (FANTOIR) puis nom.
    tokens = s.split()
    code, consumed = match_voie_type(tokens)
    nom = " ".join(tokens[consumed:]) if code else " ".join(tokens)
    if code:
        out["voie_code"] = code
    nom = (prepend + nom).strip()
    out["nom_voie"] = nom

    # 3) Assemblage de la zone 26 caractères.
    prefix = (code or "").ljust(4)[:4] + " "
    out["voie_zone"] = (prefix + _fit_left(nom, _NOM_LEN)).ljust(VOIE_ZONE_LEN)[:VOIE_ZONE_LEN]
    return out


def format_commune(label, length=26):
    """Libellé de commune : ASCII majuscule, troncature à droite (CDC §6.3.1.3)."""
    return to_ascii(label)[:length].ljust(length)


def normalize_cp(zip_raw, foreign=False):
    """Code postal 5 caractères.

    Cas France : un code sur 2 chiffres (département seul) est complété en
    « <dd>000 » (CDC §6.3.1.4 : « à défaut, code département suivi de trois zéros »).
    Le traitement des adresses hors métropole (COG pays) relève de l'appelant.
    """
    d = digits_only(zip_raw)
    if len(d) >= 5:
        return d[:5]
    if len(d) == 2:
        return d + "000"
    if 1 <= len(d) <= 4:
        return d.rjust(5, "0")
    return "00000"
