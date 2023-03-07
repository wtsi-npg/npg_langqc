<script setup>
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
    const [runName, wellLabel] = focusWell.getRunAndLabel;
    if (!(runName && wellLabel)) {
        throw new Error('Claim environment misconfigured, no run name or well label');
    }

    client.claimWell(runName, wellLabel)
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