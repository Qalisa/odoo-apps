# -*- coding: utf-8 -*-
"""Le lot du stock porte le numéro d'ordre du registre.

« Chaque objet exposé à la vente ou détenu en stock est affecté d'un numéro
d'ordre. […] Le numéro d'ordre est porté sur le registre et figure de manière
apparente sur chaque objet ou lot d'objets » (c. pén., art. R321-4).

Odoo sait déjà étiqueter un lot, le suivre en stock et le retrouver à la
sortie ; il le nomme seulement d'après sa propre séquence. Deux numéros pour
une même chose, c'en est un de trop : l'étiquette du comptoir et la ligne du
registre finiraient par diverger, et c'est l'étiquette qu'un contrôle a sous
les yeux. Le lot reprend donc le numéro d'ordre, et rien d'autre.

Reste que les deux ne naissent pas au même instant. Le numéro d'ordre est
attribué à la comptabilisation de l'avoir ; Odoo réclame le lot à la
validation de la réception. L'ordre est donc imposé, et il ne l'est pas pour
la commodité du logiciel : on ne fait pas entrer en stock un métal dont
l'achat n'est pas encore arrêté. Le refus est explicite parce que
l'alternative — nommer le lot provisoirement puis le renommer — laisse une
fenêtre pendant laquelle l'étiquette ment.
"""

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.mail import plaintext2html


class StockMove(models.Model):
    _inherit = 'stock.move'

    police_ligne_id = fields.Many2one(
        'livre.police.ligne', string="Inscription au registre",
        compute='_compute_police_ligne_id',
        help="L'inscription née de l'avoir qui a acheté ce métal. Elle "
             "n'existe qu'une fois l'avoir comptabilisé : c'est elle qui "
             "porte le numéro d'ordre dont le lot prendra le nom.",
    )
    police_numero_ordre = fields.Char(
        string="N° d'ordre", related='police_ligne_id.numero_ordre',
        readonly=True,
    )
    police_description = fields.Text(
        # Et non `description_picking`, qui est un champ libre rempli a la
        # creation du mouvement, depuis l'article : a cet instant la
        # description du registre n'existe pas encore. Celle-ci se lit, elle
        # ne s'ecrit pas, et elle apparait des que l'avoir est comptabilise.
        string="Description au registre",
        related='police_ligne_id.description', readonly=True,
        help="Les objets tels que le registre les a decrits. « 1 collier "
             "maille gourmette, 1 bague sertie, or jaune 18k » dit ce que "
             "« 18k Or 750 ‰(gr) » ne dira jamais.",
    )

    @api.depends('sale_line_id', 'sale_line_id.invoice_lines')
    def _compute_police_ligne_id(self):
        """Remonte du mouvement à l'inscription, par la facture.

        Le chemin est celui de la marchandise : un mouvement naît d'une ligne
        de devis, la ligne de devis se facture, et c'est la ligne de facture
        que le registre a recopiée. Rien ne relie directement le stock au
        registre, et c'est tant mieux — le registre atteste l'achat, pas le
        rangement.
        """
        Ligne = self.env['livre.police.ligne'].sudo()
        for mouvement in self:
            lignes_facture = mouvement.sale_line_id.invoice_lines
            mouvement.police_ligne_id = Ligne.search(
                [('move_line_id', 'in', lignes_facture.ids)], limit=1,
            ) if lignes_facture else False

    def _police_entrees_de_rachat(self):
        """Les mouvements d'entrée nés d'un rachat, qui doivent un numéro."""
        return self.filtered(
            lambda mouvement: mouvement.picking_code == 'incoming'
            and mouvement.sale_line_id.police_origin_required)


class StockMoveLine(models.Model):
    _inherit = 'stock.move.line'

    def _prepare_new_lot_vals(self):
        """Le lot naît décrit.

        Le nom du lot dit lequel ; la description dit lequel c'est. Au moment
        de choisir ce qui sort du stock, « 000004 — 21,6 g » ne se distingue
        pas de son voisin, quand « 1 lot de chaînes et pendentifs, titres
        mêlés » se reconnaît sans hésiter.

        Elle est portée à la naissance du lot, et pas après : c'est le seul
        instant où l'inscription d'origine est certaine — le livrable qui
        nomme le lot a déjà refusé toute réception sans elle.
        """
        valeurs = super()._prepare_new_lot_vals()
        inscription = self.move_id.police_ligne_id
        if not inscription:
            return valeurs
        valeurs['note'] = plaintext2html(inscription.description or '')
        # Le lot appartient à l'agence qui l'a inscrit. Sans société, Odoo
        # exige que le nom soit unique pour l'article dans toute la base — et
        # chaque agence repart de 000001. Le second « 000004 » sur le même
        # article serait refusé, et la réception avec lui.
        valeurs['company_id'] = inscription.company_id.id
        return valeurs


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def button_validate(self):
        self._police_check_inscription()
        self._police_nommer_les_lots()
        return super().button_validate()

    def _action_done(self):
        """Le métal qui part s'inscrit, une fois le transfert réellement fait.

        Et non dans `button_validate`, qui peut rendre un assistant — reliquat,
        transfert immédiat — et rendre la main sans que rien ne soit sorti.
        `_action_done` est le moment où le stock a bougé.
        """
        resultat = super()._action_done()
        self.env['livre.police.ligne']._inscrire_sorties(self)
        return resultat

    def _police_check_inscription(self):
        """Refuse de réceptionner un métal dont l'achat n'est pas inscrit."""
        sans_inscription = self.move_ids._police_entrees_de_rachat().filtered(
            lambda mouvement: not mouvement.police_ligne_id)
        if not sans_inscription:
            return
        raise UserError(_(
            "Ce métal n'est pas encore inscrit au registre.\n\n"
            "Le lot prend le numéro d'ordre de l'inscription, et "
            "l'inscription naît à la comptabilisation de l'avoir. "
            "Comptabilisez l'avoir, puis revenez valider la réception : le "
            "numéro se posera seul.\n\n"
            "Sans cela, le lot recevrait un numéro de séquence sans rapport "
            "avec le registre, et l'étiquette apposée sur le métal ne "
            "désignerait plus rien (c. pén., art. R321-4).\n\n"
            "Articles concernés : %(articles)s",
            articles=", ".join(sans_inscription.mapped('product_id.name'))))

    def _police_nommer_les_lots(self):
        """Pose le numéro d'ordre comme nom de lot, avant la validation.

        On écrase ce qui aurait été saisi : le nom du lot n'est pas un choix
        d'opérateur, c'est une donnée du registre. Odoo créera le lot lui-même
        à partir de ce nom, comme il le fait pour toute réception.
        """
        for mouvement in self.move_ids._police_entrees_de_rachat():
            if mouvement.product_id.tracking == 'none':
                continue
            numero = mouvement.police_ligne_id.numero_ordre
            lignes = mouvement.move_line_ids.filtered(
                lambda ligne: not ligne.lot_id)
            if numero and lignes:
                lignes.lot_name = numero
