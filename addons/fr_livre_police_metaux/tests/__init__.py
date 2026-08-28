# -*- coding: utf-8 -*-

from . import test_referentiel

# `test_referentiel` s'exécute aussi sans Odoo — c'est écrit dans son en-tête,
# et c'est utile : il n'a rien à faire du serveur. Importer inconditionnellement
# ici un module qui, lui, dépend d'Odoo casserait cette exécution autonome, en
# faisant échouer le paquet avant même d'arriver au fichier visé.
#
# La condition est explicite plutôt qu'un `except ImportError` : une faute de
# frappe dans le module ci-dessous doit se voir, pas disparaître.
import importlib.util

if importlib.util.find_spec('odoo') is not None:
    from . import test_poids_apres_comptabilisation
    from . import test_registre_concerne
    from . import test_prix_inscrit
