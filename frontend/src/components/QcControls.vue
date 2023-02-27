<script setup>
import { computed, defineProps, ref, watch } from "vue";
import ClaimWidget from "@/components/ClaimWidget.vue";
import QcWidget from "@/components/QcWidget.vue";
import { useWellStore } from "@/stores/focusWell.js";

const emit = defineEmits(['wellChanged']);
const focusWell = useWellStore();

const props = defineProps({
    user: String, // the user for this session
});

function changeTab() {
    emit('wellChanged', 'in_progress');
}

let override = ref(false); // Override interface restrictions on modifying QC states
function flipOverride() {
    override.value = !override.value;
}
watch(focusWell, () => { override.value = false }); // Turn override off if the well changes

const isQcOwner = computed(() => {
    if (focusWell.getAssessor && props.user && focusWell.getAssessor == props.user) {
        return true
    } else {
        return false
    }
});

const cannotClaim = computed(() => {
    // Is null rather than false to prevent the disabled attribute appearing in rendered HTML
    return (!props.user || focusWell.hasQcState) ? true : null
});

const unModifiable = computed(() => {
    if (
        override.value === true
        || (isQcOwner.value === true && !focusWell.getFinality)
    ) {
        return null
    } else {
        return true
    }
});

const canOverride = computed(() => {
    if (
        override.value === false && props.user && focusWell.hasQcState
        && (
            (isQcOwner.value === true && focusWell.getFinality)
            || (isQcOwner.value === false)
        )
    ) {
        return true
    } else {
        return false
    }
});
</script>

<template>
    <div id="QCcontrols" class="widget-box">
        <el-card shadow="always">
            <ClaimWidget @wellClaimed="changeTab" :disabled="cannotClaim" />
            <QcWidget :componentDisabled=unModifiable />
            <el-button id="override" v-if="canOverride" text type="warning" @click="flipOverride">Override</el-button>
        </el-card>
    </div>
</template>

<style>
.widget-box {
    width: max-content;
    position: sticky;
    top: 0;
}
</style>
