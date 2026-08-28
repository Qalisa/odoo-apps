# -*- coding: utf-8 -*-
"""Rejouer la chaîne, et imprimer ce qu'on a trouvé.

« L'opérateur doit être en mesure d'apporter la preuve de la fiabilité du
système informatique utilisé et de la chronologie des écritures présentées
sous forme de listes » (CGI, ann. IV, art. 56 J sexdecies, 1° c, auquel
renvoie le 2° c).

Une chaîne d'empreintes ne prouve rien tant que personne ne la recalcule.
Ce contrôle refait le calcul de chaque page à partir de son contenu actuel et
le compare au chiffre de contrôle scellé. Il vérifie trois choses, qui se
cassent différemment :

* **le contenu** — l'empreinte recalculée doit retrouver celle qui a été
  scellée. Si une mention a bougé en base, elle ne la retrouve pas ;
* **le chaînage** — le contrôle porté en tête d'une page doit être celui
  scellé en pied de la précédente. Retirer une page entière ne casse aucune
  empreinte de contenu, mais casse le chaînage ;
* **la continuité** — les numéros d'ordre et les numéros de page se suivent
  sans trou. Une suppression faite hors d'Odoo ne casserait ni l'un ni
  l'autre des deux premiers contrôles, mais laisserait un trou.

Le résultat s'imprime : c'est ce document qu'on présente, pas une capture
d'écran.
"""

from odoo import _, api, fields, models


class LivrePoliceControle(models.TransientModel):
    _name = 'livre.police.controle'
    _description = "Livre de police - contrôle d'intégrité"

    company_id = fields.Many2one(
        'res.company', string="Société", required=True,
        default=lambda self: self.env.company,
    )
    date_debut = fields.Date(
        string="À partir du",
        help="Laisser vide pour contrôler le registre depuis son ouverture.",
    )
    date_fin = fields.Date(string="Jusqu'au")

    def action_controler(self):
        self.ensure_one()
        return self.env.ref(
            'fr_livre_police_metaux.action_report_livre_police_controle'
        ).report_action(self)

    # ------------------------------------------------------------------

    def _pages(self):
        self.ensure_one()
        domaine = [('company_id', '=', self.company_id.id)]
        if self.date_debut:
            domaine.append(('date', '>=', self.date_debut))
        if self.date_fin:
            domaine.append(('date', '<=', self.date_fin))
        return self.env['livre.police.page'].sudo().search(
            domaine, order='numero')

    def _resultats(self):
        """Un constat par page, plus le relevé des trous de numérotation."""
        self.ensure_one()
        pages = self._pages()
        constats = []
        for page in pages:
            if not page.scellee:
                constats.append({
                    'page': page, 'etat': 'ouverte',
                    'libelle': "Page non scellée",
                    'detail': "Elle peut encore recevoir des inscriptions ; "
                              "son chiffre de contrôle n'est pas arrêté.",
                    'attendu': '', 'constate': '',
                })
                continue
            recalcule = page._empreinte(page.controle_precedent)
            if recalcule != page.controle:
                constats.append({
                    'page': page, 'etat': 'altere',
                    'libelle': "Contenu altéré",
                    'detail': "Le chiffre de contrôle recalculé sur le "
                              "contenu actuel ne retrouve pas celui qui a été "
                              "scellé : une mention a été modifiée depuis.",
                    'attendu': page.controle, 'constate': recalcule,
                })
                continue
            precedente = page.page_precedente_id
            if precedente and page.controle_precedent != precedente.controle:
                constats.append({
                    'page': page, 'etat': 'chaine',
                    'libelle': "Chaînage rompu",
                    'detail': "Le contrôle porté en tête n'est pas celui "
                              "scellé en pied de la page %s." % precedente.numero,
                    'attendu': precedente.controle,
                    'constate': page.controle_precedent or '',
                })
                continue
            constats.append({
                'page': page, 'etat': 'conforme',
                'libelle': "Conforme",
                'detail': "", 'attendu': page.controle, 'constate': recalcule,
            })
        return constats

    def _trous(self):
        """Numéros manquants, côté pages et côté inscriptions.

        Une empreinte ne dit rien de ce qui n'existe plus. La continuité, si.
        """
        self.ensure_one()

        def manquants(numeros):
            entiers = sorted(int(n) for n in numeros if n and n.isdigit())
            if not entiers:
                return []
            attendus = set(range(entiers[0], entiers[-1] + 1))
            return sorted(attendus - set(entiers))

        pages = self._pages()
        lignes = self.env['livre.police.ligne'].sudo().search(
            [('page_id', 'in', pages.ids)])
        return {
            'pages': manquants(pages.mapped('numero')),
            'inscriptions': manquants(lignes.mapped('numero_ordre')),
        }

    def _synthese(self):
        self.ensure_one()
        constats = self._resultats()
        trous = self._trous()
        etats = [c['etat'] for c in constats]
        return {
            'constats': constats,
            'trous': trous,
            'total': len(constats),
            'conformes': etats.count('conforme'),
            'ouvertes': etats.count('ouverte'),
            'anomalies': etats.count('altere') + etats.count('chaine'),
            'indemne': (not etats.count('altere') and not etats.count('chaine')
                        and not trous['pages'] and not trous['inscriptions']),
        }
