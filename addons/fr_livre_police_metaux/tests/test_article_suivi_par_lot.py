# -*- coding: utf-8 -*-
"""Un bien soumis au registre ne se crée pas sans suivi de stock par lot.

Un lingot de 1 g a été créé sans « Suivre l'inventaire » : son rachat s'est
inscrit au registre, mais la réception n'a créé ni lot ni quantité, et Odoo
refuse ensuite de changer le suivi d'un article déjà mouvementé.
"""

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged


@tagged('post_install', '-at_install')
class TestArticleSuiviParLot(TransactionCase):

    def test_bien_reglemente_sans_lot_refuse(self):
        or_jaune = self.env.ref('fr_numismatics_metals.metal_nature_or')
        with self.assertRaises(ValidationError):
            self.env(user=self.env.ref('base.user_admin'))['product.template'].create({
                'name': "Lingot d'essai 1 g",
                'type': 'consu', 'is_storable': True, 'tracking': 'none',
                'metal_regulated': True, 'metal_nature': or_jaune.id,
                'metal_fineness': 999.0, 'metal_quantity_mode': 'unit',
                'metal_unit_weight': 1.0,
            })
