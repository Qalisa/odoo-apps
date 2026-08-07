# -*- coding: utf-8 -*-

from odoo import _, models
from odoo.exceptions import UserError


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        self._dmet_check_vendor_id_document()
        return super()._post(soft=soft)

    def _dmet_check_vendor_id_document(self):
        """Bloque la validation d'un rachat (avoir) à un particulier tant que la
        pièce d'identité du vendeur est incomplète (art. R321-3 du code pénal).

        Périmètre aligné sur la sélection DMET (``out_refund``). Seules les
        personnes physiques sont concernées : une personne morale n'a pas de
        pièce d'identité au sens de l'art. R321-3.
        """
        blocked = []
        for move in self:
            if move.move_type != "out_refund":
                continue
            partner = move.partner_id
            if not partner or partner.is_company:
                continue
            if not partner.id_doc_complete:
                blocked.append((move, partner))
        if blocked:
            details = "\n".join(
                "- %s : %s" % (move.display_name, partner.display_name)
                for move, partner in blocked
            )
            raise UserError(_(
                "Rachat à un particulier : la pièce d'identité du vendeur est "
                "incomplète (art. R321-3). Renseignez la nature, le numéro, la "
                "date et le lieu de délivrance, et l'autorité, avant de valider "
                ":\n%s", details
            ))
