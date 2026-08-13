# -*- coding: utf-8 -*-
"""Déclaration DMET — orchestration : collecte, pré-contrôle et génération.

La logique réglementaire est déléguée au sous-paquet ``tools`` (testé en
isolation). Ce modèle ne fait que rassembler les données Odoo, appeler ces
outils et persister le résultat (fichier, anomalies) pour la traçabilité.
"""

import base64
from datetime import date, datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError

from ..tools import dmet as dmet_tools
from ..tools import precheck as precheck_tools

_SEVERITY = [
    ('bloquante', "Bloquante"),
    ('bloquante_seuil', "Bloquante à seuil"),
    ('non_bloquante', "Non bloquante"),
]


class DmetDeclaration(models.Model):
    _name = 'fr.dmet.declaration'
    _description = "Déclaration DMET (achats au détail de métaux)"
    _order = 'millesime desc, id desc'

    name = fields.Char(compute='_compute_name', store=True)
    millesime = fields.Integer(
        string="Millésime (année des achats)", required=True,
        default=lambda self: fields.Date.today().year - 1,
    )
    type_declaration = fields.Selection(
        [('1', "Initiale"), ('2', "Rectificative")],
        string="Type de déclaration", default='1', required=True,
    )
    company_id = fields.Many2one(
        'res.company', string="Société déclarante (siège)", required=True,
        default=lambda self: self.env.company,
    )
    company_ids = fields.Many2many(
        'res.company', string="Établissements à agréger", required=True,
        default=lambda self: self.env.companies.ids,
        help="Les montants d'un même vendeur sont cumulés sur ces établissements.",
    )
    ordre = fields.Integer(
        string="Numéro d'ordre", default=1, required=True,
        help="Incrémenté à chaque dépôt successif au titre du même millésime.",
    )

    responsable_name = fields.Char(string="Responsable (nom, prénom, qualité)")
    responsable_phone = fields.Char(string="Téléphone du responsable")
    responsable_email = fields.Char(string="Courriel du responsable")
    remettant_siren = fields.Char(
        string="SIREN du remettant",
        help="Entité qui dépose le fichier. En dépôt pour compte propre, "
             "il s'agit du SIREN du déclarant.",
    )

    state = fields.Selection(
        [('draft', "Brouillon"), ('checked', "Pré-contrôlé"),
         ('generated', "Généré"), ('deposited', "Déposé")],
        default='draft', required=True,
    )
    verdict = fields.Selection(
        [('ok', "Conforme"), ('rejet', "Rejet prévisible")],
        string="Verdict du pré-contrôle", readonly=True,
    )

    currency_id = fields.Many2one(related='company_id.currency_id')
    vendor_count = fields.Integer(string="Nombre de vendeurs (Q)", readonly=True)
    amount_total = fields.Monetary(
        string="Montant TTC déclaré", readonly=True, currency_field='currency_id',
    )
    date_debut = fields.Date(
        string="Début de période", compute='_compute_period_dates', store=True)
    date_fin = fields.Date(
        string="Fin de période", compute='_compute_period_dates', store=True)
    first_move_date = fields.Date(string="1er rachat concerné", readonly=True)
    last_move_date = fields.Date(string="Dernier rachat concerné", readonly=True)
    move_count = fields.Integer(string="Nombre d'avoirs (rachats)", readonly=True)

    anomaly_ids = fields.One2many(
        'fr.dmet.anomaly', 'declaration_id', string="Anomalies détectées",
    )
    blocking_count = fields.Integer(compute='_compute_anomaly_counts')
    threshold_count = fields.Integer(compute='_compute_anomaly_counts')
    nonblocking_count = fields.Integer(compute='_compute_anomaly_counts')

    line_ids = fields.One2many(
        'fr.dmet.line', 'declaration_id', string="Lignes du dépôt", readonly=True,
    )

    file = fields.Binary(string="Fichier (.txt.gz)", readonly=True, attachment=True)
    filename = fields.Char(readonly=True)
    file_txt = fields.Binary(string="Fichier texte (.txt)", readonly=True, attachment=True)
    filename_txt = fields.Char(readonly=True)
    date_generation = fields.Datetime(readonly=True)

    # ------------------------------------------------------------------
    # Calculs
    # ------------------------------------------------------------------
    @api.depends('millesime', 'company_id')
    def _compute_name(self):
        for rec in self:
            rec.name = "DMET %s — %s" % (
                rec.millesime or '', rec.company_id.name or '')

    @api.depends('millesime')
    def _compute_period_dates(self):
        for rec in self:
            if rec.millesime:
                rec.date_debut = date(rec.millesime, 1, 1)
                rec.date_fin = date(rec.millesime, 12, 31)
            else:
                rec.date_debut = rec.date_fin = False

    @api.depends('anomaly_ids.severity')
    def _compute_anomaly_counts(self):
        for rec in self:
            sev = rec.anomaly_ids.mapped('severity')
            rec.blocking_count = sev.count('bloquante')
            rec.threshold_count = sev.count('bloquante_seuil')
            rec.nonblocking_count = sev.count('non_bloquante')

    @api.onchange('company_id')
    def _onchange_company_id(self):
        for rec in self:
            comp = rec.company_id
            rec.responsable_name = comp.dmet_responsable_name or rec.responsable_name
            rec.responsable_phone = comp.dmet_responsable_phone or rec.responsable_phone
            rec.responsable_email = comp.dmet_responsable_email or rec.responsable_email
            siret = (comp.partner_id.siret or '')
            digits = ''.join(c for c in siret if c.isdigit())
            if digits and not rec.remettant_siren:
                rec.remettant_siren = digits[:9]
            if comp and comp.id not in rec.company_ids.ids:
                rec.company_ids = [(4, comp.id)]

    # ------------------------------------------------------------------
    # Préparation des données
    # ------------------------------------------------------------------
    def _period(self):
        self.ensure_one()
        return date(self.millesime, 1, 1), date(self.millesime, 12, 31)

    def _header(self):
        self.ensure_one()
        siret = ''.join(c for c in (self.company_id.partner_id.siret or '')
                        if c.isdigit())
        return {'annee': str(self.millesime), 'siret': siret,
                'type_decl': self.type_declaration}

    def _declarant_dict(self):
        self.ensure_one()
        from ..tools import address as addr_tools
        p = self.company_id.partner_id
        parsed = addr_tools.parse_street(p.street or '')
        ape = ''.join(ch for ch in (self.company_id.ape or '') if ch.isalnum())
        return {
            'nom': self.company_id.name or '',
            'compl_adr': p.street2 or '',
            'num_voie': parsed['num_voie'],
            'indice_rep': parsed['indice_rep'],
            'voie': parsed['voie_zone'],
            'insee_commune': '',
            'libelle_commune': p.city or '',
            'code_postal': addr_tools.normalize_cp(p.zip or ''),
            'bureau': p.city or '',
            'code_activite': ape[:5],
            'date_emission': fields.Date.today().strftime('%Y%m%d'),
        }

    def _totalisation_dict(self):
        self.ensure_one()
        return {
            'responsable': self.responsable_name or '',
            'tel': self.responsable_phone or '',
            'email': self.responsable_email or '',
            'siren_remettant': self.remettant_siren or '',
        }

    def _collect_vendors(self):
        """Agrège les rachats (avoirs) par vendeur sur les établissements.

        Le vendeur est l'**entité commerciale**, pas le contact retenu sur la
        pièce : quand une société vend, la personne qui s'est présentée pour
        elle n'est pas un vendeur particulier — elle la représente (livre de
        police, art. R321-3 2°). Grouper sur `commercial_partner_id` évite
        deux erreurs de déclaration : déclarer un salarié comme vendeur
        personne physique, et scinder les ventes d'une même société entre ses
        contacts. Pour un particulier, l'entité commerciale est lui-même : le
        groupement est inchangé.

        Retourne (liste de dicts vendeur, map référence -> res.partner).
        """
        self.ensure_one()
        d_start, d_end = self._period()
        domain = [
            ('move_type', '=', 'out_refund'),
            ('state', '=', 'posted'),
            ('company_id', 'in', self.company_ids.ids),
            ('invoice_date', '>=', d_start),
            ('invoice_date', '<=', d_end),
        ]
        groups = self.env['account.move']._read_group(
            domain, groupby=['commercial_partner_id'],
            aggregates=['amount_total:sum', '__count'],
        )
        vendors = []
        for partner, amount_sum, nb_moves in groups:
            if not partner:
                continue
            amount = abs(amount_sum or 0.0)
            if dmet_tools.round_euro(amount) < 1:
                continue
            vendor = partner._dmet_vendor_dict(amount)
            vendor['_nb_moves'] = nb_moves
            vendors.append(vendor)
        # Ordre stable (montant décroissant) pour un fichier reproductible.
        vendors.sort(key=lambda v: v['montant'], reverse=True)
        return vendors

    def _deposit_line_vals(self, vendors):
        """Valeurs des lignes d'aperçu du dépôt (un enregistrement Q par vendeur)."""
        vals = []
        for v in vendors:
            is_company = bool(v.get('is_company'))
            if is_company:
                personne = v.get('raison_sociale') or ''
            else:
                personne = ' '.join(p for p in (v.get('nom'), v.get('prenoms')) if p).strip()
            bd = False
            if not is_company:
                try:
                    bd = date(int(v['annee_naiss']), int(v['mois_naiss']), int(v['jour_naiss']))
                except (KeyError, ValueError, TypeError):
                    bd = False
            vals.append((0, 0, {
                'partner_id': v.get('_partner_id'),
                'personne': personne or (v.get('nom') or ''),
                'vendor_kind': 'pm' if is_company else 'pp',
                'foreign': bool(v.get('foreign')),
                'birthdate': bd,
                'code_postal': v.get('code_postal') or '',
                'commune': v.get('libelle_commune') or '',
                'nb_rachats': v.get('_nb_moves') or 0,
                'montant': dmet_tools.round_euro(v.get('montant') or 0),
            }))
        return vals

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------
    def action_precheck(self):
        self.ensure_one()
        vendors = self._collect_vendors()
        report = precheck_tools.check_file(
            self._header(), self._declarant_dict(), vendors)
        d_start, d_end = self._period()
        stats = self.env['account.move']._read_group(
            [('move_type', '=', 'out_refund'), ('state', '=', 'posted'),
             ('company_id', 'in', self.company_ids.ids),
             ('invoice_date', '>=', d_start), ('invoice_date', '<=', d_end)],
            [], ['invoice_date:min', 'invoice_date:max', '__count'],
        )
        first_d, last_d, nb_moves = stats[0] if stats else (False, False, 0)

        self.anomaly_ids.unlink()
        self.line_ids.unlink()
        lines = [(0, 0, {
            'zone': f.zone, 'label': f.label, 'severity': f.severity,
            'message': f.message, 'partner_ref': f.ref,
            'partner_id': f.partner_id,
        }) for f in report['findings']]

        self.write({
            'anomaly_ids': lines,
            'line_ids': self._deposit_line_vals(vendors),
            'verdict': 'ok' if report['verdict'] == 'OK' else 'rejet',
            'vendor_count': report['nb_vendors'],
            'amount_total': sum(dmet_tools.round_euro(v['montant']) for v in vendors),
            'first_move_date': first_d,
            'last_move_date': last_d,
            'move_count': nb_moves,
            'state': 'checked' if self.state == 'draft' else self.state,
        })
        return True

    def action_generate(self):
        self.ensure_one()
        vendors = self._collect_vendors()
        if not vendors:
            raise UserError(_("Aucun vendeur à déclarer sur la période %s.") % self.millesime)

        self.action_precheck()

        content = dmet_tools.build_file(
            self._header(), self._declarant_dict(), vendors, self._totalisation_dict())
        raw = dmet_tools.encode_utf8(content)
        siren = ''.join(c for c in (self.remettant_siren or '') if c.isdigit())[:9]
        now = datetime.now()
        fname = dmet_tools.build_filename(siren, self.millesime, self.ordre, now)
        gz = dmet_tools.gzip_bytes(raw, filename=fname)

        self.write({
            'file_txt': base64.b64encode(raw), 'filename_txt': fname,
            'file': base64.b64encode(gz), 'filename': fname + '.gz',
            'date_generation': fields.Datetime.now(),
            'state': 'generated',
        })
        return True

    def action_mark_deposited(self):
        self.write({'state': 'deposited'})

    def action_reset_draft(self):
        self.write({'state': 'draft'})


class DmetAnomaly(models.Model):
    _name = 'fr.dmet.anomaly'
    _description = "Anomalie de pré-contrôle DMET"
    _order = 'severity, zone'

    declaration_id = fields.Many2one(
        'fr.dmet.declaration', required=True, ondelete='cascade')
    zone = fields.Char(string="Zone (CDC)")
    label = fields.Char(string="Libellé")
    severity = fields.Selection(_SEVERITY, string="Gravité")
    message = fields.Char(string="Aide à la correction")
    partner_ref = fields.Char(string="Vendeur")
    partner_id = fields.Many2one('res.partner', string="Fiche")

    def action_open_partner(self):
        self.ensure_one()
        if not self.partner_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

class DmetLine(models.Model):
    _name = 'fr.dmet.line'
    _description = "Ligne de dépôt DMET (aperçu enregistrement Q)"
    _order = 'montant desc, id'

    declaration_id = fields.Many2one(
        'fr.dmet.declaration', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string="Fiche")
    personne = fields.Char(string="Personne / Raison sociale")
    vendor_kind = fields.Selection(
        [('pp', "Personne physique"), ('pm', "Personne morale")],
        string="Nature")
    foreign = fields.Boolean(string="Étranger")
    birthdate = fields.Date(string="Naissance")
    code_postal = fields.Char(string="Code postal")
    commune = fields.Char(string="Commune")
    nb_rachats = fields.Integer(string="Quantité (rachats)")
    montant = fields.Integer(string="Montant TTC annuel (€)")

    def action_open_partner(self):
        self.ensure_one()
        if not self.partner_id:
            return False
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'res.partner',
            'res_id': self.partner_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
