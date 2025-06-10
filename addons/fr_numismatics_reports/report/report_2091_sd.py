from odoo import api, models, _
from odoo.exceptions import UserError


class ReportTax(models.AbstractModel):
    _name = 'report.fr_numismatics_reports.report_2091_sd'
    _description = 'Aide pour Cerfa 2091-SD (Déclaration TMP / TFOP)'

    @api.model
    def _get_report_values(self, docids, data=None):
        if not data.get('form'):
            raise UserError(_("Form content is missing, this report cannot be printed."))
        return {
            'data': data['form'],
            'lines': self.get_lines(data.get('form')),
        }

    # SELECT aml.invoice_date, aml.move_name, aml.quantity, aml.name, aml.amount_currency, curr.symbol currency, acctx.name for_tax
    # FROM account_move_line aml
    # LEFT JOIN account_move_line_account_tax_rel aml_rel ON (aml.id = aml_rel.account_move_line_id)
    # LEFT JOIN account_tax acctx ON (aml_rel.account_tax_id = acctx.id)
    # LEFT JOIN res_currency curr ON (aml.currency_id = curr.id)
    # WHERE  aml.display_type = 'product' AND aml.invoice_date is not NULL AND acctx.tax_group_id = 44 AND aml.quantity > 0
    # ORDER BY aml.invoice_date, aml.move_name

    def _sql_from_amls(self):
        sql = """SELECT "account_move_line".tax_line_id, SUM("account_move_line".credit), SUM("account_move_line".tax_base_amount) 
                 FROM %s
                 INNER JOIN account_tax t ON ("account_move_line".tax_line_id = t.id)
                 WHERE %s
                 GROUP BY "account_move_line".tax_line_id"""
        return sql

    def _compute_from_amls(self, options, taxes):
        #compute the tax amount
        sql = self._sql_from_amls()
        tables, where_clause, where_params = self.env['account.move.line']._query_get()
        query = sql % (tables, where_clause)
        self.env.cr.execute(query, where_params)
        results = self.env.cr.fetchall()
        for result in results:
            if result[0] in taxes:
                taxes[result[0]]['tax'] = abs(result[1])
                taxes[result[0]]['net'] = abs(result[2])

    @api.model
    def get_lines(self, options):
        taxes = {}
        for tax in self.env['account.tax'].search([('type_tax_use', '!=', 'none')]):
            if tax.children_tax_ids:
                for child in tax.children_tax_ids:
                    if child.type_tax_use != 'none':
                        continue
                    taxes[child.id] = {'tax': 0, 'net': 0, 'name': child.name, 'type': tax.type_tax_use}
            else:
                taxes[tax.id] = {'tax': 0, 'net': 0, 'name': tax.name, 'type': tax.type_tax_use}
        self.with_context(date_from=options['date_from'], date_to=options['date_to'],
                          state=options['target_move'],
                          strict_range=True)._compute_from_amls(options, taxes)
        groups = dict((tp, []) for tp in ['sale', 'purchase'])
        for tax in taxes.values():
            if tax['tax']:
                groups[tax['type']].append(tax)
        return groups
