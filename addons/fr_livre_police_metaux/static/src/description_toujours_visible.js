/**
 * La zone de description reste ouverte sur les articles qui la réclament.
 *
 * Odoo replie cette zone sous la désignation de l'article : il faut cliquer
 * l'icône, ou frapper Entrée, pour la faire apparaître. Un opérateur qui ne
 * connaît pas le geste ne voit rien à remplir — et découvre l'obligation au
 * refus de la confirmation.
 *
 * Le pli n'est défait que sur les articles configurés. Il suit le choix de
 * l'article, non le signe de la quantité : au comptoir on choisit l'article
 * avant de poser sur la balance, et la zone doit être ouverte à ce moment-là.
 *
 * Le composant sert aussi des vues où ce module n'a rien déclaré — le
 * sous-formulaire d'une ligne, une liste d'un autre module. Le champ y est
 * absent, et le lire ferait échouer la vue entière : on ne le consulte donc
 * que là où la vue le charge.
 */

import { patch } from "@web/core/utils/patch";
import { useEffect } from "@odoo/owl";
import {
    ProductLabelSectionAndNoteField,
} from "@account/components/product_label_section_and_note_field/product_label_section_and_note_field";

const CHAMP = "police_description_expected";

function descriptionAttendue(record) {
    if (!record || !record.activeFields || !(CHAMP in record.activeFields)) {
        return false;
    }
    return Boolean(record.data[CHAMP]);
}

patch(ProductLabelSectionAndNoteField.prototype, {
    setup() {
        super.setup();
        // L'article est choisi après le montage de la ligne : l'attente se
        // surveille, elle ne se lit pas une fois pour toutes.
        useEffect(
            () => {
                if (descriptionAttendue(this.props.record)) {
                    this.labelVisibility.value = true;
                }
            },
            () => [descriptionAttendue(this.props.record)]
        );
    },

    /** Le bouton de repli ne referme pas une description attendue. */
    switchLabelVisibility() {
        if (descriptionAttendue(this.props.record)) {
            this.labelVisibility.value = true;
            this.switchToLabel = true;
            return;
        }
        super.switchLabelVisibility();
    },
});
