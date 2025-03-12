import logging

_logger = logging.getLogger(__name__)

# Configuration centralisée
TAX_CONFIG = {
    'plus_value': {
        'impots_rate': 19.0,
        'prelevements_rate': 17.2,
        'sequence': 10,
    },
    'forfaitaire': {
        'tmp_rate': 11.0,
        'crds_rate': 0.5,
        'sequence': 5,
    },
    'tax_groups': {
        'impot': {
            'name': 'Impôt',
            'sequence': 1,
        },
        'prelevements_sociaux': {
            'name': 'Prélèvements sociaux',
            'sequence': 2,
        },
        'crds': {
            'name': 'CRDS',
            'sequence': 3,
        },
        'tmp': {
            'name': 'TMP',
            'sequence': 4,
        },
    }
}

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
            self.create_added_value_taxes()
            self.create_fixed_taxes()
            
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
                  amount_type='percent', children_tax_ids=None):
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
                'type_tax_use': 'sale' if amount_type != 'percent' else 'none',
                'description': description,
                'tax_group_id': tax_group_id,
                'price_include': False,
                'include_base_amount': False,
                'tax_scope': 'consu',
                'country_id': self.france_id,  # Ajout du country_id pour la France
            }
            
            if amount_type == 'group' and children_tax_ids:
                vals['children_tax_ids'] = [(6, 0, children_tax_ids)]
                
            return self.Tax.create(vals)
        return existing_tax
    
    def create_added_value_taxes(self):
        """
        Crée les taxes pour la plus-value sur l'or avec 21 niveaux
        d'ancienneté différents.
        """
        _logger.info("Création des taxes pour la plus-value")
        
        config = TAX_CONFIG['plus_value']
        
        # Pour chaque niveau d'ancienneté
        for i in range(1, 22):
            percentage = 100 - (i - 1) * 5  # 100, 95, 90, ..., 0
            
            # Détermination du label d'années
            if i == 1:
                years_label = "0-2 ANS"
            elif i == 21:
                years_label = "22+ ANS"
            else:
                years_label = f"{i}-{i+1} ANS"
            
            # Calcul des taux effectifs
            impots_rate = round(config['impots_rate'] * (percentage / 100.0), 2)
            prelevements_rate = round(config['prelevements_rate'] * (percentage / 100.0), 2)
            total_rate = round(impots_rate + prelevements_rate, 2)
            
            # Création des taxes avec les groupes spécifiques
            impot_tax = self.create_tax(
                f"Plus-value - Impôt ({years_label}, {total_rate}%)",
                -impots_rate,  # Négatif car c'est une déduction
                f"Impôt sur la plus-value de la revente d'or physique après {years_label} de détention. "
                f"Base: {config['impots_rate']}%, appliqué à {percentage}%.",
                self.tax_groups['impot'].id
            )
            
            prelevements_tax = self.create_tax(
                f"Plus-value - URSSAF ({years_label}, {total_rate}%)",
                -prelevements_rate,  # Négatif car c'est une déduction
                f"Prélèvements sociaux sur la plus-value de la revente d'or physique après {years_label} de détention. "
                f"Base: {config['prelevements_rate']}%, appliqué à {percentage}%.",
                self.tax_groups['prelevements_sociaux'].id
            )
            
            # Création de la taxe parent qui regroupe les deux sous-taxes
            # Pour la taxe parent, nous utilisons également un des groupes principaux
            # ou créons un groupe de taxe spécifique pour les taxes combinées si nécessaire
            parent_tax_name = f"Plus-value - {years_label} ({total_rate}%)"
            self.create_tax(
                parent_tax_name,
                0.0,  # Le montant est calculé à partir des sous-taxes
                f"Taxation complète sur la plus-value de la revente d'or physique "
                f"après {years_label} de détention. "
                f"Taux d'imposition total: {total_rate}% ({percentage}% de la base).",
                self.tax_groups['impot'].id,  # Utilisation du groupe 'Impôt' pour la taxe parent
                amount_type='group',
                children_tax_ids=[impot_tax.id, prelevements_tax.id]
            )
    
    def create_fixed_taxes(self):
        """Crée les taxes forfaitaires pour l'or."""
        _logger.info("Création des taxes forfaitaires")
        
        config = TAX_CONFIG['forfaitaire']
        
        # Création des taxes avec les groupes spécifiques
        tmp_tax = self.create_tax(
            "TMP (11%)",
            -config['tmp_rate'],  # Négatif car c'est une déduction
            f"Taxe sur les Métaux Précieux. Fixé à {config['tmp_rate']}%.",
            self.tax_groups['tmp'].id
        )
        
        crds_tax = self.create_tax(
            "CRDS (0.5%)",
            -config['crds_rate'],  # Négatif car c'est une déduction
            f"Contribution au Remboursement de la Dette Sociale. Fixé à {config['crds_rate']}%.",
            self.tax_groups['crds'].id
        )
        
        # Création de la taxe parent forfaitaire
        total_rate = config['tmp_rate'] + config['crds_rate']
        self.create_tax(
            f"Forfaitaire - {total_rate}%",
            0.0,  # Le montant est calculé à partir des sous-taxes
            f"Taxation forfaitaire complète sur la revente d'or physique. "
            f"Taux d'imposition total: {total_rate}%.",
            self.tax_groups['tmp'].id,  # Utilisation du groupe 'TMP' pour la taxe parent
            amount_type='group',
            children_tax_ids=[tmp_tax.id, crds_tax.id]
        )