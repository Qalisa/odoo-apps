# Le sous-paquet `tools` est volontairement sans dépendance à Odoo :
# il porte toute la logique réglementaire (fixed-width 550, translittération,
# nommage, compression, pré-contrôle) afin de rester testable en isolation.
#
# Les modèles ne sont chargés que lorsque Odoo est présent, pour que les tests
# du sous-paquet `tools` restent exécutables hors Odoo (import du paquet parent).
import importlib.util as _ilu

if _ilu.find_spec('odoo') is not None:
    from . import models
