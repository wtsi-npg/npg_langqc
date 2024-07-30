<script setup>
    /*
    * An information view containing run data and metrics useful for QC assessment
    */

    import { computed, ref, watch } from "vue";
    import groupMetrics from "../utils/metrics.js";
    import { combineLabelWithPlate } from "../utils/text.js"
    import PoolStats from "./PoolStats.vue";
    import LangQc from "../utils/langqc";


    const dataClient = new LangQc()

    const props = defineProps({
        // Well object representing one prepared input for the instrument
        // Expects content in the form of lang_qc/models/pacbio/well.py:PacBioWellFull
        well: Object,
    })

    const slURL = computed(() => {
        let hostname = props.well.metrics.smrt_link.hostname
        let url = ''
        if (hostname) {
            url = `https://${hostname}:${import.meta.env.VITE_SMRTLINK_PORT}/sl`
        }
        return url
    })

    const slRunLink = computed(() => {
        let url = ''
        let run_uuid = props.well.metrics.smrt_link.run_uuid
        if (slURL.value && run_uuid) {
            url = [slURL.value, 'run-qc', run_uuid].join("/")
        }
        return url
    })

    const slDatasetLink = computed(() => {
        let url = ''
        let dataset_uuid = props.well.metrics.smrt_link.dataset_uuid
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
        if (props.well.experiment_tracking) {
            let study_id = props.well.experiment_tracking.study_id
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
        if (props.well.experiment_tracking) {
            return props.well.experiment_tracking.study_id.join(", ")
        }
        return ''
    })

    const ssLimsSampleLink = computed(() => {
        let url = ''
        if (props.well.experiment_tracking &&
            props.well.experiment_tracking.num_samples == 1) {
            url = [import.meta.env.VITE_LIMS_SS_SERVER_URL,
                   'samples',
                   props.well.experiment_tracking.sample_id].join("/")
        }
        return url
    })

    const ssLimsNumSamples = computed(() => {
        if (props.well.experiment_tracking) {
            return props.well.experiment_tracking.num_samples
        }
        return 0
    })

    const ssLimsLibraryTypes = computed(() => {
        if (props.well.experiment_tracking) {
            return props.well.experiment_tracking.library_type.join(", ")
        }
        return ''
    })

    const poolName = computed(() => {
        if (props.well.experiment_tracking && props.well.experiment_tracking.pool_name) {
            return props.well.experiment_tracking.pool_name
        }
        return ''
    })

    const poolStats = ref(null)
    watch(() => props.well, () => {
        poolStats.value = null // empty in case next well doesn't have a pool
        if (ssLimsNumSamples.value > 0) {
            dataClient.getPoolMetrics(props.well.id_product).then(
                (response) => { poolStats.value = response }
            ).catch((error) => {
                if (error.message.match("Conflict")) {
                    // Nothing to do
                } else {
                    console.log(error)
                    // make a banner show this error?
                }
            })
        }
    }, { immediate: true }
    )
</script>

<template>
    <div id="well_summary">
        <table class="summary">
            <tr>
                <td>Run</td>
                <td v-if="slRunLink">
                    <el-link :href="slRunLink" :underline="false" icon="ExtLink" target="_blank">
                        {{ well.run_name }}
                    </el-link>
                </td>
                <td v-else>{{ well.run_name }}</td>
            </tr>
            <tr>
                <td>Well label</td>
                <td v-if="slDatasetLink">
                    <el-link :href="slDatasetLink" :underline="false" icon="ExtLink" target="_blank">
                        {{ combineLabelWithPlate(well.label, well.plate_number) }}
                    </el-link>
                </td>
                <td v-else>{{ combineLabelWithPlate(well.label, well.plate_number) }}</td>
            </tr>
            <tr>
                <td>Instrument</td>
                <td>{{ well.instrument_type }} {{ well.instrument_name }}</td>
            </tr>
            <tr>
                <td>Well complete</td>
                <td v-if="well.well_complete_time">
                    {{(new Date(well.well_complete_time)).toLocaleString()}}
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
                        {{ well.experiment_tracking.study_name }}
                    </el-link>
                </td>
                <td v-else-if="ssLimsStudyIds">Multiple studies: {{ssLimsStudyIds}}</td>
                <td v-else>No study information</td>
            </tr>
            <tr>
                <td>Sample</td>
                <td v-if="ssLimsSampleLink">
                    <el-link :href="ssLimsSampleLink" :underline="false" icon="ExtLink" target="_blank">
                        {{well.experiment_tracking.sample_name}}
                    </el-link>
                </td>
                <td v-else-if="ssLimsNumSamples">Multiple samples ({{ssLimsNumSamples}})</td>
                <!-- TODO: Display a link to the LIMS server web page for a pool here? -->
                <td v-else>No sample information</td>
            </tr>
            <tr>
                <td>Pool name</td>
                <td>{{ poolName }}</td>
            </tr>
        </table>
    </div>

    <PoolStats v-if="poolStats" :pool="poolStats">Pool composition</PoolStats>

    <div id="Metrics">
        <table>
            <tr>
                <th>Property</th>
                <th>Value</th>
            </tr>
            <template :key="name" v-for="(sectionClass, name) in groupMetrics(well.metrics)">
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
        align-self: flex-start;
    }
    tr>td:first-child {
        vertical-align: top;
        /* Pin first text element to the top of the td */
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
