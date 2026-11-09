from odoo import api, models, tools

# Les menus de la comptabilite de la societe. Ils restent ouverts a qui
# detient « Facturation », et c'est le droit qu'un comptoir garde pour
# facturer : un groupe ne peut pas les lui fermer, d'ou ce filtre.
MENUS_FERMES = (
    'account.menu_finance_payables',
    'account.menu_finance_entries',
    'account.menu_finance_reports',
    'account.menu_finance_configuration',
    'account.menu_board_journal_1',
    # L'aide à la déclaration de TVA : un état de la société.
    'fr_numismatics_reports.menu_report',
)


class IrUiMenu(models.Model):
    _inherit = 'ir.ui.menu'

    @api.model
    @tools.ormcache('frozenset(self.env.user.groups_id.ids)', 'debug')
    def _visible_menu_ids(self, debug=False):
        visibles = super()._visible_menu_ids(debug)
        if not self.env.user.has_group(
                'accounting_access_control.group_sans_comptabilite'):
            return visibles
        fermes = self.env['ir.ui.menu'].sudo().with_context(
            **{'ir.ui.menu.full_list': True}).search([
                ('id', 'child_of', [
                    menu.id for xml_id in MENUS_FERMES
                    if (menu := self.env.ref(xml_id, raise_if_not_found=False))
                ])])
        return frozenset(visibles - set(fermes.ids))
