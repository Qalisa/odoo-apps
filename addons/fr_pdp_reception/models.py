import logging

from odoo import SUPERUSER_ID, models

_logger = logging.getLogger(__name__)


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


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    def peppol_get_new_documents(self):
        # Une facture recue est ecrite par la plateforme qui la livre, pas par
        # celui qui clique sur « relever » : sans cela, l'historique de la
        # piece et du fournisseur cree a la volee lui en attribue l'auteur.
        # La releve automatique tourne deja sous OdooBot ; le bouton s'aligne.
        _logger.info("Releve de la plateforme declenchee par %s", self.env.user.login)
        return super(AccountJournal, self.with_user(SUPERUSER_ID)).peppol_get_new_documents()
