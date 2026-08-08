# -*- coding: utf-8 -*-
"""Projection d'un partenaire vers un dictionnaire « vendeur » (enregistrement Q).

La transformation reste fine : elle lit les champs Odoo et délègue la mise en
forme réglementaire au sous-paquet ``tools`` (adresse, translittération...).
"""

from odoo import models

from ..tools import address as addr_tools


class ResPartner(models.Model):
    _inherit = 'res.partner'

    def _dmet_title(self):
        """Civilité au format DGFiP (zone Q 013) : 'M', 'MME' ou ''."""
        self.ensure_one()
        raw = ''
        if self.title:
            raw = (self.title.shortcut or self.title.name or '')
        raw = raw.strip().upper().rstrip('.')
        if raw in ('M', 'MR', 'MONSIEUR'):
            return 'M'
        if raw in ('MME', 'MRS', 'MS', 'MADAME', 'MLLE', 'MADEMOISELLE'):
            return 'MME'
        return ''

    def _dmet_vendor_dict(self, amount):
        """Construit le dict consommé par ``tools.dmet.build_q`` / ``precheck``.

        `amount` : montant TTC annuel cumulé (arrondi ensuite par le générateur).
        """
        self.ensure_one()
        is_company = self.is_company
        foreign = bool(self.country_id and self.country_id.code != 'FR')
        parsed = addr_tools.parse_street(self.street or '')

        vals = {
            '_partner_id': self.id,
            'is_company': is_company,
            'foreign': foreign,
            'raison_sociale': self.name if is_company else '',
            'siret_vendeur': (self.siret or '') if is_company else '',
            'nom': '' if is_company else (self.lastname or self.name or ''),
            'prenoms': '' if is_company else (self.firstname or ''),
            'nom_usage': '',
            'titre': '' if is_company else self._dmet_title(),
            'compl_adr': self.street2 or '',
            'num_voie': parsed['num_voie'],
            'indice_rep': parsed['indice_rep'],
            'voie': parsed['voie_zone'],
            'insee_commune': '',            # code INSEE commune adresse (non bloquant)
            'libelle_commune': self.city or '',
            'code_postal': addr_tools.normalize_cp(self.zip or '', foreign=foreign),
            'bureau': self.city or '',
            'montant': amount,
        }

        if not is_company:
            bd = self.birthdate
            # Le « 99 » (né à l'étranger) se déduit du pays de NAISSANCE, jamais
            # du pays de l'adresse : sinon un natif de France résidant à
            # l'étranger serait déclaré « étranger », et un natif de l'étranger
            # résidant en France ne le serait pas.
            foreign_birth = bool(
                self.birth_country_id and self.birth_country_id.code != 'FR'
            )
            # Libellé du lieu de naissance : la commune si renseignée ; sinon,
            # pour une naissance à l'étranger, le pays (déjà saisi dans
            # birth_country_id) — évite de le ressaisir dans birth_city.
            commune_naiss = self.birth_city or self.birthplace
            if not commune_naiss and foreign_birth:
                commune_naiss = self.birth_country_id.name
            vals.update({
                'jour_naiss': ('%02d' % bd.day) if bd else '',
                'mois_naiss': ('%02d' % bd.month) if bd else '',
                'annee_naiss': ('%04d' % bd.year) if bd else '',
                'dept_naiss': self.birth_department or ('99' if foreign_birth else ''),
                'insee_naiss': self.birth_insee_code or '',
                'commune_naiss': commune_naiss or '',
            })
        return vals
