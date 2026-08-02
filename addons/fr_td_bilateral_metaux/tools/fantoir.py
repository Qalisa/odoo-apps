# -*- coding: utf-8 -*-
"""Table des codes nature de voie (répertoire FANTOIR) — annexe 3 du CDC DGFiP.

Alimente les zones E 010 / Q 023 (nature et nom de la voie). Le code doit être
cadré à gauche sur 4 caractères, complété d'espaces.

Certaines natures de voie renvoient au même code quelle que soit l'orthographe
(rond-point / rond point -> RPT). La recherche normalise donc tirets et
apostrophes en espaces avant comparaison, et privilégie la correspondance la
plus longue (ex. "CHEMIN RURAL" -> CR plutôt que "CHEMIN" -> CHE).
"""

from .ascii_tools import to_ascii

# label normalisé (ASCII majuscule) -> code FANTOIR
_VOIE = {
    "AERODROME": "AER", "AGGLOMERATION": "AGL", "AIRE": "AIRE", "ALLEE": "ALL",
    "ANCIEN CHEMIN": "ACH", "ANCIENNE ROUTE": "ART", "ANGLE": "ANGL", "ARCADE": "ARC",
    "AUTOROUTE": "AUT", "AVENUE": "AV", "BARRIERE": "BRE", "BASE": "BASE",
    "BASSIN": "BSN", "BERGE": "BER", "BORD": "BORD", "BOULEVARD": "BD",
    "BOURG": "BRG", "BRETELLE D AUTOROUTE": "BRTL", "CALLE": "CALL", "CAMIN": "CAMI",
    "CAMP": "CAMP", "CAMPING": "CPG", "CANAL": "CAN", "CARREFOUR": "CAR",
    "CARRIERA": "CAE", "CARRIERE": "CARE", "CASERNE": "CASR", "CENTRE": "CTRE",
    "CHALET": "CHL", "CHAMP": "CHP", "CHASSE": "CHA", "CHATEAU": "CHT",
    "CHAUSSEE": "CHS", "CHEMIN": "CHE", "CHEMIN COMMUNAL": "CC",
    "CHEMIN DEPARTEMENTAL": "CD", "CHEMIN FORESTIER": "CF", "CHEMIN RURAL": "CR",
    "CHEMIN VICINAL": "CHV", "CHEMINEMENT": "CHEM", "CITE": "CITE", "CLOS": "CLOS",
    "COIN": "COIN", "COL": "COL", "CONTOUR": "CTR", "CORNICHE": "COR",
    "CORON": "CORO", "COTE": "COTE", "COULOIR": "CLR", "COUR": "COUR",
    "COURS": "CRS", "COURSIVE": "CIVE", "CROIX": "CRX", "DARSE": "DARS",
    "DESCENTE": "DSC", "DEVIATION": "DEVI", "DIGUE": "DIG", "DOMAINE": "DOM",
    "DRAILLE": "DRA", "ECART": "ECA", "ECLUSE": "ECL", "EMBRANCHEMENT": "EMBR",
    "ENCLAVE": "ENV", "ENCLOS": "ENC", "ESCALIER": "ESC", "ESPACE": "ESPA",
    "ESPLANADE": "ESP", "ETANG": "ETNG", "FAUBOURG": "FG", "FERME": "FRM",
    "FONTAINE": "FON", "FORT": "FORT", "FOSSE": "FOS", "GALERIE": "GAL",
    "GARE": "GARE", "GRAND BOULEVARD": "GBD", "GRAND PLACE": "GPL",
    "GRANDE RUE": "GR", "GREVE": "GREV", "HABITATION": "HAB", "HALAGE": "HLG",
    "HALLE": "HLE", "HAMEAU": "HAM", "HLM": "HLM", "ILE": "ILE", "ILOT": "ILOT",
    "IMPASSE": "IMP", "JARDIN": "JARD", "JETEE": "JTE", "LAC": "LAC",
    "LEVEE": "LEVE", "LICES": "LICE", "LIGNE": "LIGN", "LOTISSEMENT": "LOT",
    "MAIL": "MAIL", "MAISON": "MAIS", "MARCHE": "MAR", "MARINA": "MRN",
    "MAS": "MAS", "MONTEE": "MTE", "NOUVELLE ROUTE": "NTE", "PARC": "PARC",
    "PARKING": "PKG", "PARVIS": "PRV", "PASSAGE": "PAS", "PASSE": "PASS",
    "PASSERELLE": "PLE", "PETIT CHEMIN": "PCH", "PETITE ALLEE": "PTA",
    "PETITE AVENUE": "PAE", "PETITE ROUTE": "PRT", "PETITE RUE": "PTR",
    "PHARE": "PHAR", "PISTE": "PIST", "PLACA": "PLA", "PLACE": "PL",
    "PLACETTE": "PTTE", "PLACIS": "PLCI", "PLAGE": "PLAG", "PLAINE": "PLN",
    "PLAN": "PLAN", "PLATEAU": "PLT", "POINTE": "PNT", "PONT": "PONT",
    "PORT": "PORT", "PORTE": "PTE", "PORTIQUE": "PORQ", "POSTE": "POST",
    "POTERNE": "POT", "PROMENADE": "PROM", "QUAI": "QUAI", "QUARTIER": "QUA",
    "RACCOURCI": "RAC", "RAMPE": "RPE", "RAVINE": "RVE", "REMPART": "REM",
    "RESIDENCE": "RES", "RIVE": "RIVE", "ROCADE": "ROC", "ROND POINT": "RPT",
    "ROTONDE": "RTD", "ROUTE": "RTE", "ROUTE DEPARTEMENTALE": "D",
    "ROUTE NATIONALE": "N", "RUE": "RUE", "RUELLE": "RLE", "RUELLETTE": "RULT",
    "RUETTE": "RUET", "RUISSEAU": "RUIS", "SAS": "SAS", "SENTIER": "SEN",
    "SQUARE": "SQ", "STADE": "STDE", "TERRASSE": "TSSE", "TERREPLEIN": "TPL",
    "TERRE PLEIN": "TPL", "TERTRE": "TRT", "TOUR": "TOUR", "TRAVERSE": "TRA",
    "TUNNEL": "TUN", "VAL": "VAL", "VALLON": "VALL", "VENELLE": "VEN",
    "VIA": "VIA", "VIADUC": "VIAD", "VIEILLE ROUTE": "VTE", "VIEUX CHEMIN": "VCHE",
    "VILLA": "VLA", "VILLAGE": "VGE", "VILLE": "VIL", "VOIE": "VOIE",
    "VOIE COMMUNALE": "VC", "VOIRIE": "VOIR", "VOUTE": "VOUT", "VOYEUL": "VOY",
    "ZONE": "ZONE", "ZONE ARTISANALE": "ZA", "ZONE D AMENAGEMENT CONCERTE": "ZAC",
    "ZONE D AMENAGEMENT DIFFERE": "ZAD", "ZONE INDUSTRIELLE": "ZI",
    "ZONE A URBANISER EN PRIORITE": "ZUP",
    # variantes orthographiques renvoyant au même code (cf. CDC annexe 3)
    "GRAND PLACE ": "GPL", "GRAND'PLACE": "GPL",
}

# Nombre maximal de mots que peut couvrir un libellé de type de voie.
_MAX_WORDS = max(len(k.split()) for k in _VOIE)


def _norm_key(text):
    """Normalise pour la recherche : ASCII majuscule, tirets/apostrophes -> espaces."""
    s = to_ascii(text)
    for ch in "-'’.":
        s = s.replace(ch, " ")
    return " ".join(s.split())


def match_voie_type(tokens):
    """Cherche le type de voie sur la plus longue séquence de tokens en tête.

    `tokens` : liste de mots (déjà normalisés ASCII majuscule).
    Retourne (code, nb_tokens_consommes) ou (None, 0) si aucune correspondance.
    """
    upper = min(_MAX_WORDS, len(tokens))
    for n in range(upper, 0, -1):
        key = _norm_key(" ".join(tokens[:n]))
        code = _VOIE.get(key)
        if code:
            return code, n
    return None, 0


def voie_code(label):
    """Retourne le code FANTOIR d'un libellé simple, ou None."""
    return _VOIE.get(_norm_key(label))
