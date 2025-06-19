from odoo import models, fields, api
from odoo.exceptions import ValidationError
from datetime import date, timedelta

min_paginate = 1
max_paginate = 50

class CerfaReportWizard(models.TransientModel):
    _name = 'account.taxes.cerfa_report.wizard'
    _description = "Formulaire de génération de rapport d'aide à la saisie des Cerfa (Taxes)"

    ##
    ## fields
    ##

    company_ids = fields.Many2many('res.company', 
        string='Sociétés à inclure', required=True, 
        default=lambda self: self.env.context.get('allowed_company_ids', [])
    )

    main_company_id = fields.Many2one('res.company', 
        string="Société déclarante", required=True,
        help="Si génération multi-établissement, définit l'établissement déclarant parmi les entreprises selectionnées.",
        domain="[('id', 'in', company_ids)]"
    )
    show_multi_company_options = fields.Boolean(
        string="Afficher les options dans le cadre d'une génération multi-établissements",
        compute='_compute_show_multi_company_options',
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
        help="Si génération multi-établissement, crée des rapports individualisés par sociétés gérées (et selectionnées) sur la période choisie."
    )
    paginate = fields.Integer(
        string='Lignes maximum par rapport', default=21,
         help="Regroupe les lignes facturées et taxées par lots; permet notamment de s'adapter à l'identique au format restreint en nombre de lignes du CERFA."
    )
    ignore_cutoff = fields.Boolean(
        string='Ignorer les remises ?', default=True,
        help="Par mauvaises manipulations, des lignes indépendantes correspondant à des réductions appliquées aux lignes taxées peuvent apparaître sur les rapports. Cochez cette option pour les ignorer."
    )

    ##
    ## rules / triggers
    ##

    @api.constrains('paginate')
    def _check_paginate_field(self):
        for record in self:
            if not (min_paginate <= record.paginate <= max_paginate):
                raise ValidationError(f"Le nombre de lignes maximum par rapport doit être entre {min_paginate} et {max_paginate}.")

    @api.depends('company_ids')
    def _compute_show_multi_company_options(self):
        for record in self:
            record.show_multi_company_options = len(record.company_ids) > 1

    @api.onchange('company_ids')
    def _onchange_company_ids(self):
        #
        if len(self.company_ids) == 1 or len(self.main_company_id) == 0:
            self.main_company_id = self.company_ids[0]
        elif len(self.company_ids) == 0:
            self.main_company_id = False

        #
        if len(self.company_ids) < 2:
            self.split_by_company = False

    ##
    ## metadata
    ##

    def _get_report_base_filename(self):
        self.ensure_one()
        return f"Aide_2091_SD__{self.start_date.strftime('%Y-%m-%d')}__{self.end_date.strftime('%Y-%m-%d')}"

    ##
    ## actions
    ##

    def action_confirm(self):
        #
        if self.start_date > self.end_date:
            raise ValidationError("La date de début de période ne peut pas se produire avant la date de fin de période.")

        #
        self.ensure_one()

        #
        return self.env.ref('fr_numismatics_reports.action_pdf_report_cerfa_2091_sd').report_action(self)