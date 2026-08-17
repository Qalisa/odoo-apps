from odoo import api, fields, models

from .product import PARAMETRE, VUES


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    product_allow_inline_creation = fields.Boolean(
        string="Autoriser la création d'articles à la volée",
        config_parameter=PARAMETRE,
        help="Décoché, les entrées « Créer \"…\" » et « Créer et modifier… » "
             "disparaissent des lignes de devis, de facture et d'avoir, et un "
             "article ne peut plus être créé par son seul nom. Un bien doit "
             "porter dès sa création les mentions exigées au livre de police "
             "(art. R321-3 du code pénal) et au registre des métaux précieux "
             "(art. 56 J quindecies de l'annexe IV au CGI), qui ne peuvent pas "
             "être saisies depuis une ligne de document.",
    )

    def set_values(self):
        res = super().set_values()
        # Le paramètre gouverne le serveur ; les vues, elles, doivent être
        # (dés)activées pour que les entrées disparaissent de l'interface.
        self._appliquer_vues_creation_a_la_volee()
        return res

    @api.model
    def _appliquer_vues_creation_a_la_volee(self):
        autorise = self.env["ir.config_parameter"].sudo().get_param(PARAMETRE)
        autorise = str(autorise).strip().lower() in ("true", "1")
        vues = self.env["ir.ui.view"].sudo().browse([
            vue.id for vue in (
                self.env.ref(xmlid, raise_if_not_found=False) for xmlid in VUES
            ) if vue
        ])
        vues.filtered(lambda v: v.active == autorise).write({"active": not autorise})
