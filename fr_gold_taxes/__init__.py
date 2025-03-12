from . import models
from .models.fr_gold_taxes import GoldTaxCreator

# Hooks pour l'initialisation
def create_gold_tax_groups(env):    
    # Utilisation de savepoint pour assurer l'atomicité
    with env.cr.savepoint():
        creator = GoldTaxCreator(env)
        creator.create_all_tax_groups()