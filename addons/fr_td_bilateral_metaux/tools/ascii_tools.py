# -*- coding: utf-8 -*-
"""Outils de mise en conformité caractères pour la procédure TD/bilatéral.

Le cahier des charges DGFiP impose que chaque enregistrement ne contienne que
des caractères de la plage hexadécimale 0x20 à 0x7E (US-ASCII imprimable),
encodés en UTF-8 sans BOM. Les accents et caractères spéciaux doivent donc être
translittérés, et le tout mis en majuscules.
"""

import unicodedata

# Plage autorisée par le cahier des charges (§4 "Qualité des fichiers transmis").
_MIN_CP = 0x20
_MAX_CP = 0x7E

# Translittérations explicites non couvertes par la décomposition NFKD.
_SPECIALS = {
    "€": "E",
    "œ": "OE", "Œ": "OE",
    "æ": "AE", "Æ": "AE",
    "ß": "SS",
    "’": "'", "‘": "'", "`": "'", "´": "'",
    "–": "-", "—": "-", "‑": "-",
    "…": "...",
    "«": '"', "»": '"',
}


def to_ascii(value, upper=True):
    """Translittère une valeur en ASCII imprimable (0x20-0x7E).

    - décompose les accents (é -> E, à -> A, ç -> C...) ;
    - remplace les ligatures et signes spéciaux courants ;
    - met en majuscules (comportement attendu par le CDC) ;
    - neutralise par une espace tout caractère hors plage résiduel.
    """
    if value is None:
        return ""
    s = str(value)
    # Remplacements explicites avant décomposition.
    for src, dst in _SPECIALS.items():
        if src in s:
            s = s.replace(src, dst)
    # Décomposition canonique + suppression des diacritiques.
    s = unicodedata.normalize("NFKD", s)
    s = s.encode("ascii", "ignore").decode("ascii")
    if upper:
        s = s.upper()
    # Filet de sécurité : neutralise tout ce qui resterait hors plage.
    s = "".join(ch if _MIN_CP <= ord(ch) <= _MAX_CP else " " for ch in s)
    return s


def digits_only(value):
    """Ne conserve que les chiffres d'une valeur (SIRET, code postal, montant...)."""
    if value is None:
        return ""
    return "".join(ch for ch in str(value) if ch.isdigit())


def is_within_charset(text):
    """Vrai si `text` ne contient que des caractères 0x20-0x7E (contrôle CDC)."""
    return all(_MIN_CP <= ord(ch) <= _MAX_CP for ch in text)
