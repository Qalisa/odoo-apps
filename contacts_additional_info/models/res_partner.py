# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'
    
    birthdate = fields.Date(string='Date de Naissance')
    birthplace = fields.Char(string='Lieu de Naissance')
    national_id_card_number = fields.Char(string='Numéro de Carte Nationale d\'Identité', help="Numéro de la Carte Nationale d'Identité")

class AccountMove(models.Model):
    _inherit = 'account.move'
    
    # Champs calculés pour afficher les informations du partenaire
    partner_birthdate = fields.Date(related='partner_id.birthdate', string='Date de Naissance', readonly=True)
    partner_birthplace = fields.Char(related='partner_id.birthplace', string='Lieu de Naissance', readonly=True)
    partner_national_id_card_number = fields.Char(related='partner_id.national_id_card_number', string='N° CNI', readonly=True)

class SaleOrder(models.Model):
    _inherit = 'sale.order'
    
    # Champs calculés pour afficher les informations du partenaire
    partner_birthdate = fields.Date(related='partner_id.birthdate', string='Date de Naissance', readonly=True)
    partner_birthplace = fields.Char(related='partner_id.birthplace', string='Lieu de Naissance', readonly=True)
    partner_national_id_card_number = fields.Char(related='partner_id.national_id_card_number', string='N° CNI', readonly=True)