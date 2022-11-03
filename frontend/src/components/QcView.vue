<script setup>
    import { provide } from "vue";
    import groupMetrics from "../utils/metrics.js";
    import ClaimWidget from "@/components/ClaimWidget.vue";

    const props = defineProps({
        runWell: Object, // PacBioRunResult
    });

    const pacBioPort = "8243";

    function generateSmrtLink(metric) {
        return `https://${metric.smrt_link.hostname}:${pacBioPort}/sl/run-qc/${metric.smrt_link.run_uuid}`
    }

    function changeQcState(qcState) {
        // qcState is a QcState model
        props.runWell.qc_state = qcState;
        // this.$emit??????? mutating props is forbidden...
    }

    function getRunWell() {
        return [props.runWell.run_info.pac_bio_run_name, props.runWell.run_info.well_label];
    }

    provide('updateRunWellQcState', changeQcState);
    provide('getRunWell', getRunWell);
</script>

<template>
<div id="Top tier attributes of run">
    <table class="summary">
        <tr>
            <td>Run</td><td>{{runWell.run_info.pac_bio_run_name}}</td>
        </tr>
        <tr>
            <td>Well</td><td>{{runWell.run_info.well_label}}</td>
        </tr>
        <tr>
            <td>Library type</td><td>{{runWell.run_info.library_type}}</td>
        </tr>
        <tr>
            <td>Study</td><td>{{runWell.study.id}}</td>
        </tr>
        <tr>
            <td>Sample</td><td>{{runWell.sample.id}}</td>
        </tr>
        <tr>
            <td>Last updated</td><td>{{runWell.run_info.last_updated}}</td>
        </tr>
    </table>
</div>

<div id="QCcontrols">
    <ClaimWidget/>
</div>

<a :href="generateSmrtLink(runWell.metrics)">View in SMRT&reg; Link</a>

<div id="Metrics">
    <table>
        <tr>
            <th>QC property</th>
            <th>Value</th>
        </tr>
        <template :key="name" v-for="(sectionClass, name) in groupMetrics(runWell.metrics)">
            <template :key="niceName" v-for="[niceName, metric], dbName in sectionClass">
                <tr :class=name>
                    <td :title="dbName">{{niceName}}</td>
                    <td>{{metric}}</td>
                </tr>
            </template>
        </template>
    </table>
</div>
</template>

<style>
    table {
        border: 1px solid;
        border-radius: 5px;
    }
    th {
        font-weight: bold;
        background-color: #9292ff;
    }
    table.summary {
        border: 0px;
        font-weight: bold;
    }
    .MetricOrange {
        background-color: #F8CBAD;
    }
    .MetricBlue {
        background-color: #BDD6EE;
    }
    .MetricGreen {
        background-color: #C6E0B4;
    }
    .MetricYellow {
        background-color: #FFE698;
    }
</style>
