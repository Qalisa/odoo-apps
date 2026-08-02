# -*- coding: utf-8 -*-
"""Construction du fichier DMET (achats au détail de métaux ferreux et non ferreux).

Cahier des charges DGFiP TD/bilatéral, campagne 2026 (achats 2025).

Structure du fichier : une suite d'enregistrements séquentiels à format fixe de
550 caractères, chacun suivi d'un saut de ligne (position 551) :

    E   (1)      article "Déclarant" / émetteur
    Q   (1..n)   une "ligne vendeur" par vendeur (montant annuel cumulé)
    T   (1)      article "Totalisation"

La zone "indicatif" (positions 1 à 20) est identique sur E, Q et T :
    année(4) + SIRET déclarant(14) + type de déclaration(1) + type d'enregistrement(1).
"""

import gzip
import math

from .ascii_tools import to_ascii, digits_only

RECORD_LENGTH = 550

# --------------------------------------------------------------------------
# Dessins d'enregistrement : (clé, position 1-based, longueur, classe)
#   classe "N" -> numérique, cadré à droite, complété de zéros à gauche
#   classe "A" -> alphanumérique, cadré à gauche, complété d'espaces à droite
# Les séparateurs (classe "A" non renseignés) sont naturellement remplis d'espaces.
# --------------------------------------------------------------------------

FIELDS_E = [
    ("annee",            1,   4, "N"),
    ("siret",            5,  14, "A"),
    ("type_decl",       19,   1, "N"),
    ("type_enr",        20,   1, "A"),   # "E"
    ("nom",             21,  50, "A"),
    ("compl_adr",       71,  32, "A"),
    ("num_voie",       103,   4, "N"),
    ("indice_rep",     107,   1, "A"),
    ("sep1",           108,   1, "A"),
    ("voie",           109,  26, "A"),
    ("insee_commune",  135,   5, "N"),
    ("sep2",           140,   1, "A"),
    ("libelle_commune",141,  26, "A"),
    ("code_postal",    167,   5, "N"),
    ("sep3",           172,   1, "A"),
    ("bureau",         173,  26, "A"),
    ("code_activite",  199,   5, "A"),
    ("type_structure", 204,   2, "N"),   # "58"
    ("date_emission",  206,   8, "N"),   # AAAAMMJJ
    ("filler",         214, 337, "A"),
]

FIELDS_Q = [
    ("annee",            1,   4, "N"),
    ("siret",            5,  14, "A"),
    ("type_decl",       19,   1, "A"),
    ("type_enr",        20,   1, "A"),   # "Q"
    ("siret_vendeur",   21,  14, "A"),
    ("raison_sociale",  35,  50, "A"),
    ("jour_naiss",      85,   2, "N"),
    ("mois_naiss",      87,   2, "N"),
    ("annee_naiss",     89,   4, "N"),
    ("dept_naiss",      93,   2, "A"),   # 2A/2B admis
    ("insee_naiss",     95,   3, "N"),
    ("commune_naiss",   98,  26, "A"),
    ("titre",          124,   3, "A"),   # M / MME
    ("nom",            127,  30, "A"),
    ("prenoms",        157,  20, "A"),
    ("nom_usage",      177,  30, "A"),
    ("compl_adr",      207,  32, "A"),
    ("reserve1",       239,   1, "A"),
    ("num_voie",       240,   4, "N"),
    ("indice_rep",     244,   1, "A"),
    ("sep1",           245,   1, "A"),
    ("voie",           246,  26, "A"),
    ("insee_commune",  272,   5, "N"),
    ("sep2",           277,   1, "A"),
    ("libelle_commune",278,  26, "A"),
    ("code_postal",    304,   5, "N"),
    ("sep3",           309,   1, "A"),
    ("bureau",         310,  26, "A"),
    ("montant",        336,  10, "N"),
    ("reserve2",       346, 205, "A"),
]

FIELDS_T = [
    ("annee",            1,   4, "N"),
    ("siret",            5,  14, "A"),
    ("type_decl",       19,   1, "N"),
    ("type_enr",        20,   1, "A"),   # "T"
    ("nb_q",            21,  10, "N"),
    ("responsable",     31,  50, "A"),
    ("tel",             81,  10, "N"),
    ("email",           91,  60, "A"),
    ("siren_remettant",151,   9, "N"),
    ("filler",         160, 391, "A"),
]


def _place(buf, start, length, value, kind):
    """Écrit une zone formatée dans le tampon (start est 1-based)."""
    if kind == "N":
        d = digits_only(value)
        d = d[-length:]                       # tronque à gauche si trop long
        s = d.rjust(length, "0")
    else:
        s = to_ascii(value)[:length].ljust(length, " ")
    buf[start - 1:start - 1 + length] = list(s)


def _build_record(fields, values):
    """Assemble un enregistrement de 550 caractères à partir d'un dessin et de valeurs."""
    buf = [" "] * RECORD_LENGTH
    for key, start, length, kind in fields:
        _place(buf, start, length, values.get(key, ""), kind)
    record = "".join(buf)
    if len(record) != RECORD_LENGTH:
        raise ValueError(
            "Enregistrement de longueur %d au lieu de %d" % (len(record), RECORD_LENGTH)
        )
    return record


def build_e(header, declarant):
    """Construit l'enregistrement Déclarant (E)."""
    values = dict(declarant)
    values.update(header)
    values["type_enr"] = "E"
    values.setdefault("type_structure", "58")
    return _build_record(FIELDS_E, values)


def round_euro(montant):
    """Arrondit à l'euro selon le CDC : fraction >= 0,50 comptée pour 1.

    Arrondi "demi-supérieur" (et non l'arrondi au pair de `round()` de Python).
    Les montants déclarés sont toujours positifs (CDC §6.1.3).
    """
    return int(math.floor(float(montant) + 0.5))


def build_q(header, vendor):
    """Construit une ligne Vendeur (Q). Le montant est arrondi à l'euro."""
    values = dict(vendor)
    values.update(header)
    values["type_enr"] = "Q"
    if "montant" in vendor and vendor["montant"] not in (None, ""):
        values["montant"] = round_euro(vendor["montant"])
    return _build_record(FIELDS_Q, values)


def build_t(header, totalisation, nb_q):
    """Construit l'enregistrement Totalisation (T)."""
    values = dict(totalisation)
    values.update(header)
    values["type_enr"] = "T"
    values["nb_q"] = nb_q
    return _build_record(FIELDS_T, values)


def build_file(header, declarant, vendors, totalisation):
    """Assemble le contenu texte complet du fichier DMET.

    Chaque enregistrement (550 car.) est suivi d'un saut de ligne `\\n`
    (attendu en position 551 par le CDC). Retourne une chaîne `str`.
    """
    records = [build_e(header, declarant)]
    records += [build_q(header, v) for v in vendors]
    records.append(build_t(header, totalisation, nb_q=len(vendors)))
    return "".join(r + "\n" for r in records)


def encode_utf8(content):
    """Encode le contenu en UTF-8 sans BOM (exigence du CDC)."""
    return content.encode("utf-8")


def gzip_bytes(raw_bytes, filename=None, mtime=0):
    """Compresse au format GZIP. `mtime=0` pour un résultat déterministe."""
    import io
    out = io.BytesIO()
    with gzip.GzipFile(
        filename=(filename or ""), mode="wb", fileobj=out, mtime=mtime
    ) as gz:
        gz.write(raw_bytes)
    return out.getvalue()


def build_filename(siren, millesime, ordre, dt):
    """Nom réglementaire : DMET_<millesime>_<identifiant>_<ordre>_<horodatage>.txt

    Exemple : DMET_2025_999888777_001_20260130151220.txt
    """
    ident = digits_only(siren) or str(siren)
    return "DMET_%s_%s_%03d_%s.txt" % (
        millesime, ident, int(ordre), dt.strftime("%Y%m%d%H%M%S"),
    )
