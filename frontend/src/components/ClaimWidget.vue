<script setup>
/*
* A button for assigning QC responsibility to the logged-in user
*/

import { computed } from "vue";
import { ElMessage } from "element-plus";
import LangQc from "../utils/langqc.js";
import { useWellStore } from "@/stores/focusWell.js";

const focusWell = useWellStore();

const emit = defineEmits(['wellClaimed']);
const props = defineProps({
    disabled: Boolean
});

let client = new LangQc();

function claimHandler() {
    const id = focusWell.getIdProduct;
    if (!id) {
        throw new Error('Claim environment misconfigured, needs an id_product');
    }

    client.claimWell(id)
        .then(
            (response) => {
                focusWell.updateWellQcState(response);
                ElMessage({
                    message: 'Claimed',
                    type: 'success',
                    duration: 2000
                });
                emit('wellClaimed');
            }
        ).catch(
            (error) => {
                ElMessage({
                    message: error
                })
            }
        );
}

let amIDisabled = computed(() => {
    if (props.disabled == true) {
        return true
    } else {
        return null // because Vue3 renders false as attr="false"
    }
})
</script>

<template>
    <div id="ClaimButton">
        <el-button type="primary" @click="claimHandler" :disabled="amIDisabled">Claim for QC</el-button>
    </div>
</template>

<style>

</style>