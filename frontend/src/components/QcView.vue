<script setup>
    import { defineProps } from "vue";
    import groupMetrics from "../utils/metrics.js";

    defineProps({
        runWell: Object, // PacBioRunResult
    });

    const pacBioPort = "8243";

    function generateSmrtLink(metric) {
        return `https://${metric.smrt_link.hostname}:${pacBioPort}/sl/run-qc/${metric.smrt_link.run_uuid}`
    }
</script>    
    
<template>
    <div id="Top tier attributes of run">
        <table class="summary">
            <tr>
                <td>Run</td><td>{{runWell.run_name}}</td>
            </tr>
            <tr>
                <td>Well</td><td>{{runWell.label}}</td>
            </tr>
            <tr v-if="runWell.well_complete_time">
                <td>Well complete</td><td>{{runWell.well_complete_time.replace('T',' ')}}</td>
            </tr>
            <tr v-if="runWell.experiment_tracking">
                <td>Library type</td>
                <td v-if="runWell.experiment_tracking.library_type.length == 1">{{runWell.experiment_tracking.library_type[0]}}</td>
                <td v-else>Multiple library types: {{runWell.experiment_tracking.library_type.join(", ")}}</td>
            </tr>
            <tr v-if="runWell.experiment_tracking">
                <td>Study</td>
                <!-- TODO: Use study IDs to convert text to link(s) to the LIMS server web pages for the study -->
                <td v-if="runWell.experiment_tracking.study_id.length == 1">{{runWell.experiment_tracking.study_name}}</td>
                <td v-else>Multiple studies: {{runWell.experiment_tracking.study_id.join(", ")}}</td>
            </tr>
            <tr v-if="runWell.experiment_tracking">
                <td>Sample</td>
                <!-- TODO: Use sample ID to convert text to a link to the LIMS server web page for this sample -->
                <td v-if="runWell.experiment_tracking.num_samples == 1">{{runWell.experiment_tracking.sample_name}}</td>
                <!-- TODO: Display a link to the LIMS server web page for a pool here? -->
                <td v-else>Multiple samples ({{runWell.experiment_tracking.num_samples}})</td>
            </tr>
            <!-- Tag sequence info can be displayed below when the tag  deplexing info is available -->
        </table>
    </div>

    <p v-if="runWell.metrics.smrt_link.hostname">
        <a :href="generateSmrtLink(runWell.metrics)">View in SMRT&reg; Link</a>
    </p>
    <p v-else>No link to SMRT&reg; Link possible</p>

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
