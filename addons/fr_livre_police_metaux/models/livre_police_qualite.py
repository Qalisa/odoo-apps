# -*- coding: utf-8 -*-
"""Qui vend — vocabulaire du registre.

**Ce que le droit exige.** L'art. R321-3 1° du code pénal veut que le registre
comporte « Les nom, prénoms, qualité et domicile de chaque personne qui a
vendu, apporté à l'échange ou remis en dépôt en vue de la vente un ou
plusieurs objets, ainsi que la nature, le numéro et la date de délivrance de
la pièce d'identité ». Le 2° reprend le mot pour la société : « la
dénomination et le siège de celle-ci ainsi que les nom, prénoms, qualité et
domicile du représentant ».

Le modèle officiel de registre intitule la colonne « NOM, PRENOM ou
dénomination sociale du vendeur, du déposant ou de l'apporteur à l'échange,
**qualité ou profession**, domicile ou siège social » (arrêté du 15 mai 2020,
annexe I, colonne 2) : les deux mots y sont donnés pour équivalents.

La mention est donc obligatoire au registre. **Le champ, lui, ne l'est pas**
dans Odoo : il ne bloque ni l'enregistrement d'un contact, ni la confirmation
d'un devis. C'est un choix d'exploitation — le comptoir doit pouvoir avancer
sur une fiche incomplète — et l'obligation est rappelée là où la saisie se
fait, sur la fiche contact.

Le libellé se fige dès qu'un contact le porte. Pas au nom de R321-6-1, qui
protège le registre lui-même et non cette liste : au nom du simple fait que
renommer « Retraité(e) » en « Salarié(e) » changerait d'un coup ce que
déclarent tous les vendeurs qui la portaient, sans que rien ne le dise. On
archive au lieu de renommer.
"""

from odoo import models, fields


class LivrePoliceQualite(models.Model):
    _name = 'livre.police.qualite'
    _inherit = 'livre.police.referentiel'
    _description = "Qualité ou profession du vendeur"

    _police_usage_noms = ("fiche contact", "fiches contact")
    _police_effet_renommage = ("changerait ce que déclarent ces vendeurs, "
                               "sans laisser de trace")

    usage_count = fields.Integer(
        string="Fiches contact",
        help="Nombre de contacts portant cette qualité, archivés compris. "
             "Au-delà de zéro, le libellé est figé.",
    )

    def _police_usage_domain(self):
        return 'res.partner', [('police_qualite_id', 'in', self.ids)]
