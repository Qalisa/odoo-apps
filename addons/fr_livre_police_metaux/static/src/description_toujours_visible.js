/**
 * La zone de description reste ouverte sur les articles qui l'exigent.
 *
 * Odoo replie cette zone sous la désignation de l'article : il faut cliquer
 * l'icône, ou frapper Entrée, pour la faire apparaître. Un opérateur qui ne
 * connaît pas le geste ne voit rien à remplir — et découvre l'obligation au
 * refus de la confirmation.
 *
 * Le pli n'est donc défait que là où la description est obligatoire. Ailleurs,
 * la saisie d'une vente garde le comportement standard.
 */

import { patch } from "@web/core/utils/patch";
import { useEffect } from "@odoo/owl";
import {
    ProductLabelSectionAndNoteField,
} from "@account/components/product_label_section_and_note_field/product_label_section_and_note_field";

patch(ProductLabelSectionAndNoteField.prototype, {
    setup() {
        super.setup();
        // L'exigence dépend de l'article, choisi après le montage de la ligne :
        // elle se surveille, elle ne se lit pas une fois pour toutes.
        useEffect(
            () => {
                if (this.props.record.data.police_description_required) {
                    this.labelVisibility.value = true;
                }
            },
            () => [this.props.record.data.police_description_required]
        );
    },

    /** Le bouton de repli ne referme pas une description obligatoire. */
    switchLabelVisibility() {
        if (this.props.record.data.police_description_required) {
            this.labelVisibility.value = true;
            this.switchToLabel = true;
            return;
        }
        super.switchLabelVisibility();
    },
});
