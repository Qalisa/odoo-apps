from . import models
from .models.fr_gold_taxes import GoldTaxCreator

# Hooks pour l'initialisation
def create_gold_tax_groups(env):    
    """Hook pour l'initialisation des taxes lors de l'installation du module."""
    with env.cr.savepoint():
        creator = GoldTaxCreator(env)
        creator.create_all_tax_groups()
