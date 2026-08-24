# Le sous-paquet `tools` est volontairement sans dépendance à Odoo : il porte
# la lecture des libellés de ligne et la comparaison des valeurs de référence,
# afin de rester testable en isolation.
#
# Les modèles ne sont chargés que lorsque Odoo est présent, pour que les tests
# du sous-paquet `tools` restent exécutables hors Odoo.
import importlib.util as _ilu

from . import tools

if _ilu.find_spec('odoo') is not None:
    from . import models
