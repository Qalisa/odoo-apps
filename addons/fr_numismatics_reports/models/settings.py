from odoo import models, fields, api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    tax_group_tfop_id = fields.Many2one(
        'account.tax.group',
        string='Groupe de taxe pour la TFOP',
        help="Définissez obligatoirement ce groupe afin que les rapports d'aide à la complétion de Cerfa puissent être correctement générés.",
        config_parameter='fr_numismatics_reports.tax_group_tfop_id'
    )

    tax_group_tmp_id = fields.Many2one(
        'account.tax.group',
        string='Groupe de taxe pour la TMP',
        help="Définissez obligatoirement ce groupe afin que les rapports d'aide à la complétion de Cerfa puissent être correctement générés.",
        config_parameter='fr_numismatics_reports.tax_group_tmp_id'
    )
