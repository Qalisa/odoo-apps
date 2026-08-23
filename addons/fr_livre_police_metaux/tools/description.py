# -*- coding: utf-8 -*-
"""Ce qu'un libellé de ligne ajoute à la désignation de l'article.

Odoo pré-remplit le champ « Description » d'une ligne avec la désignation de
l'article, suivie s'il y en a une de la description commerciale portée par sa
fiche. Le champ n'est donc **jamais vide**, et le déclarer obligatoire ne
dirait rien : « 18k Or 750 ‰(gr) » est un tarif, pas un objet.

Ce qui compte est ce que l'opérateur a **ajouté** — la ligne qui décrit ce qui
a été posé sur la balance. C'est déjà l'usage de la maison : « 18k Or
750 ‰(gr) ⏎ 1 BAGUE ».

Deux formes se présentent et se traitent de la même façon :

* le libellé commence par la désignation par défaut — le reste est la
  description ;
* l'article a été renommé sur la ligne, mais une deuxième ligne suit — c'est
  elle, la description.

Un libellé d'une seule ligne, fût-il différent du nom de l'article, ne décrit
rien : « 20 FRANCS OR (Non-Scellé) » nomme une variante, il ne désigne aucun
objet particulier.

Enfin, **ce que dit la fiche article ne décrit jamais un objet** : cette
phrase est la même sur toutes les lignes. La règle vaut aussi bien pour une
description commerciale que pour une consigne de saisie — « [Saisir la
nature] » posée en amorce sur la fiche apparaît sous chaque ligne, et le
registre ne doit pas la recevoir parce qu'on a écrit la vraie description
*en dessous* plutôt qu'à sa place.

Aucun ``import odoo`` ici : la règle se teste en isolation.
"""


def description_ajoutee(libelle, designation, texte_article=''):
    """Partie descriptive d'un libellé de ligne, éventuellement vide.

    ``designation`` est la désignation par défaut de l'article, telle
    qu'Odoo la produit — ``get_product_multiline_description_sale``.
    ``texte_article`` est la description portée par la fiche article, dont
    les lignes ne décrivent aucun objet en particulier.
    """
    texte = (libelle or '').strip()
    defaut = (designation or '').strip()
    if defaut and texte.startswith(defaut):
        reste = texte[len(defaut):]
    elif '\n' in texte:
        reste = texte.split('\n', 1)[1]
    else:
        reste = ''

    repetitions = {
        ligne.strip() for ligne in (texte_article or '').split('\n')
        if ligne.strip()}
    if repetitions:
        reste = '\n'.join(
            ligne for ligne in reste.split('\n')
            if ligne.strip() not in repetitions)
    return reste.strip()
