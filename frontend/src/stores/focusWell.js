import { isNull } from 'lodash';
import { defineStore } from 'pinia';

export const useWellStore = defineStore('focusWell', {
    state: () => ({
        runWell: null,
        qcState: null,
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
                && state.qcState != null
            ) {
                return state.qcState;
            } else {
                return null;
            }
        },
        getQcValue(state) {
            if (
                !isNull(state.runWell)
                && state.qcState != null
            ) {
                return state.qcState.qc_state;
            } else {
                return null;
            }
        },
        hasQcState(state) {
            if (state.qcState != null) {
                return true
            }
            return false;
        },
        getFinality(state) {
            if (state.qcState != null) {
                return !state.qcState.is_preliminary;
            }
            return null;
        },
        getAssessor(state) {
            if (state.qcState != null && state.qcState.user) {
                return state.qcState.user;
            }
        }
    },
    actions: {
        updateWellQcState(qcState) {
            this.qcState = qcState;
        },
        setFocusWell(well) {
            this.runWell = well;
        }
    }
});
