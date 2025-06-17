from odoo import api, models, _
from odoo.exceptions import UserError


class TwoZeroNineOneSDPDFReportModel(models.AbstractModel):
    _name = 'report.fr_numismatics_reports.report_2091_sd'
    _description = 'Aide à la saisie pour Cerfa 2091-SD (Déclaration TMP / TFOP)'

    @api.model
    def _get_report_values(self, docids, data=None):
        # check settings are set
        ICP = self.env['ir.config_parameter']
        tfop_tax_group_id = ICP.get_param('fr_numismatics_reports.tax_group_tfop_id')
        tmp_tax_group_id = ICP.get_param('fr_numismatics_reports.tax_group_tmp_id')
        if tfop_tax_group_id is False or tmp_tax_group_id is False:
            raise UserError("""
Impossible de générer vos rapports pour le moment, des éléments de configuration manquent:

Merci de configurer les groupes de taxes à faire apparaître dans `Menu > Paramètres > Facturation > Rapports d'aide à la saisie (Cerfa)`.
""")

        # extract parameters
        wizard = self.env['account.taxes.cerfa_report.wizard'].browse(docids)
        company_ids = wizard.company_ids
        start_date = wizard.start_date
        end_date = wizard.end_date
        ignore_cutoff = wizard.ignore_cutoff
        split_by_company = wizard.split_by_company
        paginate = wizard.paginate

        query = """SELECT 
                aml.move_name, 
                aml.invoice_date, 
                aml.company_id,
                aml.quantity, 
                aml.name, 
                aml.amount_currency, 
                curr.symbol currency,
                acctx.tax_group_id, 
                acctx.name for_tax
            FROM 
                account_move_line aml
            LEFT JOIN 
                account_move_line_account_tax_rel aml_rel ON (aml.id = aml_rel.account_move_line_id)
            LEFT JOIN 
                account_tax acctx ON (aml_rel.account_tax_id = acctx.id)
            LEFT JOIN 
                res_currency curr ON (aml.currency_id = curr.id)
            WHERE 
                aml.display_type = 'product' 
                AND aml.invoice_date is not NULL 
                AND acctx.tax_group_id IN %s
                AND aml.company_id IN %s
                AND aml.invoice_date BETWEEN %s AND %s
                """ + 'AND aml.quantity > 0' if ignore_cutoff else '' + """
            ORDER BY 
                aml.invoice_date ASC, 
                aml.move_name ASC
        """

        # prepare query
        tax_groups_ids = [int(tfop_tax_group_id), int(tmp_tax_group_id)]
        query = self.env.cr.mogrify(query, (
            tuple(tax_groups_ids), 
            tuple(company_ids.ids), 
            start_date, end_date, 
        )).decode('utf-8')

        # run it and get values
        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()

        return {
            'doc_ids': docids,
            'doc_model': 'account.taxes.cerfa_report.wizard',
            'docs': wizard,
            'results': results,
        }

    # @api.model
    # def _get_report_values(self, docids, data=None):
    #     if not data.get('form'):
    #         raise UserError(_("Form content is missing, this report cannot be printed."))
    #     return {
    #         'data': data['form'],
    #         'lines': self.get_lines(data.get('form')),
    #     }



    # def _sql_from_amls(self):
    #     sql = """SELECT "account_move_line".tax_line_id, SUM("account_move_line".credit), SUM("account_move_line".tax_base_amount) 
    #              FROM %s
    #              INNER JOIN account_tax t ON ("account_move_line".tax_line_id = t.id)
    #              WHERE %s
    #              GROUP BY "account_move_line".tax_line_id"""
    #     return sql

    # def _compute_from_amls(self, options, taxes):
    #     #compute the tax amount
    #     sql = self._sql_from_amls()
    #     tables, where_clause, where_params = self.env['account.move.line']._query_get()
    #     query = sql % (tables, where_clause)
    #     self.env.cr.execute(query, where_params)
    #     results = self.env.cr.fetchall()
    #     for result in results:
    #         if result[0] in taxes:
    #             taxes[result[0]]['tax'] = abs(result[1])
    #             taxes[result[0]]['net'] = abs(result[2])

    # @api.model
    # def get_lines(self, options):
    #     taxes = {}
    #     for tax in self.env['account.tax'].search([('type_tax_use', '!=', 'none')]):
    #         if tax.children_tax_ids:
    #             for child in tax.children_tax_ids:
    #                 if child.type_tax_use != 'none':
    #                     continue
    #                 taxes[child.id] = {'tax': 0, 'net': 0, 'name': child.name, 'type': tax.type_tax_use}
    #         else:
    #             taxes[tax.id] = {'tax': 0, 'net': 0, 'name': tax.name, 'type': tax.type_tax_use}
    #     self.with_context(date_from=options['date_from'], date_to=options['date_to'],
    #                       state=options['target_move'],
    #                       strict_range=True)._compute_from_amls(options, taxes)
    #     groups = dict((tp, []) for tp in ['sale', 'purchase'])
    #     for tax in taxes.values():
    #         if tax['tax']:
    #             groups[tax['type']].append(tax)
    #     return groups
