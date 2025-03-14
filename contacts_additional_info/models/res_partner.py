# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    birthdate = fields.Date(string='Date de Naissance')
    birthplace = fields.Char(string='Lieu de Naissance')
    id_number = fields.Char(string='Numéro CNI')