<script setup>
import { inject, onMounted, ref } from "vue";
import LangQc from "../utils/langqc.js";
import { useMessageStore } from '@/stores/message.js';
import { useWellStore } from '@/stores/focusWell.js';

const appConfig = inject('config');
const errorBuffer = useMessageStore();
const focusWell = useWellStore();

let client = new LangQc();
let qcSetting = ref(null);
let finality = ref(false);
let options = [];

onMounted( () => {
    for (const setting of appConfig.value.qc_states) {
        options.push({
            'value': setting.description,
            'label': setting.description
        });
    }
    if (focusWell.hasQcState) {
        qcSetting.value = focusWell.getQcValue;
        finality.value = focusWell.getQcState.is_preliminary;
    }
});

function submitQcState() {
    let [ name, well ] = focusWell.getRunAndLabel;

    client.setWellQcState(name, well, qcSetting.value, finality.value)
    .then(
        response => focusWell.updateWellQcState(response)
    ).catch(
        (error) => errorBuffer.addMessage(error.message)
    )
}
</script>

<template>
    <div :data-testId="'previousSetting'"
        v-if="focusWell.hasQcState">
        Current QC state: {{focusWell.getQcState.is_preliminary ? "Preliminary":"Final"}} "{{focusWell.getQcValue}}" set by "{{focusWell.getQcState.user}}"
    </div>
    <div :data-testId="'notHere'" v-else>No QC setting</div>
    <div>
        <el-select
            v-model="qcSetting"
            :placeholder="focusWell.getQcValue"
            :disabled="qcSetting ? false : true"
            :data-testId="'QC state selector'"
        >
            <el-option
                v-for="item in options"
                :key="item.value"
                :label="item.label"
                :value="item.value"
            />
        </el-select>
        <el-switch
            v-model="finality"
            active-text="Final"
            inactive-text="Preliminary"
            size="large"
            style="--el-switch-off-color: #131313"
            :data-testId="'QC finality selector'"
        />
        <el-button type="primary" @click="submitQcState" :data-testId="'QC submit'">Submit</el-button>
    </div>
</template>

<style>
</style>