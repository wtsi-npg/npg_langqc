<script setup>
    import { inject } from "vue";
    import LangQc from "../utils/langqc.js";
    import { useMessageStore } from "@/stores/message.js";
    import { useWellStore } from "@/stores/focusWell.js";

    const errorBuffer = useMessageStore();
    const focusWell = useWellStore();

    const emit = defineEmits(['wellClaimed']);

    const tabGetter = inject('activeTab');

    let client = new LangQc();

    function claimHandler() {
        const [runName, wellLabel] = focusWell.getRunAndLabel;
        if (! (runName && wellLabel) ) {
            throw new Error('Claim environment misconfigured, no run name or well label');
        }

        client.claimWell(runName, wellLabel)
        .then(
            response => { focusWell.updateWellQcState(response) }
        ).catch(
            (error) => {
                errorBuffer.addMessage(error);
            }
        );

        emit('wellClaimed');
    }
</script>

<template>
    <div id="ClaimButton">
        <el-button type="primary" @click="claimHandler" :disabled="tabGetter != 'inbox'">Claim for QC</el-button>
    </div>
</template>

<style>
</style>