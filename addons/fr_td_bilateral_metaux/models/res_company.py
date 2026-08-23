# -*- coding: utf-8 -*-
"""Paramètres de déclaration DMET portés par la société (valeurs par défaut)."""

from odoo import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    dmet_responsable_name = fields.Char(
        string="Cerfa 2093-SD — Responsable (nom, prénom, qualité)",
        help="Personne à contacter par la DGFiP (zone T 007 du fichier).",
    )
    dmet_responsable_phone = fields.Char(string="DMET — Téléphone du responsable")
    dmet_responsable_email = fields.Char(string="DMET — Courriel du responsable")
