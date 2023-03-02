import { isNull } from 'lodash';
import { defineStore } from 'pinia';

export const useWellStore = defineStore('focusWell', {
    state: () => ({
        runWell: null,
        /* Example state doc: {
            "qc_state": "Claimed",
            "is_preliminary": true,
            "qc_type": "sequencing",
            "outcome": null,
            "id_product": "3fc2b80d84bcec1f526a9bcff7c54b40227d6724d5a5dacc1e530a5e27ebacff",
            "date_created": "2022-11-17T14:56:52",
            "date_updated": "2022-11-17T14:56:52",
            "user": "dog@doggy.www.rrr.com",
            "created_by": "LangQC"
        } */
    }),
    getters: {
        getRunAndLabel(state) {
            if (!isNull(state.runWell)) {
                return [
                    state.runWell.run_name,
                    state.runWell.label
                ];
            } else {
                return [null, null]
            }
        },
        getQcState(state) {
            if (
                !isNull(state.runWell)
                && state.runWell.qc_state != null
            ) {
                return state.runWell.qc_state;
            } else {
                return null;
            }
        },
        getQcValue(state) {
            if (
                !isNull(state.runWell)
                && state.runWell.qc_state != null
            ) {
                return state.runWell.qc_state.qc_state;
            } else {
                return null;
            }
        },
        hasQcState(state) {
            if (state.runWell.qc_state != null) {
                return true
            }
            return false;
        },
        getFinality(state) {
            if (state.runWell && state.runWell.qc_state != null) {
                return !state.runWell.qc_state.is_preliminary;
            }
            return false;
        },
        getAssessor(state) {
            if (state.runWell.qc_state != null && state.runWell.qc_state.user) {
                return state.runWell.qc_state.user;
            }
            return null;
        }
    },
    actions: {
        updateWellQcState(qcState) {
            this.runWell.qc_state = qcState;
        },
        setFocusWell(well) {
            this.runWell = well;
        }
    }
});
