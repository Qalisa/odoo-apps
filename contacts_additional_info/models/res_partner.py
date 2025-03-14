# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    birthdate = fields.Date(string='Date de Naissance')
    birthplace = fields.Char(string='Lieu de Naissance')
    national_id_card_number = fields.Char(string='Numéro de Carte Nationale d\'Identité', help="Numéro de la Carte Nationale d'Identité")
