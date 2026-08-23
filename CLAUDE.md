# Conventions du dépôt

Addons Odoo 18 CE pour un négociant en métaux précieux. Plusieurs modules
matérialisent des obligations légales — livre de police, registre des métaux
précieux, déclaration d'achats au détail de métaux. Les articles qu'ils citent
ont été vérifiés un à un sur Légifrance : ne les paraphrase pas, ne les
« simplifie » pas, et ne déplace pas une citation d'un texte à l'autre sans la
revérifier.

## Tests

Cadre toujours l'exécution sur nos modules :

```
--test-tags /fr_numismatics_metals,/fr_td_bilateral_metaux,/product_creation_control,/fr_livre_police
```

Sans ce drapeau, les suites d'`account`, `sale` et `product` tournent aussi et
échouent par centaines : nos modules rendent obligatoires, sur tout article de
type « bien », des mentions que les fixtures standard ne remplissent pas. Ces
échecs ne disent rien de notre code, ils noient le signal utile. Ce sont des
suites qu'on ne possède pas et qu'on ne corrigera pas.

**Pas de tests défensifs.** N'écris pas de test pour un comportement qu'on
suppose déjà correct : le comportement est tenu pour acquis.

Un test n'entre au dépôt que dans un seul cas — un comportement s'est révélé
faux, il a fallu un correctif, et le test constate le comportement attendu
**depuis** ce correctif. Le test documente alors un cas limite réellement
rencontré, pas une intention.

Écrire des tests jetables pendant la mise au point reste utile ; les livrer ne
l'est pas.

## Commits

Un commit ne touche **qu'un seul module** sous `addons/`. Les fichiers hors
`addons/` ne comptent pas dans cette règle.

Quand deux modules doivent bouger ensemble — un champ retiré d'un côté, son
lecteur mis à jour de l'autre — les séparer produirait un commit intermédiaire
cassé. C'est légitime, mais ça se justifie en pied de message :

```
Multi-module: le champ retire de contacts_citizenship_id est lu par fr_td_bilateral_metaux
```

Messages en français, sans accents dans le sujet, préfixes conventionnels :
`feat(portee):`, `fix(portee):`, `docs(portee):`, `test(portee):`. Le corps dit
*pourquoi*, jamais *quoi* — le diff dit déjà quoi.

## Développement local

Base de données et serveur via `.dev/docker-compose.yml`. Une exécution ponctuelle :

```
docker compose -f .dev/docker-compose.yml run --rm --no-deps -T \
  --entrypoint /usr/bin/odoo odoo -d <base> \
  --db_host db --db_user odoo --db_password odoo --no-http --stop-after-init \
  -u <modules> \
  --addons-path "/mnt/extra-addons,/more-addons/odooapps,/more-addons/eqp_odoo_addons,/more-addons/partner-contact,/more-addons/l10n-france,/more-addons/server-tools"
```

Le service `db` doit tourner (`docker compose -f .dev/docker-compose.yml up -d db`) :
`--no-deps` ne le démarre pas.

## Dépôt public

Ce dépôt est ouvert. Aucune donnée nominative de client n'y entre : ni SIREN,
ni SIRET, ni adresse, ni nom de personne. Les exemples utilisent des
valeurs fictives, et les documents de passation restent hors git.
