from odoo import _, api, models
from odoo.exceptions import UserError

PARAMETRE = "product_creation_control.allow_inline_creation"

# Vues neutralisant la création depuis les lignes de document. Elles sont
# activées ou désactivées avec le paramètre, depuis `res.config.settings`.
VUES = (
    "product_creation_control.view_order_form_no_inline_product",
    "product_creation_control.view_move_form_no_inline_product",
)


def creation_a_la_volee_autorisee(env):
    """L'option des paramètres est-elle cochée ?

    Le paramètre est absent tant que personne ne l'a coché : la création à la
    volée est donc interdite dès l'installation, sans donnée à charger.
    """
    valeur = env["ir.config_parameter"].sudo().get_param(PARAMETRE)
    return str(valeur).strip().lower() in ("true", "1")


def _refuser_creation_a_la_volee(env):
    """Interdit la création d'un article par son seul nom.

    ``name_create`` est ce qu'appelle la combobox derrière « Créer "…" ». Un
    article ainsi créé ne porte que son nom, alors qu'un bien doit porter dès
    l'origine les mentions du livre de police et, pour les métaux précieux,
    la nature du métal, son titre et son poids.

    Le mode super-utilisateur reste ouvert : c'est par lui que passent
    l'installation des modules et les scripts de reprise, qui ne sont pas des
    saisies d'utilisateur.
    """
    if env.su or creation_a_la_volee_autorisee(env):
        return
    raise UserError(_(
        "La création d'un article à la volée est désactivée.\n\n"
        "Un article se crée depuis sa fiche complète (Ventes ▸ Articles), afin "
        "que les mentions obligatoires au livre de police et au registre des "
        "métaux précieux soient renseignées dès sa création."
    ))


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.model
    def name_create(self, name):
        _refuser_creation_a_la_volee(self.env)
        return super().name_create(name)


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def name_create(self, name):
        _refuser_creation_a_la_volee(self.env)
        return super().name_create(name)
