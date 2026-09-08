# -*- coding: utf-8 -*-
"""Le responsable d'un établissement.

« Un registre est tenu pour chaque établissement » (c. pén., art. R321-6), et
quelqu'un en répond. Odoo ne connaît pas cette notion : une société y a des
utilisateurs, pas de responsable, et les neuf comptes de la maison ont accès
aux trois comptoirs.

Ce champ la nomme, pour un usage précis : la réception d'un transfert entre
établissements. Celui qui envoie ne constate pas lui-même que la marchandise
est arrivée — c'est le comptoir d'arrivée qui le dit, et il faut donc pouvoir
dire qui parle pour lui.
"""

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    police_responsable_id = fields.Many2one(
        'res.users', string="Responsable de l'établissement",
        help="La personne qui répond de ce comptoir. Elle seule — ou qui "
             "porte le droit « Livre de police - responsable » — peut "
             "réceptionner un transfert arrivant ici.\n\n"
             "Laissé vide, aucune réception n'est possible sans ce droit : "
             "mieux vaut un blocage explicite qu'une réception que personne "
             "n'a endossée.",
    )
