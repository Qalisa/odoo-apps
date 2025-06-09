import logging

_logger = logging.getLogger(__name__)

# Configuration centralisée
TAX_CONFIG = {
    'tpv_rates': {
        'ir': 19.0, # Taux d'impôt sur le revenu
        'urssaf': 17.2, # Taux prélèvements sociaux divers
    },
    'tmp_rates': {
        'mp': 11.0, # Taux Metaux Précieux
        'op': 6.0, # Taux Objets Précieux 
        'crds': 0.5 # Taux CRDS
    },
    ##
    ## Note: tax groups ids are meaningless on "amount_type" == "group"
    ##
    'tax_groups': {
        ##
        ## 2091-SD
        ## https://entreprendre.service-public.fr/vosdroits/R17176
        ##
        'tmp': {
            'name': 'TMP', # affiché comme libellé sur les factures / avoirs 
            'sequence': 0,
            # 447100 - TMP / TFOP
            'tax_payable_account_id': "fr_gold_taxes.fr_gold_taxes_447100",
        },
        'tfop': {
            'name': 'TFOP', # affiché comme libellé sur les factures / avoirs 
            'sequence': 0,
            # 447100 - TMP / TFOP
            'tax_payable_account_id': "fr_gold_taxes.fr_gold_taxes_447100",
        },
        ##
        ## 2092-SD
        ## https://www.impots.gouv.fr/formulaire/2092-sd/declaration-doption-pour-le-regime-general-de-taxation-des-plus-values
        ##
        'tpv': {
            'name': 'TPV', # affiché comme libellé sur les factures / avoirs 
            'sequence': 0,
            # 442610 - TPV
            'tax_payable_account_id': "fr_gold_taxes.fr_gold_taxes_442610",
        }
    }
}

#
rate_type_config = {
    "tfop_tmp": {
        "price_include_override": "tax_included",
        "amount_type": "division"
    },
    "tpv": {
        "price_include_override": "tax_excluded",
        "amount_type": "percent"
    }
}



class GoldTaxCreator:
    """Classe utilitaire pour la création des taxes relatives à l'or."""
    
    def __init__(self, env):
        self.env = env
        self.Tax = env['account.tax']
        self.TaxGroup = env['account.tax.group']
        self.TaxRepartition = env['account.tax.repartition.line']
        self.tax_groups = {}  # Pour stocker les groupes de taxes créés
        
        # Récupération de la France depuis les pays
        self.france_id = self.env.ref('base.fr').id
    
    ##
    ##
    ##

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
                group_config['sequence'],
                group_config['tax_payable_account_id']
            )
    
    def get_or_create_tax_group(self, name, sequence, tax_payable_account_id):
        """Récupère ou crée un groupe de taxes."""
        tax_group = self.TaxGroup.search([('name', '=', name)], limit=1)
        if not tax_group:
            _logger.info(f"Création du groupe de taxes: {name}")
            tax_group = self.TaxGroup.create({
                'name': name, 
                'sequence': sequence,
                'country_id': self.france_id,
                'tax_payable_account_id': self.env.ref(tax_payable_account_id).id,
            })
        return tax_group
    
    def create_tax(self, tax_type, 
                   name, amount, description,
                   tax_group_id,
                   account_xid=None,
                  children_tax_ids=None):
        """Crée une taxe si elle n'existe pas déjà."""
        existing_tax = self.Tax.search([
            ('name', '=', name),
            ('tax_group_id', '=', tax_group_id)
        ], limit=1)
        
        is_group = children_tax_ids is not None

        if not existing_tax:
            _logger.info(f"Création de la taxe: {name}")
            vals = {
                #
                'name': name,
                'description': description,
                'country_id': self.france_id, # nécessaire
                'tax_group_id': tax_group_id, # required
                #
                'amount_type': "group" if is_group else rate_type_config[tax_type]['amount_type'],
                'amount': 0 if is_group else amount, # amount is meaningless if group of taxes
                #
                'tax_scope': 'consu',
                'type_tax_use': 'sale' if is_group else 'none',
                #
                'price_include': False,
                'include_base_amount': False,
            }
            
            if is_group:
                vals['children_tax_ids'] = [(6, 0, children_tax_ids)]
            else:
                vals['price_include_override'] = rate_type_config[tax_type]['price_include_override']

            #
            created_tax = self.Tax.create(vals)

            #
            if not is_group:
                # only apply on refunds, since tax is only collected there
                tax_lines = created_tax.refund_repartition_line_ids.filtered(lambda l: l.repartition_type == 'tax')   
                for line in tax_lines:
                    line.write({
                        'account_id': self.env.ref(account_xid).id,
                    })

            #
            return created_tax


        return existing_tax
    
    ##
    ##
    ##

    def create_added_value_taxes(self):
        """
        Crée les taxes pour les plus-values mobilières, pour chaque palier d'abattement
        """
        _logger.info("Création des taxes sur les plus-values")
        
        config = TAX_CONFIG['tpv_rates']
        
        # Pour chaque palier d'abattement
        for i in range(1, 22):
            percentage_discount = (i - 1) * 5
            percentage_paid = 100 - percentage_discount  # 100, 95, 90, ..., 0

            # Détermination du label d'années
            if i == 1:
                years_label = "0 à 2+ ANS"
            else:
                years_label = f"{i+1}+ ANS"
            
            # Calcul des taux effectifs
            ir_rate = round(config['ir'] * (percentage_paid / 100.0), 2)
            urssaf_rate = round(config['urssaf'] * (percentage_paid / 100.0), 2)
            total_rate = round(ir_rate + urssaf_rate, 2)
            
            # Création des taxes avec les groupes spécifiques
            ir_tax = self.create_tax(
                'tpv',
                f"TPV - IR ({years_label}, {ir_rate}%)", # affiché sur la facture par default
                -ir_rate,  # Négatif car c'est une déduction
                f"Impôt sur le revenu associé à la TPV après {years_label} de détention. "
                f"Base: {config['ir']}% - appliqué à {percentage_paid}% | {percentage_discount}% d'abattment > {ir_rate}%",
                self.tax_groups['tpv'].id,
                 "fr_gold_taxes.fr_gold_taxes_442611"
            )
            
            urssaf_tax = self.create_tax(
                'tpv',
                f"TPV - URSSAF ({years_label}, {urssaf_rate}%)", # affiché sur la facture par default
                -urssaf_rate,  # Négatif car c'est une déduction
                f"Prélèvements sociaux associé à la TPV après {years_label} de détention. "
                f"Base: {config['urssaf']}% - appliqué à {percentage_paid}% | {percentage_discount}% d'abattment > {urssaf_rate}%",
                self.tax_groups['tpv'].id,
                "fr_gold_taxes.fr_gold_taxes_442612"
            )
            
            # Création de la taxe parent qui regroupe les deux sous-taxes
            # Pour la taxe parent, nous utilisons également un des groupes principaux
            # ou créons un groupe de taxe spécifique pour les taxes combinées si nécessaire
            parent_tax_name = f"TPV ({years_label})"
            self.create_tax(
                'tpv',
                parent_tax_name,
                0.0,  # nulle, Le montant est calculé à partir des sous-taxes
                f"Taxe sur la plus-value après {years_label} de détention d'un bien. "
                f"Base: {config['urssaf'] + config['ir']}% - appliqué à {percentage_paid}% | {percentage_discount}% d'abattment > {total_rate}%",
                self.tax_groups['tpv'].id,
                # includes
                children_tax_ids=[ir_tax.id, urssaf_tax.id]
            )
    
    def create_fixed_taxes(self):
        """Crée les taux de TMP"""
        _logger.info("Création des taxes forfaitaires pour les objets précieux")

        #
        crdsRate = TAX_CONFIG['tmp_rates']['crds']

        ##
        ## Taxes "Métaux Précieux"
        ##

        # Taxe TMP seule
        curr_tax_rate = TAX_CONFIG['tmp_rates']['mp']
        tfmp_tax = self.create_tax(
            'tfop_tmp',
            f"TMP - Métaux Précieux ({curr_tax_rate}%)",
            -curr_tax_rate,  # Négatif car c'est une déduction
            "Taxe Forfaitaire sur les Métaux Précieux (monnaie > 1800JC, or, argent, platine)",
            self.tax_groups['tmp'].id,
            "fr_gold_taxes.fr_gold_taxes_447111"
        )

        # CRDS sur TMP
        crds_tax = self.create_tax(
            'tfop_tmp',
            f"TMP - CRDS ({crdsRate}%)",
            -crdsRate,  # Négatif car c'est une déduction
            "Contribution au Remboursement de la Dette Sociale sur la TMP.",
            self.tax_groups['tmp'].id,
            "fr_gold_taxes.fr_gold_taxes_447112"
        )
        
        total_rate = curr_tax_rate + crdsRate

        # TMP complète
        self.create_tax(
            'tfop_tmp',
            f"{total_rate}% TMP",
            0.0,  # nulle, Le montant est calculé à partir des sous-taxes
            f"Regroupe les taxes à appliquer lors de la revente de métaux précieux.",
            self.tax_groups['tmp'].id,
            # includes
            children_tax_ids=[tfmp_tax.id, crds_tax.id]
        )

        ##
        ## Taxes "Objets Précieux" (Fourre-tout, autre que Métaux Précieux) (https://www.economie.gouv.fr/particuliers/vente-objet-precieux-fiscalite-taxe)
        ##

        # Taxe TFOP seule
        curr_tax_rate = TAX_CONFIG['tmp_rates']['op']
        tmp_tax = self.create_tax(
            'tfop_tmp',
            f"TFOP - Objets Précieux ({curr_tax_rate}%)",
            -curr_tax_rate,  # Négatif car c'est une déduction
            f"Taxe sur les bijoux, objets d'art, de collection et d'antiquité, si montant supérieur à 5000€.",
            self.tax_groups['tfop'].id,
            "fr_gold_taxes.fr_gold_taxes_447121"
        )

        # CRDS sur TFOP
        crds_tax = self.create_tax(
            'tfop_tmp',
            f"TFOP - CRDS ({crdsRate}%)",
            -crdsRate,  # Négatif car c'est une déduction
            "Contribution au Remboursement de la Dette Sociale sur la TMP.",
            self.tax_groups['tfop'].id,
            "fr_gold_taxes.fr_gold_taxes_447122"
        )
        
        total_rate = curr_tax_rate + crdsRate

        # TFOP complète
        self.create_tax(
            'tfop_tmp',
            f"{total_rate}% TFOP",
            0.0,  # nulle, Le montant est calculé à partir des sous-taxes
            f"Regroupe les taxes à appliquer lors de la revente d'objets précieux si montant supérieur à 5000€.",
            self.tax_groups['tfop'].id,
            # includes
            children_tax_ids=[tmp_tax.id, crds_tax.id]
        )