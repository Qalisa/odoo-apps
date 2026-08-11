# -*- coding: utf-8 -*-
"""Dérivation du poids d'une ligne d'achat, et vraisemblance du résultat.

Le livre de police (art. R321-4 du code pénal) exige la désignation de
l'objet et, pour les métaux précieux, son poids. Les caractéristiques de
chaque objet — nature, titre, poids unitaire — vivent sur l'article
(``product.template``) : c'est lui le référentiel. Ce module ne porte que
les règles qui s'y appliquent.

Trois régimes de saisie coexistent dans les avoirs de rachat :

``gram``
    la quantité de la ligne *est* le poids en grammes (« 18 carats (18k) Or
    750 ‰ (g) », « Argent (g) », « Platine (g) »…). Quantités fractionnaires.
``unit``
    la quantité est un nombre de pièces ou de lingotins de poids normalisé
    (« 20 Francs Or », « Lingot 50 g Or 999 ‰ »…). Le poids se déduit du
    poids unitaire porté par l'article.
``lot``
    la ligne est un lot hétérogène facturé forfaitairement (« Lot de pièces
    Argent »…). Aucun poids n'est déductible : il doit être saisi.

Aucun ``import odoo`` ici : la logique est testable en isolation.
"""

#: Régimes de saisie de la quantité, cf. docstring du module.
MODES = ('gram', 'unit', 'lot')


def derive_weight(mode, unit_weight, quantity):
    """Poids en grammes déductible d'une ligne, ou ``None``.

    ``None`` signifie « non déductible » (lot, article hors métal, poids
    unitaire manquant) : le poids devra être saisi.
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
