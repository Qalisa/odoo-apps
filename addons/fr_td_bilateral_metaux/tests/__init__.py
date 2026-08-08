import importlib.util as _ilu

from . import test_dmet_tools
from . import test_precheck

# Le test d'intégration dépend d'Odoo (TransactionCase) : importé seulement
# lorsque Odoo est présent, pour préserver l'exécution standalone des autres.
if _ilu.find_spec('odoo') is not None:
    from . import test_integration
    from . import test_id_document_gate
    from . import test_birth_mapping
