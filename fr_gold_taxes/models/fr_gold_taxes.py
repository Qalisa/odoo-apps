import logging

_logger = logging.getLogger(__name__)

# Configuration centralisée
TAX_CONFIG = {
    'plus_value': {
        'impots_rate': -19.0,
        'prelevements_rate': -17.2,
        'parent_group_name': 'Métaux Précieux - Plus-value',
        'parent_sequence': 10,
    },
    'forfaitaire': {
        'tmp_rate': -11.0,
        'crds_rate': -0.5,
        'group_name': 'Métaux Précieux - Forfaitaire - 11,5%',
        'sequence': 5,
    }
}

class GoldTaxCreator:
    """Classe utilitaire pour la création des taxes relatives à l'or."""
    
    def __init__(self, env):
        self.env = env
        self.Tax = env['account.tax']
        self.TaxGroup = env['account.tax.group']
    
    def create_all_tax_groups(self):
        """Crée tous les groupes de taxes pour l'or."""
        try:
            _logger.info("Début de la création des groupes de taxes pour l'or")
            self.create_added_value_tax_groups()
            self.create_fixed_tax_group()
            _logger.info("Fin de la création des groupes de taxes pour l'or")
            return True
        except Exception as e:
            _logger.error(f"Erreur lors de la création des groupes de taxes: {e}")
            return False
    
    def get_or_create_tax_group(self, name, sequence, parent_id=False):
        """Récupère ou crée un groupe de taxes."""
        tax_group = self.TaxGroup.search([('name', '=', name)], limit=1)
        if not tax_group:
            _logger.info(f"Création du groupe de taxes: {name}")
            values = {'name': name, 'sequence': sequence}
            if parent_id:
                values['parent_id'] = parent_id
            tax_group = self.TaxGroup.create(values)
        return tax_group
    
    def create_tax(self, name, amount, description, tax_group_id, type_tax_use='sale'):
        """Crée une taxe si elle n'existe pas déjà."""
        existing_tax = self.Tax.search([
            ('name', '=', name),
            ('tax_group_id', '=', tax_group_id)
        ], limit=1)
        
        if not existing_tax:
            _logger.info(f"Création de la taxe: {name}")
            self.Tax.create({
                'name': name,
                'amount': amount,
                'amount_type': 'percent',
                'type_tax_use': type_tax_use,
                'description': description,
                'tax_group_id': tax_group_id,
            })
    
    def create_added_value_tax_groups(self):
        """
        Crée 21 groupes de taxes pour la plus-value sur l'or.
        Chaque groupe contient 2 taxes : Impôts (19%) et Prélèvements Sociaux (17.2%).
        """
        _logger.info("Création des groupes de taxes pour la plus-value")
        
        config = TAX_CONFIG['plus_value']
        
        # Création du groupe parent
        parent_group = self.get_or_create_tax_group(
            config['parent_group_name'], 
            config['parent_sequence']
        )
        
        # Création des 21 groupes de taxes
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
            total_rate = round(abs(impots_rate) + abs(prelevements_rate), 2)
            
            # Nom du groupe
            group_name = f"{config['parent_group_name']} - {years_label} / {percentage}% / {total_rate}%"
            
            # Création ou récupération du groupe
            tax_group = self.get_or_create_tax_group(
                group_name, 
                config['parent_sequence'] + i,
                parent_group.id
            )
            
            # Création des taxes
            self.create_tax(
                f"Impôts ({percentage}%)",
                impots_rate,
                f"Partie impôt du régime de la plus-value sur la revente d'or physique, "
                f"correspondant à {years_label} de détention. "
                f"Base: {abs(config['impots_rate'])}%, appliqué à {percentage}%.",
                tax_group.id
            )
            
            self.create_tax(
                f"Prélèvements Sociaux ({percentage}%)",
                prelevements_rate,
                f"Partie prélèvements sociaux du régime de la plus-value sur la revente d'or physique, "
                f"correspondant à {years_label} de détention. "
                f"Base: {abs(config['prelevements_rate'])}%, appliqué à {percentage}%.",
                tax_group.id
            )
    
    def create_fixed_tax_group(self):
        """Crée le groupe de taxe forfaitaire pour l'or."""
        _logger.info("Création du groupe de taxe forfaitaire")
        
        config = TAX_CONFIG['forfaitaire']
        
        # Création du groupe
        tax_group = self.get_or_create_tax_group(
            config['group_name'],
            config['sequence']
        )
        
        # Création des taxes
        self.create_tax(
            "TMP (11%)",
            config['tmp_rate'],
            f"Partie de la taxe forfaitaire sur la revente d'or physique liée à la "
            f"Taxe sur les Métaux Précieux. Fixé à {abs(config['tmp_rate'])}%.",
            tax_group.id
        )
        
        self.create_tax(
            "CRDS (0.5%)",
            config['crds_rate'],
            f"Partie de la taxe forfaitaire sur la revente d'or physique liée à la "
            f"Contribution au Remboursement de la Dette Sociale. Fixé à {abs(config['crds_rate'])}%.",
            tax_group.id
        )
