import { isNull } from 'lodash';
import { defineStore } from 'pinia';

export const useWellStore = defineStore('focusWell', {
    state: () => ({runWell: null}),
    getters: {
        getRunAndLabel(state) {
            if (! isNull(state.runWell)) {
                return [
                    state.runWell.run_info.pac_bio_run_name,
                    state.runWell.run_info.well_label
                ];
            } else {
                return [null, null]
            }
        },
        getQcState(state) {
            if (
                ! isNull(state.runWell)
                && 'qcState' in state.runWell
                && state.runWell.qcState != null
            ) {
                return state.runWell.qcState['state'];
            } else {
                return null;
            }
        }
    },
    actions: {
        updateWellQcState(qcState) {
            this.runWell.qcState = qcState;
        },
        setFocusWell(well) {
            this.runWell = well;
        }
    }
});
