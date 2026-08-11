# -*- coding: utf-8 -*-

from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    police_start_date = fields.Date(
        related='company_id.police_start_date', readonly=False,
        string="Début du livre de police",
    )
    police_sequence_prefix = fields.Char(
        related='company_id.police_sequence_prefix', readonly=False,
        string="Préfixe des numéros d'ordre",
    )
