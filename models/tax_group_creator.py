
from odoo import api, SUPERUSER_ID

#
def create_gold_tax_groups(cr, registry):
    create_gold_tax_groups__added_value(cr, registry)
    create_gold_tax_groups__fixed(cr, registry)

#
def create_gold_tax_groups__added_value(cr, registry):
    ###
    # Post init hook qui crée 21 groupes de taxes automatiques pour la plus-value sur l'or.
    # Chaque groupe contient 2 taxes : Impôts (base 19%) et Prélèvements Sociaux (base 17.2%),
    # appliquées avec le pourcentage du groupe.
    ###
    env = api.Environment(cr, SUPERUSER_ID, {})
    Tax = env['account.tax']

    # Boucle pour créer 21 groupes de taxes (de 100% à 0% par pas de 5)
    for i in range(1, 22):  # i de 1 à 21 inclus
        percentage = 100 - (i - 1) * 5  # 100, 95, 90, …, 0
        # Définir le label de la durée en fonction du groupe
        if i == 1:
            years_label = "0-2 ANS"
        elif i == 21:
            years_label = "22+ ANS"
        else:
            years_label = f"{i}-{i+1} ANS"
        
        group_name = f"Métaux Précieux - Plus-value - {years_label} / {percentage}% / {taux_impots + taux_sociaux}%"
        
        # Calcul des taux effectifs
        taux_impots = round(-19 * (percentage / 100.0), 2)
        taux_sociaux = round(-17.2 * (percentage / 100.0), 2)
        
        # Création de la taxe pour les Impôts
        Tax.create({
            'name': group_name + " Impôts",
            'amount': taux_impots,
            'amount_type': 'percent',
            'type_tax_use': 'sale',  # Modifier si nécessaire (ex: 'purchase')
            'description': f"Partie impôt du régime de la plus-value sur la revente d'or physique, correspondant à {years_label} de détention. Base: 19%, appliqué à {percentage}%.",
        })
        
        # Création de la taxe pour les Prélèvements Sociaux
        Tax.create({
            'name': group_name + " Prélèvements Sociaux",
            'amount': taux_sociaux,
            'amount_type': 'percent',
            'type_tax_use': 'sale',  # Modifier si nécessaire
            'description': f"Partie prélèvements sociaux du régime de la plus-value sur la revente d'or physique, correspondant à {years_label} de détention. Base: 17.2%, appliqué à {percentage}%.",
        })

def create_gold_tax_groups__fixed(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    Tax = env['account.tax']

    # Création du groupe de taxe "Taxe Métaux Précieux - 11,5%"
    metaux_group_name = "Métaux Précieux - Forfaitaire - 11,5%"
    # Taux fixes pour ce groupe
    taux_impots_metaux = -11.0   # 11% pour l'impôt
    taux_crds = -0.5             # 0.5% pour la CRDS

    Tax.create({
        'name': metaux_group_name + " - TMP",
        'amount': taux_impots_metaux,
        'amount_type': 'percent',
        'type_tax_use': 'sale',
        'description': f"Partie de la taxe forfaitaire sur la revente d'or physique liée à la Taxe sur les Métaux Précieux. Fixé à {taux_impots_metaux}%.",
    })
    Tax.create({
        'name': metaux_group_name + " - CRDS",
        'amount': taux_crds,
        'amount_type': 'percent',
        'type_tax_use': 'sale',
        'description': f"Partie de la taxe forfaitaire sur la revente d'or physique liée à la Contribution au Remboursement de la Dette Sociale. Fixé à {taux_crds}%.",
    })