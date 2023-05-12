<script setup>

    import { computed } from "vue";
    import groupMetrics from "../utils/metrics.js";

    const props = defineProps({
        runWell: Object, // PacBioRunResult
    });

    const slURL = computed(() => {
        let hostname = props.runWell.metrics.smrt_link.hostname
        return `https://${hostname}:${import.meta.env.VITE_SMRTLINK_PORT}/sl`
    })

    const slRunLink = computed(() => {
        return [slURL.value,
                'run-qc',
                props.runWell.metrics.smrt_link.run_uuid].join("/")
    })

    const ssLimsStudyLink = computed(() => {
        return [import.meta.env.VITE_LIMS_SS_SERVER_URL,
                'studies',
                props.runWell.experiment_tracking.study_id[0],
                'properties'].join("/")
    })

    const ssLimsSampleLink = computed(() => {
        return [import.meta.env.VITE_LIMS_SS_SERVER_URL,
                'samples',
                props.runWell.experiment_tracking.sample_id].join("/")
    })

</script>

<template>
    <div id="well_summary">
        <table class="summary">
            <tr>
                <td>Run</td>
                <td v-if="runWell.metrics.smrt_link.hostname">
                    <el-link :href="slRunLink" :underline="false" icon="ExtLink" target="_blank">
                        {{ runWell.run_name }}
                    </el-link>
                </td>
                <td v-else>{{ runWell.run_name }}</td>
            </tr>
            <tr>
                <td>Well</td><td>{{runWell.label}}</td>
            </tr>
            <tr v-if="runWell.well_complete_time">
                <td>Well complete</td><td>{{(new Date(runWell.well_complete_time)).toLocaleString()}}</td>
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
                        :href="ssLimsStudyLink"
                        :underline="false"
                        icon="ExtLink"
                        target="_blank">
                        {{ runWell.experiment_tracking.study_name }}
                    </el-link>
                </td>
                <td v-else>Multiple studies: {{runWell.experiment_tracking.study_id.join(", ")}}</td>
            </tr>
            <tr v-if="runWell.experiment_tracking">
                <td>Sample</td>
                <td v-if="runWell.experiment_tracking.num_samples == 1">
                    <el-link
                        :href="ssLimsSampleLink"
                        :underline="false"
                        icon="ExtLink"
                        target="_blank">
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
                <th>Property</th>
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
        text-align: center;
        background-color: #92b0bd;
        padding: 5px;
    }
    td {
        padding-left: 5px;
        padding-right: 5px;
    }
    table.summary {
        border: 0px;
    }
    .well_selector {
        text-align: center;
        margin: auto;
    }
    #well_summary {
        margin-bottom: 20px;
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
