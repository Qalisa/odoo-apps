# -*- coding: utf-8 -*-
"""Les regles visees etant `noupdate`, le XML ne les atteint pas."""

from odoo import SUPERUSER_ID, api

from odoo.addons.stats_access_control.hooks import reattacher_les_regles


def migrate(cr, version):
    reattacher_les_regles(api.Environment(cr, SUPERUSER_ID, {}))
