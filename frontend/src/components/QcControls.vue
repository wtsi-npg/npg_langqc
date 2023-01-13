<script setup>
    import ClaimWidget from "@/components/ClaimWidget.vue";
    import QcWidget from "@/components/QcWidget.vue";

    const emit = defineEmits(['wellChanged']);

    function changeTab() {
        emit('wellChanged', 'in_progress');
    }
</script>

<template>
    <div id="QCcontrols" class="widget-box">
        <el-card shadow="always" >
            <ClaimWidget @wellClaimed="changeTab"/>
            <QcWidget />
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
