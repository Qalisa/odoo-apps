# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    birthdate = fields.Date(string='Date de Naissance')
    birthplace = fields.Char(string='Lieu de Naissance')
    id_proof = fields.Char(string="Justificatif d'identité (CNI, Passeport, Permis, Titre de séjour...)", help="Libellé de la preuve de l'identité fournie (carte d'identité nationnale, titre de séjour, permis, passport...) accompagné du numéro d'identité associé")
