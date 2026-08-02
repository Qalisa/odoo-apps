# `fr_td_bilateral_metaux` — Notes de développement / reprise

> Document de passation. À lire avant de reprendre le module.
> Le cahier des charges DGFiP officiel est versionné à côté :
> [`cdc_achat_detail_metaux_2026-achats_2025.pdf`](./cdc_achat_detail_metaux_2026-achats_2025.pdf).

## 1. Objet

Génère le fichier **DMET** — déclaration des *achats au détail de métaux ferreux et
non ferreux* (article **1649 bis du CGI**, dépôt électronique obligatoire art. **89 A**),
procédure DGFiP **TD/bilatéral**, campagne 2026 (achats **2025**).

Le fichier est déposé manuellement par le client sur son espace professionnel
impots.gouv.fr (service « Tiers déclarants »). **Il n'existe aucune API** : le module
produit le fichier, le dépôt reste une action humaine.

Échéance dure : **dépôt avant le 30 septembre 2026** (clôture définitive du guichet).

## 2. Contexte client

- **Agence Mosellane de l'Or** — SIREN `847642311`, **3 établissements** (un seul SIREN) :
  - Metz **siège** NIC `00033` (17 av. de Plantières, 57070) — APE 47.78C
  - Nancy NIC `00025` — Mondelange NIC `00041`
- ⚠️ **Odoo contient un SIRET de siège erroné** : `...00017` (établissement **fermé** au
  répertoire SIRENE). Le SIRET déclarant correct est **`84764231100033`**. À corriger
  dans `res.company` / `res.partner` (incrément « Lot 0 »).
- **Une seule déclaration** agrégée sous le SIRET du siège (CDC LIMINAIRE), montants
  **cumulés par vendeur** sur les 3 établissements. 6 vendeurs communs à 2 agences.
- Les **rachats** (flux entrant) sont des **avoirs client** (`account.move`,
  `move_type = 'out_refund'`) — cf. module `sales_confirm_popup`. Audit 2025 :
  **831 vendeurs**, **2 776 730 € TTC**, 1 657 lignes d'avoirs, **0 personne morale**.
- Le flux **sortant** (ventes aux fondeurs) n'est **pas** tracé dans Odoo → relève du
  livre de police (Phase 2), pas du DMET.

## 3. Architecture

Deux modules :

| Module | Rôle |
|---|---|
| `contacts_citizenship_id` *(à bumper)* | Socle identité `res.partner` : dépendance OCA `partner_firstname`, naissance structurée, pièce d'identité éclatée (R321-3 C. pénal) |
| **`fr_td_bilateral_metaux`** *(ce module)* | Génération DMET |

**Principe clé — `tools/` sans Odoo.** Toute la logique réglementaire vit dans
`tools/` **sans aucun `import odoo`**, donc testable en isolation
(`python3 -m unittest`). Les modèles/wizards Odoo (à venir) ne feront qu'appeler ces
fonctions.

```
tools/
  ascii_tools.py  translittération ASCII 0x20-0x7E (accents -> majuscules), digits_only
  fantoir.py      table des codes nature de voie (annexe 3 du CDC) + match longest-prefix
  address.py      parse_street() -> zones voie DGFiP ; normalize_cp() ; format_commune()
  dmet.py         dessins E/Q/T (positions fixes), générateur 550 car., nommage, gzip
  precheck.py     anomalies §8 (gravités B/S/N, seuils 1%/5%) -> check_file() verdict
tests/
  test_dmet_tools.py  16 tests (générateur, adresse, arrondi)
  test_precheck.py     9 tests (bloquantes, seuils, vendeur étranger)
```

Les 25 tests passent en isolation :
`cd addons && python3 -m unittest fr_td_bilateral_metaux.tests.test_dmet_tools fr_td_bilateral_metaux.tests.test_precheck`

## 4. Format du fichier (rappel)

- Séquentiel **format fixe, 550 caractères** par enregistrement + `\n` en position 551.
- Ordre : **E** (déclarant) → **Q** × n (un par vendeur) → **T** (totalisation).
- **UTF-8 sans BOM**, uniquement caractères **0x20–0x7E** (aucun accent).
- Zone « indicatif » **positions 1 à 19 identiques** sur E/Q/T
  (année 4 + SIRET 14 + type déclaration 1) ; **position 20** = type d'enregistrement.
- Numérique : cadré à droite, zéros à gauche. Alphanumérique : cadré à gauche, espaces.
- Montants : euros, **arrondi demi-supérieur** (`dmet.round_euro`, ≠ `round()` Python).
- Nommage : `DMET_2025_<SIREN>_<ordre 3ch>_<AAAAMMJJHHMMSS>.txt`, puis **gzip**
  (`.txt.gz`) puis **chiffrement GPG** clé publique DGFiP (`.txt.gz.gpg`).

Les dessins exacts (clé, position, longueur, classe) sont dans `tools/dmet.py`
(`FIELDS_E`, `FIELDS_Q`, `FIELDS_T`) et tracés à partir des fiches descriptives du CDC.

## 5. Décisions de conception

- **Normalisation à la génération**, non destructive : les données `res.partner`
  ne sont pas réécrites ; le format DGFiP est produit à la volée. Un nettoyage en base
  progressif relève de la Phase 2.
- **`country_id` NULL = France par défaut** (655/831 vendeurs sans pays). Mais un CP non
  conforme au format français **doit être signalé** au pré-contrôle (cas d'un vendeur
  étranger sans pays renseigné, ex. Porto).
- **Code postal** : département seul (`54`) complété en `54000` (CDC §6.3.1.4). CP
  bloquant avec seuil 5 % → viser 0 %.
- **Code INSEE commune** (Q024/E012) : laissé à `00000` (anomalie **non bloquante**)
  tant qu'un référentiel COG communes n'est pas embarqué. À arbitrer.
- **Civilité** (Q013) : **ne pas déduire** du prénom (assignation de genre erronée).
  557/831 manquantes → saisie client, ou zone à blanc (non bloquant).
- **Personnes morales = 0** aujourd'hui → seuil bloquant 1 % sur SIRET vendeur (Q005)
  sans objet, mais le code doit rester correct si des PM apparaissent.

## 6. État d'avancement

**Noyau pur-Python (testé en isolation, sans Odoo) — TERMINÉ :**
- [x] **Inc. 1** — noyau générateur (ascii_tools, dmet) + fichier d'exemple
- [x] **Inc. 2** — table FANTOIR + moteur d'adresse (address) + tests
- [x] **Inc. 5-core** — moteur de pré-contrôle (precheck) + tests seuils

**Couche Odoo — ÉCRITE et VALIDÉE en Docker (Odoo 18.0-20250606) :**
- [x] **Inc. 3** — bump `contacts_citizenship_id` 1.2.0 (naissance structurée, pièce
      d'identité éclatée, dépendance `partner_firstname`, migration `id_proof`) +
      mapping `res.partner._dmet_vendor_dict()`
- [x] **Inc. 4** — modèle `fr.dmet.declaration` + `fr.dmet.anomaly` (collecte des avoirs,
      pré-contrôle, génération .txt/.txt.gz)
- [x] **Inc. 5-ui** — écran anomalies (one2many, liens vers fiches) branché sur `precheck`
- [x] **Inc. 6** — vues (form/list), menu, `ir.model.access.csv`

Smoke test réalisé : `-i fr_td_bilateral_metaux` s'installe proprement (tables, vues
Odoo 18, sécurité, menu, migration `contacts_citizenship_id`) et **4 tests
d'intégration `TransactionCase` passent** (`tests/test_integration.py`).

## 9. Reste à faire pour la mise en production (recette sur copie de prod)

Validé en Docker sur base vierge — reste à éprouver sur les **vraies données** :
- `_collect_vendors` sur les **avoirs réels** (agrégation `out_refund` postés par vendeur) ;
- correction du **SIRET du siège** (`...00017` fermé -> `...00033`) dans `res.company` ;
- migration `contacts_citizenship_id` sur la base client (données `id_proof` existantes) ;
- chiffrement **GPG** (clé publique DGFiP) et **dépôt** sur impots.gouv.fr (action client) ;
- réintégrer les submodules `odooapps` / `eqp_odoo_addons` dans l'addons-path
  (retirés du smoke test car non initialisés dans ce clone).

### Rejouer le smoke test
```bash
docker compose -f .dev/docker-compose.yml up -d db
docker compose -f .dev/docker-compose.yml run --rm -T --no-deps --entrypoint "" odoo \
  /usr/bin/odoo -d smoke -u fr_td_bilateral_metaux --test-enable \
  --test-tags /fr_td_bilateral_metaux --stop-after-init --without-demo=all \
  --db_host db --db_user odoo --db_password odoo \
  --addons-path=/mnt/extra-addons,/more-addons/partner-contact
```

### Mapping `res.partner` → Q (à implémenter en Inc. 3)
- `partner_firstname` → Q015 (prénoms) ; `lastname` → Q014 (nom de famille)
- `birthdate` → Q007/008/009 ; naissance structurée → Q010/011/012
- `title` (M/MME) → Q013 ; `siret` → Q005 (si personne morale)
- `street`(+`street2`) → `address.parse_street` → Q020/021/023 ; `zip`/`city` → Q024-029
- montant Q030 = **somme annuelle** des `out_refund` postés du vendeur, arrondie

## 7. Tests

```bash
# En isolation (rapide, sans Odoo) :
cd addons && python3 -m unittest fr_td_bilateral_metaux.tests.test_dmet_tools -v

# Sous Odoo :
odoo -d <db> -i fr_td_bilateral_metaux --test-enable --stop-after-init
```

Les tests valident notamment les **exemples chiffrés du CDC** (§6.3.1.2 : zones voie
`N␣␣␣␣13`, `AV␣␣␣DES TILLEULS`, etc.), la longueur 550, le jeu de caractères, l'indicatif
1-19 et l'arrondi demi-supérieur.

## 8. Références réglementaires

- **CGI** art. 1649 bis (obligation), 89 A (voie électronique), 1729 B / 1736 / 1738 (sanctions)
- **Livre de police** (Phase 2) : CGI art. 537 + annexe IV art. 56 J quindecies/sexdecies ;
  Code pénal art. R321-1 à R321-12 (**R321-3** mentions, **R321-6-1** registre informatisé /
  intangibilité)
- **Paiement** : CMF art. **L112-6** (achats de métaux : espèces interdites sans seuil,
  virement sur compte au nom du vendeur)
- Cahier des charges DGFiP TD/bilatéral 2026 → PDF joint dans ce dossier.
