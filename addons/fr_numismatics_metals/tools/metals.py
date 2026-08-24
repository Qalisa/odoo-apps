# -*- coding: utf-8 -*-
"""Dérivation du poids d'une ligne d'achat, et vraisemblance du résultat.

Le livre de police (CGI, ann. IV, art. 56 J quindecies) exige le poids de
l'objet et, pour les métaux précieux, son poids. Les caractéristiques de
chaque objet — nature, titre, poids unitaire — vivent sur l'article
(``product.template``) : c'est lui le référentiel. Ce module ne porte que
les règles qui s'y appliquent.

Deux régimes de saisie coexistent dans les avoirs de rachat :

``gram``
    la quantité de la ligne *est* le poids en grammes (« 18 carats (18k) Or
    750 ‰ (g) », « Argent (g) », « Platine (g) »…). Quantités fractionnaires.
``unit``
    la quantité est un nombre de pièces ou de lingotins de poids normalisé
    (« 20 Francs Or », « Lingot 50 g Or 999 ‰ »…). Le poids se déduit du
    poids unitaire porté par l'article.

Il n'y a pas de troisième régime pour les lots hétérogènes. Un lot se pèse :
il entre au gramme, et son poids est celui que la balance affiche. Ce qu'un
lot n'a pas, c'est un *titre* unique — et cela se dit ailleurs, par la case
« Considérer en lot de titres » de l'article. Séparer les deux questions
évite qu'un lot arrive au registre sans poids, ce que le CGI n'admet pas.

Aucun ``import odoo`` ici : la logique est testable en isolation.
"""

#: Régimes de saisie de la quantité, cf. docstring du module.
MODES = ('gram', 'unit')


def derive_weight(mode, unit_weight, quantity):
    """Poids en grammes déductible d'une ligne, ou ``None``.

    ``None`` ne subsiste que pour un article hors métal, ou pour un article
    « à la pièce » dont le poids unitaire manque — cas que la contrainte de
    saisie interdit, et qui ne survit que sur les articles entrés avant elle.
    """
    if mode == 'gram':
        return quantity
    if mode == 'unit' and unit_weight:
        return quantity * unit_weight
    return None


def price_per_gram(amount, weight):
    """Prix au gramme constaté sur une ligne, ou ``None``.

    Rien à paramétrer : ce prix n'est pas une donnée du module, c'est une
    conséquence de l'article et de ce que le vendeur a saisi. L'afficher
    suffit — une ligne « Argent (g) » de quantité 1 facturée 3 500 € se
    dénonce d'elle-même à 3 500 €/g, sans qu'aucun seuil n'ait à être tenu
    à jour dans le code.
    """
    if not weight or not amount:
        return None
    return abs(amount) / abs(weight)
