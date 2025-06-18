from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta

min_paginate = 1
max_paginate = 50

class CerfaReportWizard(models.TransientModel):
    _name = 'account.taxes.cerfa_report.wizard'
    _description = "Formulaire de génération de rapport d'aide à la saisie des Cerfa (Taxes)"

    company_ids = fields.Many2many('res.company', 
        string='Sociétés à inclure', required=True, 
        default=lambda self: self.env.context.get('allowed_company_ids', []),
        help="La 1ère société selectionnée sera celle présentée comme déclarante par défaut."
    )

    start_date = fields.Date(
        string='Début de période', required=True, 
        default=lambda self: fields.Date.to_string(date.today().replace(day=1).__sub__(timedelta(days=1)).replace(day=1))
    )
    end_date = fields.Date(
        string='Fin de période', required=True, 
        default=lambda self: fields.Date.to_string(date.today().replace(day=1).__sub__(timedelta(days=1)))
    )
    split_by_company = fields.Boolean(
        string='Distinguer par entreprise ?', default=False,
        help="Si multi-établissement, crée des rapports individualisés par sociétés gérées (et selectionnées) sur la période choisie."
    )
    paginate = fields.Integer(
        string='Lignes maximum par rapport', default=21,
         help="Regroupe les lignes facturées et taxées par lots; permet notamment de s'adapter à l'identique au format restreint en nombre de lignes du CERFA."
    )
    ignore_cutoff = fields.Boolean(
        string='Ignorer les remises ?', default=True,
        help="Par mauvaises manipulations, des lignes indépendantes correspondant à des réductions appliquées aux lignes taxées peuvent apparaître sur les rapports. Cochez cette option pour les ignorer."
    )

    @api.constrains('paginate')
    def _check_my_integer_field(self):
        for record in self:
            if not (min_paginate <= record.paginate <= max_paginate):
                raise ValidationError(f"Le nombre de lignes maximum par rapport doit être entre {min_paginate} et {max_paginate}.")

    def action_confirm(self):
        #
        if self.start_date > self.end_date:
            raise ValidationError("La date de début de période ne peut pas se produire avant la date de fin de période.")

        #
        self.ensure_one()

        #
        return self.env.ref('fr_numismatics_reports.action_pdf_report_cerfa_2091_sd').report_action(self)