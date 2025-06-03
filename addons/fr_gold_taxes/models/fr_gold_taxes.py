import logging

_logger = logging.getLogger(__name__)

# Configuration centralisée
TAX_CONFIG = {
    'tpv_rates': {
        'ir': 19.0,
        'urssaf': 17.2,
    },
    'tfop_rates': {
        'mp': 11.0, # Taux Metaux Précieux
        'op': 6.0, # Taux Objets Précieux 
        'crds': 0.5 # Taux CRDS
    },
    ##
    ##
    ##
    'tax_groups': {
        ##
        ## 2091-SD
        ## https://entreprendre.service-public.fr/vosdroits/R17176
        ##
        'tfop': {
            'name': 'Taxes Forfaitaires sur les Objets Précieux (TFOP)',
            'sequence': 0,
            # 447100 - TFOP due à l'administration
        },
        'tfop_tax': {
            'name': 'Taxes (TFOP)',
            'sequence': 0,
            # 447110 - TFOP Seule due à l'administration
        },
        'tfop_crds': {
            'name': 'CRDS (TFOP)',
            'sequence': 0,
            # 447120 - CRDS sur TFOP due à l'administration
        },
        ##
        ## 2092-SD
        ## https://www.impots.gouv.fr/formulaire/2092-sd/declaration-doption-pour-le-regime-general-de-taxation-des-plus-values
        ##
        'tpv': {
            'name': 'Taxation sur les Plus Values réelles (TPV)',
            'sequence': 0,
            # 442600 - Taxe sur les plus-values mobilières due à l'administration
        },        
        'tpv_ir': {
            'name': 'IR (TPV)',
            'sequence': 0,
            # 442600 – Impôt sur le revenu collecté
        },
        'tpv_urssaf': {
            'name': 'URSSAF (TPV)',
            'sequence': 0,
            # 442400 – Prélèvements sociaux sur revenus du capital
        },
    }
}

# 'percent' n'applique pas la règle de la façon désirée
default_tax_rate_type = "division" # 'percent'

class GoldTaxCreator:
    """Classe utilitaire pour la création des taxes relatives à l'or."""
    
    def __init__(self, env):
        self.env = env
        self.Tax = env['account.tax']
        self.TaxGroup = env['account.tax.group']
        self.tax_groups = {}  # Pour stocker les groupes de taxes créés
        
        # Récupération de la France depuis les pays
        self.france_id = self.env.ref('base.fr').id
    
    def create_all_tax_groups(self):
        """Crée tous les groupes de taxes pour l'or."""
        try:
            _logger.info("Début de la création des groupes de taxes pour l'or")
            
            # Création des groupes de taxes principaux
            self._create_main_tax_groups()
            
            # Création des taxes
            self.create_fixed_taxes()
            self.create_added_value_taxes()
            
            _logger.info("Fin de la création des groupes de taxes pour l'or")
            return True
        except Exception as e:
            _logger.error(f"Erreur lors de la création des groupes de taxes: {e}")
            raise e  # Rethrow pour voir l'erreur complète
    
    def _create_main_tax_groups(self):
        """Crée les groupes de taxes principaux."""
        for key, group_config in TAX_CONFIG['tax_groups'].items():
            self.tax_groups[key] = self.get_or_create_tax_group(
                group_config['name'],
                group_config['sequence']
            )
    
    def get_or_create_tax_group(self, name, sequence):
        """Récupère ou crée un groupe de taxes."""
        tax_group = self.TaxGroup.search([('name', '=', name)], limit=1)
        if not tax_group:
            _logger.info(f"Création du groupe de taxes: {name}")
            tax_group = self.TaxGroup.create({
                'name': name, 
                'sequence': sequence,
                'country_id': self.france_id,
            })
        return tax_group
    
    def create_tax(self, name, amount, description, tax_group_id, 
                  amount_type=default_tax_rate_type, children_tax_ids=None):
        """Crée une taxe si elle n'existe pas déjà."""
        existing_tax = self.Tax.search([
            ('name', '=', name),
            ('tax_group_id', '=', tax_group_id)
        ], limit=1)
        
        if not existing_tax:
            _logger.info(f"Création de la taxe: {name}")
            vals = {
                'name': name,
                'amount': amount,
                'amount_type': amount_type,
                'type_tax_use': 'sale' if amount_type != default_tax_rate_type else 'none',
                'description': description,
                'tax_group_id': tax_group_id,
                'price_include': False,
                'include_base_amount': False,
                'tax_scope': 'consu',
                'country_id': self.france_id,  # Ajout du country_id pour la France
            }
            
            if amount_type == 'group' and children_tax_ids:
                vals['children_tax_ids'] = [(6, 0, children_tax_ids)]
                
            # if amount_type != 'group':
            #     vals['price_include_override'] = 'tax_included'

            return self.Tax.create(vals)
        return existing_tax
    
    def create_added_value_taxes(self):
        """
        Crée les taxes pour les plus-values mobilières, pour chaque palier d'abattement
        """
        _logger.info("Création des taxes sur les plus-values")
        
        config = TAX_CONFIG['tpv_rates']
        
        # Pour chaque palier d'abattement
        for i in range(1, 22):
            percentage = 100 - (i - 1) * 5  # 100, 95, 90, ..., 0
            
            # Détermination du label d'années
            if i == 1:
                years_label = "0 à 2+ ANS"
            else:
                years_label = f"{i+1}+ ANS"
            
            # Calcul des taux effectifs
            ir_rate = round(config['ir'] * (percentage / 100.0), 2)
            urssaf_rate = round(config['urssaf'] * (percentage / 100.0), 2)
            total_rate = round(ir_rate + urssaf_rate, 2)
            
            # Création des taxes avec les groupes spécifiques
            ir_tax = self.create_tax(
                f"TPV - IR ({years_label}, {ir_rate}%)",
                -ir_rate,  # Négatif car c'est une déduction
                f"Impôt sur le revenu associé à la TPV après {years_label} de détention. "
                f"Base: {config['ir']}%, appliqué à {percentage}%.",
                self.tax_groups['tpv_ir'].id
            )
            
            urssaf_tax = self.create_tax(
                f"TPV - URSSAF ({years_label}, {urssaf_rate}%)",
                -urssaf_rate,  # Négatif car c'est une déduction
                f"Prélèvements sociaux associé à la TPV après {years_label} de détention. "
                f"Base: {config['urssaf']}%, appliqué à {percentage}%.",
                self.tax_groups['tpv_urssaf'].id
            )
            
            # Création de la taxe parent qui regroupe les deux sous-taxes
            # Pour la taxe parent, nous utilisons également un des groupes principaux
            # ou créons un groupe de taxe spécifique pour les taxes combinées si nécessaire
            parent_tax_name = f"TPV ({years_label})"
            self.create_tax(
                parent_tax_name,
                0.0,  # nulle, Le montant est calculé à partir des sous-taxes
                f"Taxe sur la plus-value après {years_label} de détention d'un bien. "
                f"Taux d'imposition total: {total_rate}% ({percentage}% de la base).",
                self.tax_groups['tpv'].id,
                amount_type='group',
                children_tax_ids=[ir_tax.id, urssaf_tax.id]
            )
    
    def create_fixed_taxes(self):
        """Crée les taux de TFOP"""
        _logger.info("Création des taxes forfaitaires pour les objets précieux")
        
        ##
        ## CRDS (commune aux 2 autres)
        ##

        #
        crdsRate = TAX_CONFIG['tfop_rates']['crds']
        crds_tax = self.create_tax(
            f"TFOP - CRDS ({crdsRate}%)",
            -crdsRate,  # Négatif car c'est une déduction
            "Contribution au Remboursement de la Dette Sociale sur la TFOP.",
            self.tax_groups['tfop_crds'].id
        )

        ##
        ## Taxes "Métaux Précieux"
        ##

        # Sous-taxe
        curr_tax_rate = TAX_CONFIG['tfop_rates']['mp']
        tfmp_tax = self.create_tax(
            f"TFOP - Métaux Précieux ({curr_tax_rate}%)",
            -curr_tax_rate,  # Négatif car c'est une déduction
            "Taxe Forfaitaire sur les Métaux Précieux (monnaie > 1800JC, or, argent, platine)",
            self.tax_groups['tfop_tax'].id
        )
        
        total_rate = curr_tax_rate + crdsRate

        # Groupement, incluant CRDS
        self.create_tax(
            f"{total_rate}% TMP",
            0.0,  # nulle, Le montant est calculé à partir des sous-taxes
            f"Regroupe les taxes à appliquer lors de la revente de métaux précieux.",
            self.tax_groups['tfop'].id,
            amount_type='group',
            children_tax_ids=[tfmp_tax.id, crds_tax.id]
        )

        ##
        ## Taxes "Objets Précieux" (Fourre-tout, autre que Métaux Précieux) (https://www.economie.gouv.fr/particuliers/vente-objet-precieux-fiscalite-taxe)
        ##

        # Sous-taxe
        curr_tax_rate = TAX_CONFIG['tfop_rates']['op']
        tfop_tax = self.create_tax(
            f"TFOP - Objets Précieux ({curr_tax_rate}%)",
            -curr_tax_rate,  # Négatif car c'est une déduction
            f"Taxe sur les bijoux, objets d'art, de collection et d'antiquité, si montant supérieur à 5000€.",
            self.tax_groups['tfop_tax'].id
        )
        
        total_rate = curr_tax_rate + crdsRate

        # Groupement, incluant CRDS
        self.create_tax(
            f"{total_rate}% TFOP",
            0.0,  # nulle, Le montant est calculé à partir des sous-taxes
            f"Regroupe les taxes à appliquer lors de la revente d'objets précieux si montant supérieur à 5000€.",
            self.tax_groups['tfop'].id,
            amount_type='group',
            children_tax_ids=[tfop_tax.id, crds_tax.id]
        )