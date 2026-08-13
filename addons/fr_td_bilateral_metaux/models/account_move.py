# -*- coding: utf-8 -*-

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        self._dmet_check_vendor_completeness()
        return super()._post(soft=soft)

    def _dmet_check_vendor_completeness(self):
        """Bloque la validation d'un rachat (avoir) à un particulier tant que les
        données **obligatoires** du vendeur sont incomplètes.

        Périmètre aligné sur la sélection DMET (``out_refund``), personnes
        physiques uniquement — au sens de l'**entité commerciale** du contact
        retenu, non du contact lui-même : la personne qui vend pour le compte
        d'une société n'est pas un vendeur particulier, elle la représente
        (livre de police, art. R321-3 2°). Lui réclamer date et pays de
        naissance reviendrait à la déclarer comme vendeuse, ce qu'elle n'est
        pas. Pour un particulier, l'entité commerciale est lui-même.

        Champs contrôlés :

        - **Nom** et **prénom** — DMET (Q014/Q015) et livre de police (R321-3) ;
        - **Pays de naissance** — détermine le « 99 » (naissance à l'étranger) du
          DMET ;
        - **Adresse** (rue, code postal, ville) — domicile (R321-3) et zones
          DMET adresse ;
        - **Pièce d'identité** complète — livre de police (art. R321-3 : nature,
          numéro, date de délivrance et autorité émettrice ; le *lieu* de
          délivrance n'est pas exigé par le texte).

        L'obligation naît de l'achat : on la contrôle donc au moment de valider
        l'avoir, sans imposer ces champs à tous les contacts.
        """
        # Backfill historique : exemption explicite. Les rachats antérieurs à
        # l'adoption du logiciel sont réinjectés pour le DMET / la concordance du
        # livre de police ; leur pièce d'identité et leur adresse complètes
        # n'existent qu'au format papier (livre de police tenu à l'époque). On ne
        # fabrique pas de données (ce serait corrompre le livre de police) : on
        # exempte ces imports via un contexte dédié, sans affaiblir le contrôle
        # des nouveaux rachats saisis dans le logiciel.
        if self.env.context.get('dmet_backfill'):
            return
        checks = [
            ('lastname', "nom"),
            ('firstname', "prénom"),
            ('birth_country_id', "pays de naissance"),
            ('street', "adresse (rue)"),
            ('zip', "code postal"),
            ('city', "ville"),
        ]
        problems = []
        for move in self:
            if move.move_type != "out_refund":
                continue
            partner = move.commercial_partner_id
            if not partner or partner.is_company:
                continue
            missing = [label for fname, label in checks if not partner[fname]]
            if not partner.id_doc_complete:
                missing.append("pièce d'identité (R321-3)")
            if missing:
                problems.append((move, partner, missing))
        if problems:
            details = "\n".join(
                "- %s (%s) : %s" % (
                    move.display_name, partner.display_name, ", ".join(missing))
                for move, partner, missing in problems
            )
            raise UserError(_(
                "Rachat à un particulier : les données obligatoires du vendeur "
                "(déclaration DMET / livre de police) sont incomplètes. "
                "Complétez la fiche avant de valider :\n%s", details
            ))
