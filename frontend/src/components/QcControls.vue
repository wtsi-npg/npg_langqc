<script setup>
    import ClaimWidget from "@/components/ClaimWidget.vue";

    const emit = defineEmits(['wellChanged']);

    function changeTab() {
        emit('wellChanged', 'in_progress');
    }
</script>

<template>
    <div id="QCcontrols">
        <ClaimWidget @wellClaimed="changeTab"/>
    </div>
</template>

<style>
</style>
