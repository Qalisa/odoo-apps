from odoo import models


class AccountEdiCii(models.AbstractModel):
    _inherit = 'account.edi.cii'

    def _import_cii_invoice_line_add_name(self, collected_values):
        super()._import_cii_invoice_line_add_name(collected_values)
        produit = './/{*}SpecifiedTradeProduct/{*}'
        intitule = collected_values['line_tree'].findtext(produit + 'Name')
        description = collected_values['line_tree'].findtext(produit + 'Description')
        if intitule and description and description != intitule:
            nom = f"{intitule}\n{description}"
            collected_values['name'] = collected_values['to_write']['name'] = nom
