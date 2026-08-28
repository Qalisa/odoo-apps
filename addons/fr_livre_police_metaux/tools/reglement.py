# -*- coding: utf-8 -*-
"""Les moyens de règlement qu'un rachat de métaux peut employer.

La liste est fermée, et elle l'est par la loi. « Lorsqu'un professionnel
achète des métaux à un particulier ou à un autre professionnel, le paiement
est effectué par chèque barré ou par virement à un compte ouvert au nom du
vendeur. Le non-respect de cette obligation est puni par une contravention de
cinquième classe » (code monétaire et financier, art. L112-6, version en
vigueur depuis le 15 juin 2025).

Le texte ne pose ni seuil ni exception : les espèces sont exclues d'un rachat
quel qu'en soit le montant. Cette liste n'en propose donc pas — non par
prudence, mais parce qu'aucun rachat ne peut légalement s'y régler.

D'où une sélection et non un référentiel administrable, à la différence de la
provenance ou de la qualité du vendeur : celles-là s'enrichissent au comptoir,
celle-ci ne peut s'enrichir que si le texte change. Ajouter une valeur doit
donc coûter un commit, et se justifier par un article.

La carte de paiement figurait dans une rédaction antérieure de l'article ;
elle a disparu de celle en vigueur, et n'est pas reprise ici.
"""

MODES_REGLEMENT = [
    ('cheque', "Chèque barré"),
    ('virement', "Virement"),
]
