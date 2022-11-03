<script setup>
    import { inject } from "vue";
    import LangQc from "../utils/langqc.js";
    import useMessageStore from "@/stores/message.js";

    const errorBuffer = useMessageStore();

    const changeQcState = inject('updateRunWellQcState');
    const runInfo = inject('getRunWell');

    let client = new LangQc();

    function claimHandler() {
        const [runName, wellLabel] = runInfo();
        try {
            let responseBody = client.claimWell(
                runName,
                wellLabel
            );
            console.log(responseBody);
            changeQcState(responseBody);
        } catch (error) {
            console.log(error);
            errorBuffer.addMessage(error);
        }
    }
</script>

<template>
    <div id="ClaimButton">
        <el-button type="primary" @click="claimHandler">Claim for QC</el-button>
    </div>
</template>

<style>
</style>