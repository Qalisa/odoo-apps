from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

PARAMETRE = "product_creation_control.allow_inline_creation"
VUES = (
    "product_creation_control.view_order_form_no_inline_product",
    "product_creation_control.view_move_form_no_inline_product",
)


@tagged("post_install", "-at_install")
class TestCreationALaVolee(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # `self.env` est en super-utilisateur, qui reste volontairement autorisé.
        # Les tests raisonnent donc sur un utilisateur réel.
        cls.env_utilisateur = cls.env(user=cls.env.ref("base.user_admin"))

    def _vues(self):
        return self.env["ir.ui.view"].browse(
            [self.env.ref(xmlid).id for xmlid in VUES]
        )

    def _creer(self, nom, env):
        """Crée par `name_create`, en service.

        Le type importe : `fr_numismatics_metals`, s'il est installé à côté,
        exige de tout *bien* ses mentions de registre — ce qu'un article créé
        par son seul nom ne peut pas porter. Un service ne désigne aucun objet
        acheté, la fixture reste donc valable que ce module soit là ou non.
        """
        return env["product.template"].with_context(
            default_type='service').name_create(nom)

    def _regler(self, autorise):
        reglages = self.env["res.config.settings"].create({
            "product_allow_inline_creation": autorise,
        })
        reglages.execute()

    def test_bloque_des_installation(self):
        """Sans rien régler, la création à la volée est refusée."""
        self.assertFalse(
            self.env["ir.config_parameter"].sudo().get_param(PARAMETRE),
            "le paramètre ne doit pas exister tant que personne n'a coché la case",
        )
        for modele in ("product.template", "product.product"):
            with self.assertRaises(UserError):
                self.env_utilisateur[modele].name_create("Lingot d'essai")

    def test_vues_actives_des_installation(self):
        self.assertTrue(all(self._vues().mapped("active")))

    def test_option_cochee_retablit_le_standard(self):
        self._regler(True)
        self.assertFalse(
            any(self._vues().mapped("active")),
            "les vues qui suppriment « Créer … » doivent être désactivées",
        )
        article = self._creer("Lingot d'essai", self.env_utilisateur)
        self.assertTrue(article[0])

    def test_option_decochee_bloque_de_nouveau(self):
        self._regler(True)
        self._regler(False)
        self.assertTrue(all(self._vues().mapped("active")))
        with self.assertRaises(UserError):
            self.env_utilisateur["product.template"].name_create("Lingot d'essai")

    def test_super_utilisateur_toujours_autorise(self):
        """Installations de modules et scripts de reprise ne sont pas des saisies."""
        article = self._creer("Lingot de reprise", self.env)
        self.assertTrue(article[0])
