from odoo import api, models, _
from odoo.exceptions import UserError
from itertools import groupby,batched,product
from operator import itemgetter

class TwoZeroNineOneSDPDFReportModel(models.AbstractModel):
    _name = 'report.fr_numismatics_reports.report_2091_sd'
    _description = 'Aide à la saisie pour Cerfa 2091-SD (Déclaration TMP / TFOP)'

    @api.model
    def _get_report_values(self, docids, data=None):
        # check referenced tax groups exist and are configured 
        ICP = self.env['ir.config_parameter']
        tfop_group_id = int(ICP.get_param('fr_numismatics_reports.tax_group_tfop_id'))
        tmp_group_id = int(ICP.get_param('fr_numismatics_reports.tax_group_tmp_id'))
        tax_group_ids = [tfop_group_id, tmp_group_id]
        found_tax_groups = self.env['account.tax.group'].browse(tax_group_ids).exists()
        if len(found_tax_groups) != len(tax_group_ids):
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

        query = f"""SELECT 
                aml.move_name, 
                aml.invoice_date, 
                aml.company_id,
                aml.quantity, 
                aml.name, 
                aml.price_total, 
                aml.currency_id,
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
            LEFT JOIN 
                account_move am ON (aml.move_id = am.id)
            WHERE 
                am.state = 'posted'
                AND aml.display_type = 'product' 
                AND aml.invoice_date is not NULL 
                AND acctx.tax_group_id IN %s
                AND aml.company_id IN %s
                AND aml.invoice_date BETWEEN %s AND %s
                {'AND aml.quantity > 0' if ignore_cutoff else ''}
            ORDER BY 
                aml.invoice_date ASC, 
                aml.move_name ASC
        """

        # prepare query
        query = self.env.cr.mogrify(query, (
            tuple(tax_group_ids), 
            tuple(company_ids.ids), 
            start_date, end_date, 
        )).decode('utf-8')

        # run it and get values
        self.env.cr.execute(query)
        results = self.env.cr.dictfetchall()

        # group by company
        grouped_by_companies = {}
        if split_by_company:
            # ensure all expected companies is present
            for company_id in company_ids.ids:
                grouped_by_companies[company_id] = []
            # fill with data (if any fetched)
            for company_id, group in groupby(results, key=itemgetter('company_id')):
                grouped_by_companies[company_id] = list(group)
        else:
            # else, gather all ids as first company's results
            grouped_by_companies[company_ids.ids[0]] = results

        # split
        grouped_by_companies_by_batches = {'companies': {}}
        for company_id, rows in grouped_by_companies.items():
            grouped_by_companies_by_batches['companies'][company_id] = {
                'company': self.env['res.company'].browse(company_id).exists(),
                'batches': [],
            }
            batches = list(batched(rows, paginate))
            for i, batch in enumerate(batches):
                grouped_by_companies_by_batches['companies'][company_id]['batches'].append({
                    'items': batch,
                    'i': i + 1,
                    'i_of': len(batches),
                    'total': sum(record['price_total'] for record in batch),
                    'total_tfop': sum(record['price_total'] for record in batch if record['tax_group_id'] == tfop_group_id),
                    'total_tmp': sum(record['price_total'] for record in batch if record['tax_group_id'] == tmp_group_id),
                })

        return {
            'doc_ids': docids,
            'doc_model': 'account.taxes.cerfa_report.wizard',
            'docs': wizard,
            'results': grouped_by_companies_by_batches,
            'tfop_group_id': tfop_group_id, 
            'tmp_group_id': tmp_group_id,
        }
