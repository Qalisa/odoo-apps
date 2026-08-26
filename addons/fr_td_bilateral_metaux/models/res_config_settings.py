# -*- coding: utf-8 -*-
"""Les deux clés publiques de la DGFiP, déposées une fois pour toutes.

Le cahier des charges TD/bilatéral publie deux clés distinctes — une pour les
fichiers de test, une pour les fichiers de production — et prévient que « le
type de clé qui ne correspond pas à la nature du fichier conduit à son rejet »
(§ 2.4.3.4). Elles se téléchargent sur impots.gouv.fr, espace Tiers
déclarants, sous forme d'archives ZIP.

Elles vivent ici, dans les paramètres système, et non sur la société : ce sont
les clés de l'administration, les mêmes pour tous les établissements et pour
tous les déclarants de France. Les dupliquer par société inviterait à en avoir
deux versions différentes.

**Ces clés sont publiques.** Rien n'est confidentiel dans ce qui est stocké ;
ce qui compte est de savoir *laquelle* est en place, d'où l'empreinte relevée
au téléversement et affichée à côté du champ. Se tromper de clé ne provoque
aucune erreur au chiffrement : le rejet arrive plus tard, chez la DGFiP, sur
un dépôt qu'on croyait fait.
"""

import base64
from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..tools import openpgp

# Paramètres système où atterrissent les clés. Le suffixe dit l'environnement
# de dépôt, pas celui d'Odoo : une base de test peut préparer un fichier réel.
PARAM_CLE = {
    'test': 'fr_td_bilateral_metaux.gpg_key_test',
    'production': 'fr_td_bilateral_metaux.gpg_key_prod',
}
PARAM_INFO = {env: cle + '_info' for env, cle in PARAM_CLE.items()}
PARAM_NOM = {env: cle + '_filename' for env, cle in PARAM_CLE.items()}

ENVIRONNEMENTS = [
    ('test', "Test (plateforme partenaire)"),
    ('production', "Production (dépôt réel)"),
]


def cle_publique(env, environnement):
    """Matière de la clé DGFiP pour cet environnement, ou une erreur claire."""
    valeur = env['ir.config_parameter'].sudo().get_param(
        PARAM_CLE[environnement])
    if not valeur:
        raise UserError(_(
            "La clé publique DGFiP « %(env)s » n'est pas chargée. "
            "Téléversez-la dans Paramètres ▸ Paramètres généraux ▸ "
            "Cerfa 2093-SD. Elle se télécharge sur impots.gouv.fr, espace "
            "Tiers déclarants, cahier des charges TD/bilatéral.",
            env=dict(ENVIRONNEMENTS)[environnement]))
    return base64.b64decode(valeur)


def resume_cle(matiere):
    """Ligne lisible décrivant une clé : empreinte, titulaire, échéance."""
    infos = openpgp.decrire_cle(matiere)
    empreinte = infos['fingerprint']
    groupes = " ".join(empreinte[i:i + 4] for i in range(0, len(empreinte), 4))
    morceaux = [groupes]
    if infos['uid']:
        morceaux.append(infos['uid'])
    if infos['expires']:
        try:
            echeance = datetime.utcfromtimestamp(int(infos['expires']))
            morceaux.append("expire le %s" % echeance.strftime('%d/%m/%Y'))
        except (TypeError, ValueError):
            pass
    else:
        morceaux.append("sans échéance")
    return " — ".join(morceaux)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    dmet_gpg_key_test = fields.Binary(
        string="Clé publique DGFiP — fichiers de test",
        help="Archive ZIP telle qu'elle se télécharge sur impots.gouv.fr, ou "
             "la clé seule. Elle chiffre les fichiers déposés sur la "
             "plateforme partenaire de tests.",
    )
    dmet_gpg_key_test_filename = fields.Char()
    dmet_gpg_key_test_info = fields.Char(readonly=True)

    dmet_gpg_key_prod = fields.Binary(
        string="Clé publique DGFiP — fichiers de production",
        help="Archive ZIP telle qu'elle se télécharge sur impots.gouv.fr, ou "
             "la clé seule. Elle chiffre le dépôt réel, celui qui vaut "
             "déclaration.",
    )
    dmet_gpg_key_prod_filename = fields.Char()
    dmet_gpg_key_prod_info = fields.Char(readonly=True)

    @api.model
    def get_values(self):
        valeurs = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        for environnement in PARAM_CLE:
            suffixe = 'test' if environnement == 'test' else 'prod'
            valeurs.update({
                'dmet_gpg_key_%s' % suffixe:
                    params.get_param(PARAM_CLE[environnement]) or False,
                'dmet_gpg_key_%s_filename' % suffixe:
                    params.get_param(PARAM_NOM[environnement]) or False,
                'dmet_gpg_key_%s_info' % suffixe:
                    params.get_param(PARAM_INFO[environnement]) or False,
            })
        return valeurs

    def set_values(self):
        """Une clé illisible est refusée au téléversement, pas à la génération.

        C'est le seul moment où quelqu'un regarde : découvrir en janvier, la
        veille de l'échéance, que le fichier téléversé était le guide de
        chiffrement et non la clé, c'est le découvrir trop tard.
        """
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        for environnement in PARAM_CLE:
            suffixe = 'test' if environnement == 'test' else 'prod'
            b64 = self['dmet_gpg_key_%s' % suffixe] or ''
            if isinstance(b64, bytes):
                b64 = b64.decode()
            if b64 == (params.get_param(PARAM_CLE[environnement]) or ''):
                continue
            if not b64:
                for param in (PARAM_CLE, PARAM_NOM, PARAM_INFO):
                    params.set_param(param[environnement], '')
                continue
            try:
                matiere = openpgp.extraire_cle(base64.b64decode(b64))
                resume = resume_cle(matiere)
            except openpgp.ErreurChiffrement as erreur:
                raise UserError(_(
                    "Clé « %(env)s » refusée : %(motif)s",
                    env=dict(ENVIRONNEMENTS)[environnement],
                    motif=str(erreur)))
            # On range la clé extraite, pas l'archive : ce qui sert au
            # chiffrement est ce qu'on a lu et vérifié.
            params.set_param(PARAM_CLE[environnement],
                             base64.b64encode(matiere).decode())
            params.set_param(PARAM_NOM[environnement],
                             self['dmet_gpg_key_%s_filename' % suffixe] or '')
            params.set_param(PARAM_INFO[environnement], resume)
