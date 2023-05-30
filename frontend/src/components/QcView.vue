<script setup>
    import { computed } from "vue";
    import groupMetrics from "../utils/metrics.js";

    const props = defineProps({
        runWell: Object, // PacBioRunResult
    });

    const slURL = computed(() => {
        let hostname = props.runWell.metrics.smrt_link.hostname
        let url = ''
        if (hostname) {
            url = `https://${hostname}:${import.meta.env.VITE_SMRTLINK_PORT}/sl`
        }
        return url
    })

    const slRunLink = computed(() => {
        let url = ''
        let run_uuid = props.runWell.metrics.smrt_link.run_uuid
        if (slURL.value && run_uuid) {
            url = [slURL.value, 'run-qc', run_uuid].join("/")
        }
        return url
    })

    const slDatasetLink = computed(() => {
        let url = ''
        let dataset_uuid = props.runWell.metrics.smrt_link.dataset_uuid
        if (slURL.value && dataset_uuid) {
            url = [
                slURL.value,
                'data-management',
                'dataset-detail',
                dataset_uuid
            ].join("/") + '?type=ccsreads&show=analyses'
        }
        return url
    })

    const ssLimsStudyLink = computed(() => {
        let url = ''
        if (props.runWell.experiment_tracking) {
            let study_id = props.runWell.experiment_tracking.study_id
            if (study_id.length == 1) {
                url = [import.meta.env.VITE_LIMS_SS_SERVER_URL,
                       'studies',
                       study_id[0],
                       'properties'].join("/")
            }
        }
        return url
    })

    const ssLimsStudyIds = computed(() => {
        if (props.runWell.experiment_tracking) {
            return props.runWell.experiment_tracking.study_id.join(", ")
        } 
        return ''
    })

    const ssLimsSampleLink = computed(() => {
        let url = ''
        if (props.runWell.experiment_tracking &&
            props.runWell.experiment_tracking.num_samples == 1) {
            url = [import.meta.env.VITE_LIMS_SS_SERVER_URL,
                   'samples',
                   props.runWell.experiment_tracking.sample_id].join("/")
        }
        return url
    })

    const ssLimsNumSamples = computed(() => {
        if (props.runWell.experiment_tracking) {
            return props.runWell.experiment_tracking.num_samples
        }
        return 0
    })

    const ssLimsLibraryTypes = computed(() => {
        if (props.runWell.experiment_tracking) {
            return props.runWell.experiment_tracking.library_type.join(", ")
        }
        return ''
    })

</script>

<template>
    <div id="well_summary">
        <table class="summary">
            <tr>
                <td>Run</td>
                <td v-if="slRunLink">
                    <el-link :href="slRunLink" :underline="false" icon="ExtLink" target="_blank">
                        {{ runWell.run_name }}
                    </el-link>
                </td>
                <td v-else>{{ runWell.run_name }}</td>
            </tr>
            <tr>
                <td>Well</td>
                <td v-if="slDatasetLink">
                    <el-link :href="slDatasetLink" :underline="false" icon="ExtLink" target="_blank">
                        {{ runWell.label }}
                    </el-link>
                </td>
                <td v-else>{{ runWell.label }}</td>
            </tr>
            <tr>
                <td>Well complete</td>
                <td v-if="runWell.well_complete_time">
                    {{(new Date(runWell.well_complete_time)).toLocaleString()}}
                </td>
                <td v-else>No well completion timestamp</td>
            </tr>
            <tr>
                <td>Library type</td>
                <td v-if="ssLimsLibraryTypes">{{ssLimsLibraryTypes}}</td>
                <td v-else>No library type information</td>
            </tr>
            <tr>
                <td>Study</td>
                <td v-if="ssLimsStudyLink">
                    <el-link :href="ssLimsStudyLink" :underline="false" icon="ExtLink" target="_blank">
                        {{ runWell.experiment_tracking.study_name }}
                    </el-link>
                </td>
                <td v-else-if="ssLimsStudyIds">Multiple studies: {{ssLimsStudyIds}}</td>
                <td v-else>No study information</td>
            </tr>
            <tr>
                <td>Sample</td>
                <td v-if="ssLimsSampleLink">
                    <el-link :href="ssLimsSampleLink" :underline="false" icon="ExtLink" target="_blank">
                        {{runWell.experiment_tracking.sample_name}}
                    </el-link>
                </td>
                <td v-else-if="ssLimsNumSamples">Multiple samples ({{ssLimsNumSamples}})</td>
                <!-- TODO: Display a link to the LIMS server web page for a pool here? -->
                <td v-else>No sample information</td>
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
