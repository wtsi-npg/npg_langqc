<script setup>
import { inject, ref, computed, watch, onMounted } from "vue";
import LangQc from "../utils/langqc.js";
import { useMessageStore } from '@/stores/message.js';
import { useWellStore } from '@/stores/focusWell.js';

const appConfig = inject('config');
const activeWell = inject('activeWell');
const errorBuffer = useMessageStore();
const focusWell = useWellStore();

let client = new LangQc();

// The state at time of last QC update
let qcSetting = ref(null);
let finality = ref(false);
let user = ref(null);

// Vars representing the current state of the form until submission
// updates the focusWell store and the backend API
let widgetQcSetting = ref(null);
let widgetFinality = ref(false);

// When the selected QC view changes, we need to reset this component
// to whatever is now in focusWell
watch(activeWell, () => {
    syncLastQcState();
    syncWidgetToQcState();
});

onMounted(() => {
    syncLastQcState();
    syncWidgetToQcState();
});

// Nicer than using onMounted() trigger?
const options = computed(() => {
    let opts = [];
    for (const setting of appConfig.value.qc_states) {
        opts.push({
            'value': setting.description,
            'label': setting.description
        });
    }
    return opts;
});

function syncWidgetToQcState() {
    if (focusWell.hasQcState) {
        widgetQcSetting.value = focusWell.getQcValue;
        widgetFinality.value = focusWell.getFinality;
    }
}

function syncLastQcState() {
    if (focusWell.hasQcState) {
        qcSetting.value = focusWell.getQcValue;
        finality.value = focusWell.getFinality;
        user.value = focusWell.getQcState.user;
    }
}

function submitQcState() {
    let [ name, well ] = focusWell.getRunAndLabel;

    client.setWellQcState(name, well, widgetQcSetting.value, widgetFinality.value)
    .then(
        (response) => {
            focusWell.updateWellQcState(response);
            // Set new "old" settings for the widgets
            syncLastQcState();
            syncWidgetToQcState();
        }
    ).catch(
        (error) => errorBuffer.addMessage(error.message)
    )
}
</script>

<template>
    <div :data-testId="'previousSetting'"
        v-if="focusWell.hasQcState">
        Current QC state: {{finality ? "Final": "Preliminary"}} "{{qcSetting}}" set by "{{user}}"
    </div>
    <div :data-testId="'notHere'" v-else>No QC setting</div>
    <div>
        <el-select
            v-model="widgetQcSetting"
            :placeholder="widgetQcSetting"
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
            v-model="widgetFinality"
            active-text="Final"
            inactive-text="Preliminary"
            size="large"
            style="--el-switch-off-color: #131313"
            :data-testId="'QC finality selector'"
            :disabled="qcSetting ? false : true"
        />
        <el-button
            type="primary"
            @click="submitQcState"
            :data-testId="'QC submit'"
            :disabled="qcSetting ? false : true"
        >Submit</el-button>
    </div>
</template>

<style>
</style>