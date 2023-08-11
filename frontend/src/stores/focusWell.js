import { isNull } from 'lodash';
import { defineStore } from 'pinia';

import LangQc from '../utils/langqc';
import { ElMessage } from 'element-plus';

const apiClient = new LangQc;

export const useWellStore = defineStore('focusWell', {
    state: () => ({
        well: null,
        /* Example state doc:
        run_name: "TRACTION-RUN-nnn",
        label: "A1",
        qc_state: {
            "qc_state": "Claimed",
            "is_preliminary": true,
            "qc_type": "sequencing",
            "outcome": null,
            "id_product": "3fc2b80d84bcec1f526a9bcff7c54b40227d6724d5a5dacc1e530a5e27ebacff",
            "date_created": "2022-11-17T14:56:52",
            "date_updated": "2022-11-17T14:56:52",
            "user": "dog@doggy.www.rrr.com",
            "created_by": "LangQC"
        },
        metrics: {},
        experiment_tracking: {}
        */
    }),
    getters: {
        getIdProduct(state) {
            if (state.well && !isNull(state.well.id_product)) {
                return state.well.id_product
            } else {
                return null
            }
        },
        getQcState(state) {
            if (
                !isNull(state.well)
                && state.well.qc_state != null
            ) {
                return state.well.qc_state;
            } else {
                return null;
            }
        },
        getQcValue() {
            let qcState = this.getQcState;
            return qcState != null ? qcState.qc_state : null;
        },
        hasQcState() {
            return this.getQcState == null ? false : true;
        },
        getFinality() {
            let qcState = this.getQcState;
            return qcState != null ? !qcState.is_preliminary : false;
        },
        getAssessor() {
            let qcState = this.getQcState;
            return (qcState != null && qcState.user) ? qcState.user : null;
        }
    },
    actions: {
        updateWellQcState(qcState) {
            this.well.qc_state = qcState;
        },
        setFocusWell(well) {
            this.well = well;
        },
        loadWellDetail(id_product) {
            apiClient.getWellPromise(id_product).then(
                (well) => this.well = well
            ).catch(
                (error) => {
                    ElMessage({
                        message: error.message,
                        type: error,
                        duration: 5000
                    })
                }
            )
        },
    }
});
