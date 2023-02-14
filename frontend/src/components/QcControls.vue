<script setup>
import { computed, defineProps, ref, watch } from "vue";
import ClaimWidget from "@/components/ClaimWidget.vue";
import QcWidget from "@/components/QcWidget.vue";
import { useWellStore } from "@/stores/focusWell.js";

const emit = defineEmits(['wellChanged']);
const focusWell = useWellStore();

const props = defineProps({
    assignee: String, // whomever has claimed this QC item
    user: String, // the user for this session
});

function changeTab() {
    emit('wellChanged', 'in_progress');
}

let override = ref(false);
function flipOverride() {
    console.log(override.value);
    override.value = !override.value;
    console.log(override.value);
}
watch(focusWell, override.value = false); // Turn override off if the well changes

const owner = computed(() => {
    if (props.assignee && props.user && props.assignee == props.user) {
        return true
    } else {
        return false
    }
});

const cannotClaim = computed(() => {
    return (!props.user || focusWell.hasQcState) ? true : null
});

const unModifiable = computed(() => {
    if (
        override.value == true
        || (owner && focusWell.hasQcState && !focusWell.getFinality)
    ) {
        return null
    } else {
        return true
    }
});

const canOverride = computed(() => {
    if (
        (override.value == false)
        && (
            (owner && focusWell.hasQcState && focusWell.getFinality)
            || (!owner && props.user)
        )
    ) {
        return true
    } else {
        return null
    }
});


</script>

<template>
    <div id="QCcontrols" class="widget-box">
        <el-card shadow="always">
            <ClaimWidget @wellClaimed="changeTab" :disabled="cannotClaim" />
            <QcWidget :disabled=unModifiable />
            <el-button v-if="canOverride" text type="warning" @click="flipOverride">Override</el-button>
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
