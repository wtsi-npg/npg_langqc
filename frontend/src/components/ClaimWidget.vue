<script setup>
    import LangQc from "../utils/langqc.js";
    import useMessageStore from "@/stores/message.js";
    import useWellStore from "@/stores/focusWell.js";

    const errorBuffer = useMessageStore();
    const focusWell = useWellStore();

    let client = new LangQc();

    function claimHandler() {
        const [runName, wellLabel] = focusWell.getRunAndLabel;

        client.claimWell(runName, wellLabel)
        .then(
            response => { focusWell.updateWellQcState(response) }
        ).catch(
            (error) => {
                console.log(error);
                errorBuffer.addMessage(error);
            }
        );
    }
</script>

<template>
    <div id="ClaimButton">
        <el-button type="primary" @click="claimHandler">Claim for QC</el-button>
    </div>
</template>

<style>
</style>