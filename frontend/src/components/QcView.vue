<script setup>
    import { defineProps } from "vue";
    import groupMetrics from "../utils/metrics.js";

    defineProps({
        runWell: Object, // PacBioRunResult
    });

    function generateSmrtLink(metric) {
        return `https://${metric.smrt_link.hostname}:${import.meta.env.VITE_SMRTLINK_PORT}/sl/run-qc/${metric.smrt_link.run_uuid}`
    }

    function generateSequencescapeLink(id, isSampleId) {
        let url_components = [import.meta.env.VITE_LIMS_SS_SERVER_URL];
        url_components.push(isSampleId == true ? "samples" : "studies");
        url_components.push(id);
        if (isSampleId == false) {
            url_components.push("properties");
        }
        return url_components.join("/");
    }
</script>

<template>
    <div id="Top tier attributes of run">
        <table class="summary">
            <tr>
                <td>Run</td>
                <td v-if="runWell.metrics.smrt_link.hostname">
                    <el-link :href="generateSmrtLink(runWell.metrics)" :underline="false" icon="Link">
                        {{ runWell.run_name }}
                    </el-link>
                </td>
                <td v-else>{{ runWell.run_name }}</td>
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
                <td v-if="runWell.experiment_tracking.study_id.length == 1">
                    <el-link
                        :href="generateSequencescapeLink(runWell.experiment_tracking.study_id[0], false)"
                        :underline="false"
                        icon="Link">
                        {{ runWell.experiment_tracking.study_name }}
                    </el-link>
                </td>
                <td v-else>Multiple studies: {{runWell.experiment_tracking.study_id.join(", ")}}</td>
            </tr>
            <tr v-if="runWell.experiment_tracking">
                <td>Sample</td>
                <td v-if="runWell.experiment_tracking.num_samples == 1">
                    <el-link
                        :href="generateSequencescapeLink(runWell.experiment_tracking.sample_id, true)"
                        :underline="false"
                        icon="Link">
                        {{runWell.experiment_tracking.sample_name}}
                    </el-link>
                </td>
                <!-- TODO: Display a link to the LIMS server web page for a pool here? -->
                <td v-else>Multiple samples ({{runWell.experiment_tracking.num_samples}})</td>
            </tr>
            <!-- Tag sequence info can be displayed below when the tag deplexing info is available -->
        </table>
    </div>

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
