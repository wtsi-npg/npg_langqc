<script setup>
    import ClaimWidget from "@/components/ClaimWidget.vue";
    import QcWidget from "@/components/QcWidget.vue";

    const emit = defineEmits(['wellChanged']);

    function changeTab() {
        emit('wellChanged', 'in_progress');
    }
</script>

<template>
    <div id="QCcontrols">
        <ClaimWidget @wellClaimed="changeTab"/>
        <QcWidget />
    </div>
</template>

<style>
</style>
