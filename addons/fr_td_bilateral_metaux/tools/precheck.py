# -*- coding: utf-8 -*-
"""Pré-contrôle des anomalies DGFiP (§7 et §8 du CDC) avant génération du fichier.

Rejoue, sur les données déjà normalisées d'un déclarant et de ses vendeurs, les
contrôles du cahier des charges, classés en trois gravités :

    B (bloquante)          -> une seule occurrence entraîne le rejet du fichier.
    S (bloquante à seuil)  -> rejet seulement si le taux dépasse le seuil
                              (1 % sur le SIRET vendeur, 5 % sur code postal /
                              commune). En dessous, l'administration exerce son
                              droit de contrôle habituel.
    N (non bloquante)      -> signalée, sans rejet.

Le module ne dépend pas d'Odoo : il opère sur les mêmes dictionnaires que ceux
consommés par ``dmet.build_q`` / ``build_e``, donc il contrôle exactement ce qui
sera écrit dans le fichier.
"""

from dataclasses import dataclass
from typing import Optional

from .ascii_tools import to_ascii, digits_only
from .dmet import round_euro

# Gravités
B = "bloquante"
S = "bloquante_seuil"
N = "non_bloquante"


@dataclass
class Finding:
    zone: str                       # code zone CDC, ex. "Q027"
    label: str                      # libellé de la zone
    severity: str                   # B / S / N
    message: str                    # aide à la correction
    ref: str                        # vendeur concerné (ou "DECLARANT")
    threshold: Optional[float] = None   # seuil en % pour la gravité S
    partner_id: Optional[int] = None    # id opaque du partenaire (rattachement anomalie -> fiche)


# --------------------------------------------------------------------------
# Prédicats
# --------------------------------------------------------------------------

def _blank(value):
    """Vrai si vide, ou ne contenant aucun caractère alphanumérique."""
    if value is None:
        return True
    return not any(ch.isalnum() for ch in to_ascii(value))


def _is_number(value):
    try:
        float(value)
        return True
    except (TypeError, ValueError):
        return False


def valid_fr_cp(cp):
    """Code postal France valide : 5 chiffres, 2 premiers significatifs (≠ 00)."""
    d = digits_only(cp)
    return len(d) == 5 and d[:2] != "00"


def vendor_ref(vendor, index=0):
    """Libellé lisible d'un vendeur pour l'affichage des anomalies.

    Inclut le prénom afin de distinguer les homonymes (même nom de famille).
    Ce texte est purement indicatif : le rattachement à la fiche se fait via
    ``Finding.partner_id`` (identifiant unique), jamais par ce libellé.
    """
    nom = to_ascii(vendor.get("nom") or vendor.get("raison_sociale") or "").strip()
    prenoms = to_ascii(vendor.get("prenoms") or "").strip()
    if nom and prenoms:
        return "%s %s" % (nom, prenoms)
    return nom or ("vendeur #%d" % index)


# --------------------------------------------------------------------------
# Contrôles
# --------------------------------------------------------------------------

def check_declarant(header, declarant):
    out = []
    ref = "DECLARANT"
    if digits_only(header.get("annee")) != "2025":
        out.append(Finding("E001", "Année", B,
                           "L'année doit être 2025 (achats réalisés en 2025).", ref))
    if len(digits_only(header.get("siret"))) != 14:
        out.append(Finding("E002", "SIRET déclarant", B,
                           "SIRET à 14 chiffres requis (siège : 12345678900014).", ref))
    if _blank(declarant.get("nom")):
        out.append(Finding("E005", "Identification du déclarant", B,
                           "Nom ou raison sociale obligatoire.", ref))
    if not valid_fr_cp(declarant.get("code_postal")):
        out.append(Finding("E015", "Code postal déclarant", B,
                           "Code postal invalide (2 premiers chiffres significatifs).", ref))
    if _blank(declarant.get("bureau")) and _blank(declarant.get("libelle_commune")):
        out.append(Finding("E014/E017", "Commune / bureau distributeur", B,
                           "Commune et bureau distributeur obligatoires.", ref))
    if len(digits_only(declarant.get("date_emission"))) != 8:
        out.append(Finding("E020", "Date d'émission", B,
                           "Date d'émission au format AAAAMMJJ requise.", ref))
    act = to_ascii(declarant.get("code_activite")).strip().strip("0")
    if not act:
        out.append(Finding("E018", "Code activité (APE)", N,
                           "Code activité INSEE non renseigné.", ref))
    return out


def check_vendor(vendor, index):
    out = []
    ref = vendor_ref(vendor, index)
    is_company = bool(vendor.get("is_company"))
    foreign = bool(vendor.get("foreign"))

    # Noms (Q006/Q014/Q016) — au moins une zone renseignée. Bloquante.
    if all(_blank(vendor.get(k)) for k in ("raison_sociale", "nom", "nom_usage")):
        out.append(Finding("Q006/Q014/Q016", "Raison sociale / nom / nom d'usage", B,
                           "Aucun nom exploitable : l'une de ces zones doit contenir "
                           "des caractères alphabétiques.", ref))

    if not is_company:
        if _blank(vendor.get("nom")):
            out.append(Finding("Q014", "Nom de famille", B,
                               "Nom de naissance obligatoire (personne physique).", ref))
        if _blank(vendor.get("prenoms")):
            out.append(Finding("Q015", "Prénom", N, "Prénom absent.", ref))
        # Date de naissance : non numérique -> bloquante ; absente -> non bloquante.
        for key, zone, lbl in (("jour_naiss", "Q007", "Jour de naissance"),
                               ("mois_naiss", "Q008", "Mois de naissance"),
                               ("annee_naiss", "Q009", "Année de naissance")):
            val = vendor.get(key)
            if val not in (None, "") and not str(val).isdigit():
                out.append(Finding(zone, lbl, B, "Date de naissance non numérique.", ref))
        if all(_blank(vendor.get(k)) for k in ("jour_naiss", "mois_naiss", "annee_naiss")):
            out.append(Finding("Q007-009", "Date de naissance", N,
                               "Date de naissance absente (00/00/0000 accepté).", ref))
        if to_ascii(vendor.get("titre")).strip() not in ("M", "MME"):
            out.append(Finding("Q013", "Titre (civilité)", N,
                               "Civilité absente ou différente de M / MME.", ref))
        if _blank(vendor.get("commune_naiss")):
            out.append(Finding("Q010-012", "Lieu de naissance", N,
                               "Lieu de naissance absent (accepté à zéro).", ref))

    # Personne morale (non étrangère) : SIRET vendeur. Bloquante à seuil 1 %.
    if is_company and not foreign:
        siret = digits_only(vendor.get("siret_vendeur"))
        if _blank(vendor.get("siret_vendeur")):
            out.append(Finding("Q005", "Numéro SIRET vendeur", S,
                               "SIRET obligatoire pour une personne morale.", ref, 1.0))
        elif len(siret) != 14:
            out.append(Finding("Q005", "Numéro SIRET vendeur", S,
                               "SIRET vendeur mal formé (14 chiffres).", ref, 1.0))

    # Code postal (Q027). Bloquante à seuil 5 % (non bloquante si vendeur étranger).
    if not valid_fr_cp(vendor.get("code_postal")):
        if foreign:
            out.append(Finding("Q027", "Code postal", N,
                               "Adresse étrangère : code postal au format pays.", ref))
        else:
            out.append(Finding("Q027", "Code postal", S,
                               "Code postal absent ou invalide (2 premiers chiffres "
                               "significatifs requis).", ref, 5.0))

    # Commune + bureau distributeur (Q026/Q029). Bloquante à seuil 5 %.
    if _blank(vendor.get("bureau")) and _blank(vendor.get("libelle_commune")):
        out.append(Finding("Q026/Q029", "Commune / bureau distributeur", S,
                           "Commune et bureau distributeur absents.", ref, 5.0))

    # Montant TTC annuel (Q030). Bloquante.
    montant = vendor.get("montant")
    if _blank(montant) or not _is_number(montant):
        out.append(Finding("Q030", "Montant TTC annuel", B,
                           "Montant absent ou non numérique.", ref))
    elif round_euro(montant) < 1:
        out.append(Finding("Q030", "Montant TTC annuel", B,
                           "Montant < 1 € : ce vendeur ne doit pas être déclaré.", ref))

    pid = vendor.get("_partner_id")
    for finding in out:
        finding.partner_id = pid
    return out


def check_file(header, declarant, vendors):
    """Contrôle complet. Retourne un rapport agrégé avec évaluation des seuils."""
    findings = list(check_declarant(header, declarant))
    for i, vendor in enumerate(vendors, start=1):
        findings.extend(check_vendor(vendor, i))

    nb = max(len(vendors), 1)

    # Évaluation des anomalies à seuil : regroupement par (zone, seuil).
    groups = {}
    for f in findings:
        if f.severity == S:
            groups.setdefault((f.zone, f.threshold, f.label), []).append(f)
    seuils = []
    for (zone, thr, label), items in sorted(groups.items()):
        rate = 100.0 * len(items) / nb
        seuils.append({
            "zone": zone, "label": label, "threshold": thr,
            "count": len(items), "rate": rate, "exceeded": rate > thr,
        })

    hard = [f for f in findings if f.severity == B]
    non_blocking = [f for f in findings if f.severity == N]
    rejected = bool(hard) or any(s["exceeded"] for s in seuils)

    return {
        "verdict": "REJET" if rejected else "OK",
        "nb_vendors": len(vendors),
        "findings": findings,
        "bloquantes": hard,
        "seuils": seuils,
        "non_bloquantes": non_blocking,
    }
