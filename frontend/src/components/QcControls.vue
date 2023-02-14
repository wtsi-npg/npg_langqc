<script setup>
import { computed, defineProps, ref } from "vue";
import ClaimWidget from "@/components/ClaimWidget.vue";
import QcWidget from "@/components/QcWidget.vue";

const emit = defineEmits(['wellChanged']);

const props = defineProps({
    assignee: String, // whomever has claimed this QC item
    user: String, // the user for this session
    state: Object // The state of the selected well, so we can decide which buttons to enable
});

function changeTab() {
    emit('wellChanged', 'in_progress');
}

let override = ref(false)

let owner = computed(() => {
    if (props.assignee && props.user && props.assignee == props.user) {
        return true
    } else {
        return false
    }
})

let cannotClaim = computed(() => {
    return !props.user || Boolean(props.state)
});

let modifiable = computed(() => {
    if (override || (owner && props.state && props.state.is_preliminary === true)) {
        return true
    } else {
        return false
    }
})

let canOverride = computed(() => {
    if ((owner && props.state && !props.state.is_preliminary) || !owner && props.user) {
        return true
    } else {
        return false
    }
})


</script>

<template>
    <div id="QCcontrols" class="widget-box">
        <el-card shadow="always">
            <ClaimWidget @wellClaimed="changeTab" :disabled="cannotClaim" />
            <QcWidget :disabled="!modifiable" />
            <el-button v-if="canOverride" text type="warning" :onclick="override = !override">Override</el-button>
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
