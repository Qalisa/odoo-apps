#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Générateur de fichiers CSV pour les taxes sur l'or dans Odoo.

Ce module génère les fichiers CSV nécessaires pour créer les taxes françaises
sur les métaux précieux, objets précieux et plus-values mobilières.
"""

import csv
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union

self_mod= "fr_numismatics_taxes"

@dataclass
class TaxRates:
    """Configuration des taux de taxes."""
    tpv_ir: float = 19.0
    tpv_urssaf: float = 17.2
    tmp_metaux_precieux: float = 11.0
    tmp_objets_precieux: float = 6.0
    crds: float = 0.5


@dataclass
class TaxGroupConfig:
    """Configuration d'un groupe de taxes."""
    name: str
    sequence: int
    # tax_payable_account_id: str


@dataclass
class TaxConfig:
    """Configuration d'une taxe."""
    id: str
    name: str
    description: str
    amount_type: str
    amount: float
    tax_group_id: str
    type_tax_use: str = 'none'
    tax_scope: str = 'consu'
    price_include: bool = False
    include_base_amount: bool = False
    price_include_override: Optional[str] = None
    children_tax_ids: Optional[List[str]] = None
    account_id: Optional[str] = None


@dataclass
class TaxRepartitionConfig:
    """Configuration d'une ligne de répartition de taxe."""
    id: str
    tax_id: str
    repartition_type: str
    account_id: str
    factor_percent: float = 100.0


class TaxCalculator:
    """Calculateur pour les taux de taxes avec abattements."""
    
    @staticmethod
    def calculate_tpv_rates(base_rate: float, years: int) -> float:
        """Calcule le taux effectif avec abattement selon l'ancienneté."""
        percentage_discount = max(0, min(100, (years - 1) * 5))
        percentage_paid = 100 - percentage_discount
        return round(base_rate * (percentage_paid / 100.0), 2)
    
    @staticmethod
    def format_years_label(years: int) -> str:
        """Formate le libellé des années pour les taxes TPV."""
        return "0 à 2+ ANS" if years == 1 else f"{years+1}+ ANS"


class CSVWriter:
    """Gestionnaire d'écriture des fichiers CSV."""
    
    def __init__(self, output_dir: Union[str, Path]):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def write_csv(self, filename: str, data: List[Dict], fieldnames: List[str]) -> None:
        """Écrit un fichier CSV avec les données fournies."""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            
            for row_data in data:
                row = {field: row_data.get(field, '') for field in fieldnames}
                writer.writerow(row)
        
        print(f"📄 {filename}: {len(data)} enregistrements")


class BaseTaxGenerator(ABC):
    """Classe de base pour les générateurs de taxes."""
    
    def __init__(self, rates: TaxRates):
        self.rates = rates
        self.taxes: List[TaxConfig] = []
        self.repartition_lines: List[TaxRepartitionConfig] = []
    
    @abstractmethod
    def generate(self) -> None:
        """Génère les taxes et lignes de répartition."""
        pass
    
    def _add_tax(self, tax_config: TaxConfig) -> None:
        """Ajoute une taxe à la liste."""
        self.taxes.append(tax_config)
        
        # Ajoute automatiquement une ligne de répartition si un compte est spécifié
        if tax_config.account_id and tax_config.type_tax_use == 'none':
            self._add_repartition_line(tax_config.id, 'tax', tax_config.account_id)
    
    def _add_repartition_line(self, tax_id: str, repartition_type: str, account_id: str) -> None:
        """Ajoute une ligne de répartition."""
        repartition = TaxRepartitionConfig(
            id=f"{tax_id}_repartition_line",
            tax_id=tax_id,
            repartition_type=repartition_type,
            account_id=account_id
        )
        self.repartition_lines.append(repartition)


class TPVTaxGenerator(BaseTaxGenerator):
    """Générateur de taxes sur les plus-values (TPV)."""
    
    def generate(self) -> None:
        """Génère les taxes TPV pour tous les paliers d'abattement."""
        for years in range(1, 22):
            self._generate_tpv_for_years(years)
    
    def _generate_tpv_for_years(self, years: int) -> None:
        """Génère les taxes TPV pour une année donnée."""
        years_label = TaxCalculator.format_years_label(years)
        ir_rate = TaxCalculator.calculate_tpv_rates(self.rates.tpv_ir, years)
        urssaf_rate = TaxCalculator.calculate_tpv_rates(self.rates.tpv_urssaf, years)
        
        # Taxe IR
        ir_tax_id = f"tpv_ir_{years:02d}"
        ir_tax = TaxConfig(
            id=ir_tax_id,
            name=f"TPV - IR ({years_label}, {ir_rate}%)",
            description=self._build_tpv_description("Impôt sur le revenu", years_label, 
                                                   self.rates.tpv_ir, years, ir_rate),
            amount_type='percent',
            amount=-ir_rate,
            tax_group_id=f'{self_mod}.tax_group_tpv',
            price_include_override='tax_excluded',
            account_id=f'{self_mod}.numim_442611'
        )
        self._add_tax(ir_tax)
        
        # Taxe URSSAF
        urssaf_tax_id = f"tpv_urssaf_{years:02d}"
        urssaf_tax = TaxConfig(
            id=urssaf_tax_id,
            name=f"TPV - URSSAF ({years_label}, {urssaf_rate}%)",
            description=self._build_tpv_description("Prélèvements sociaux", years_label,
                                                   self.rates.tpv_urssaf, years, urssaf_rate),
            amount_type='percent',
            amount=-urssaf_rate,
            tax_group_id=f'{self_mod}.tax_group_tpv',
            price_include_override='tax_excluded',
            account_id=f'{self_mod}.numim_442612'
        )
        self._add_tax(urssaf_tax)
        
        # Taxe parent (groupe)
        total_rate = round(ir_rate + urssaf_rate, 2)
        parent_tax = TaxConfig(
            id=f"tpv_group_{years:02d}",
            name=f"TPV ({years_label})",
            description=self._build_tpv_group_description(years_label, years, total_rate),
            amount_type='group',
            amount=0.0,
            tax_group_id=f'{self_mod}.tax_group_tpv',
            type_tax_use='sale',
            children_tax_ids=[f"{self_mod}.{ir_tax_id}", f"{self_mod}.{urssaf_tax_id}"]
        )
        self._add_tax(parent_tax)
    
    def _build_tpv_description(self, tax_type: str, years_label: str, 
                              base_rate: float, years: int, effective_rate: float) -> str:
        """Construit la description d'une taxe TPV."""
        percentage_discount = (years - 1) * 5
        percentage_paid = 100 - percentage_discount
        
        return (f"{tax_type} associé à la TPV après {years_label} de détention. "
                f"Base: {base_rate}% - appliqué à {percentage_paid}% | "
                f"{percentage_discount}% d'abattement > {effective_rate}%")
    
    def _build_tpv_group_description(self, years_label: str, years: int, total_rate: float) -> str:
        """Construit la description d'un groupe de taxes TPV."""
        percentage_discount = (years - 1) * 5
        percentage_paid = 100 - percentage_discount
        base_total = self.rates.tpv_ir + self.rates.tpv_urssaf
        
        return (f"Taxe sur la plus-value après {years_label} de détention d'un bien. "
                f"Base: {base_total}% - appliqué à {percentage_paid}% | "
                f"{percentage_discount}% d'abattement > {total_rate}%")


class FixedTaxGenerator(BaseTaxGenerator):
    """Générateur de taxes forfaitaires (TMP/TFOP)."""
    
    def generate(self) -> None:
        """Génère les taxes forfaitaires TMP et TFOP."""
        self._generate_tmp_taxes()
        self._generate_tfop_taxes()
    
    def _generate_tmp_taxes(self) -> None:
        """Génère les taxes TMP (Métaux Précieux)."""
        tax_configs = [
            {
                'id': 'tmp_metaux_precieux',
                'name': f"TMP - Métaux Précieux ({self.rates.tmp_metaux_precieux}%)",
                'description': "Taxe Forfaitaire sur les Métaux Précieux (monnaie > 1800JC, or, argent, platine)",
                'amount': -self.rates.tmp_metaux_precieux,
                'account_id': f'{self_mod}.numim_447111'
            },
            {
                'id': 'tmp_crds',
                'name': f"TMP - CRDS ({self.rates.crds}%)",
                'description': "Contribution au Remboursement de la Dette Sociale sur la TMP.",
                'amount': -self.rates.crds,
                'account_id': f'{self_mod}.numim_447112'
            }
        ]
        
        child_ids = []
        for config in tax_configs:
            tax = TaxConfig(
                id=config['id'],
                name=config['name'],
                description=config['description'],
                amount_type='division',
                amount=config['amount'],
                tax_group_id='tax_group_tmp',
                price_include_override='tax_included',
                account_id=config['account_id']
            )
            self._add_tax(tax)
            child_ids.append(config['id'])
        
        # Taxe groupe TMP
        total_rate = self.rates.tmp_metaux_precieux + self.rates.crds
        group_tax = TaxConfig(
            id='tmp_complete',
            name=f"{total_rate}% TMP",
            description="Regroupe les taxes à appliquer lors de la revente de métaux précieux.",
            amount_type='group',
            amount=0.0,
            tax_group_id='tax_group_tmp',
            type_tax_use='sale',
            children_tax_ids=child_ids
        )
        self._add_tax(group_tax)
    
    def _generate_tfop_taxes(self) -> None:
        """Génère les taxes TFOP (Objets Précieux)."""
        tax_configs = [
            {
                'id': 'tfop_objets_precieux',
                'name': f"TFOP - Objets Précieux ({self.rates.tmp_objets_precieux}%)",
                'description': "Taxe sur les bijoux, objets d'art, de collection et d'antiquité, si montant supérieur à 5000€.",
                'amount': -self.rates.tmp_objets_precieux,
                'account_id': f'{self_mod}.numim_447121'
            },
            {
                'id': 'tfop_crds',
                'name': f"TFOP - CRDS ({self.rates.crds}%)",
                'description': "Contribution au Remboursement de la Dette Sociale sur la TMP.",
                'amount': -self.rates.crds,
                'account_id': f'{self_mod}.numim_447122'
            }
        ]
        
        child_ids = []
        for config in tax_configs:
            tax = TaxConfig(
                id=config['id'],
                name=config['name'],
                description=config['description'],
                amount_type='division',
                amount=config['amount'],
                tax_group_id='tax_group_tfop',
                price_include_override='tax_included',
                account_id=config['account_id']
            )
            self._add_tax(tax)
            child_ids.append(f"{self_mod}.{config['id']}")
        
        # Taxe groupe TFOP
        total_rate = self.rates.tmp_objets_precieux + self.rates.crds
        group_tax = TaxConfig(
            id='tfop_complete',
            name=f"{total_rate}% TFOP",
            description="Regroupe les taxes à appliquer lors de la revente d'objets précieux si montant supérieur à 5000€.",
            amount_type='group',
            amount=0.0,
            tax_group_id='tax_group_tfop',
            type_tax_use='sale',
            children_tax_ids=child_ids
        )
        self._add_tax(group_tax)


class OdooTaxCSVGenerator:
    """Générateur principal des fichiers CSV pour les taxes Odoo."""
    
    # Configuration des groupes de taxes
    TAX_GROUPS = {
        'tmp': TaxGroupConfig('TMP', 0), # f'{self_mod}.numim_447100'),
        'tfop': TaxGroupConfig('TFOP', 0), # f'{self_mod}.numim_447100'),
        'tpv': TaxGroupConfig('TPV', 0), #f'{self_mod}.numim_442610')
    }
    
    # Définition des champs CSV
    TAX_GROUP_FIELDS = ['id', 'name', 'sequence', 'country_id:id', #'tax_payable_account_id:id'
                        ]
    TAX_FIELDS = [
        'id', 'name', 'description', 'amount_type', 'amount', 'country_id:id',
        'tax_group_id:id', 'tax_scope', 'type_tax_use', 'price_include',
        'price_include_override', 'include_base_amount', 'children_tax_ids:id'
    ]
    REPARTITION_FIELDS = [
        'id', 'tax_id:id', 'document_type', 'repartition_type',
        'account_id:id', 'factor_percent'
    ]
    
    def __init__(self, output_dir: str = "../data_gen", rates: Optional[TaxRates] = None):
        self.rates = rates or TaxRates()
        self.csv_writer = CSVWriter(output_dir)
        self.generators = [
            TPVTaxGenerator(self.rates),
            FixedTaxGenerator(self.rates)
        ]
    
    def generate_all_files(self) -> None:
        """Génère tous les fichiers CSV."""
        print("🚀 Génération des fichiers CSV pour les taxes sur l'or...")
        print("=" * 60)
        
        # Génération des données
        all_taxes = []
        all_repartitions = []
        
        for generator in self.generators:
            generator.generate()
            all_taxes.extend(generator.taxes)
            all_repartitions.extend(generator.repartition_lines)
        
        # Écriture des fichiers
        self._write_tax_groups()
        self._write_taxes(all_taxes)
        self._write_repartition_lines(all_repartitions)
        
        print("\n🎉 Génération terminée avec succès!")
        self._print_summary(all_taxes, all_repartitions)
    
    def _write_tax_groups(self) -> None:
        """Écrit le fichier des groupes de taxes."""
        data = []
        for key, config in self.TAX_GROUPS.items():
            data.append({
                'id': f'tax_group_{key}',
                'name': config.name,
                'sequence': config.sequence,
                'country_id:id': 'base.fr',
                # 'tax_payable_account_id:id': config.tax_payable_account_id
            })
        
        self.csv_writer.write_csv('account.tax.group.csv', data, self.TAX_GROUP_FIELDS)
    
    def _write_taxes(self, taxes: List[TaxConfig]) -> None:
        """Écrit le fichier des taxes."""
        data = []
        for tax in taxes:
            tax_dict = {
                'id': tax.id,
                'name': tax.name,
                'description': tax.description,
                'amount_type': tax.amount_type,
                'amount': tax.amount,
                'country_id:id': 'base.fr',
                'tax_group_id:id': tax.tax_group_id,
                'tax_scope': tax.tax_scope,
                'type_tax_use': tax.type_tax_use,
                'price_include': str(tax.price_include),
                'include_base_amount': str(tax.include_base_amount)
            }
            
            if tax.price_include_override:
                tax_dict['price_include_override'] = tax.price_include_override
            
            if tax.children_tax_ids:
                tax_dict['children_tax_ids:id'] = ','.join(tax.children_tax_ids)
            
            data.append(tax_dict)
        
        self.csv_writer.write_csv('account.tax.csv', data, self.TAX_FIELDS)
    
    def _write_repartition_lines(self, repartitions: List[TaxRepartitionConfig]) -> None:
        """Écrit le fichier des lignes de répartition."""
        data = []
        for rep in repartitions:
            data.append({
                'id': rep.id,
                'tax_id:id': f"{self_mod}.{rep.tax_id}",
                'document_type': "refund",
                'repartition_type': rep.repartition_type,
                'account_id:id': rep.account_id,
                'factor_percent': rep.factor_percent
            })
        
        self.csv_writer.write_csv('account.tax.repartition.line.csv', data, self.REPARTITION_FIELDS)
    
    def _print_summary(self, taxes: List[TaxConfig], repartitions: List[TaxRepartitionConfig]) -> None:
        """Affiche un résumé de la génération."""
        print(f"\n📊 Résumé:")
        print(f"  • {len(self.TAX_GROUPS)} groupes de taxes")
        print(f"  • {len(taxes)} taxes générées")
        print(f"  • {len(repartitions)} lignes de répartition")
        
        # Statistiques par type
        tpv_count = len([t for t in taxes if t.id.startswith('tpv')])
        tmp_count = len([t for t in taxes if t.id.startswith('tmp')])
        tfop_count = len([t for t in taxes if t.id.startswith('tfop')])
        
        print(f"\n📈 Répartition:")
        print(f"  • TPV: {tpv_count} taxes")
        print(f"  • TMP: {tmp_count} taxes")
        print(f"  • TFOP: {tfop_count} taxes")


def main():
    """Fonction principale."""
    print("🏗️  Générateur de fichiers CSV pour module Odoo - Taxes sur l'or")
    
    # Possibilité de personnaliser les taux
    custom_rates = TaxRates(
        tpv_ir=19.0,
        tpv_urssaf=17.2,
        tmp_metaux_precieux=11.0,
        tmp_objets_precieux=6.0,
        crds=0.5
    )
    
    generator = OdooTaxCSVGenerator(rates=custom_rates)
    generator.generate_all_files()
    
    print("\n💡 Fichiers prêts pour intégration dans votre module Odoo!")


if __name__ == "__main__":
    main()