<script setup>
    const props = defineProps({
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
            <td>Run</td><td>{{runWell.run_info.pac_bio_run_name}}</td>
        </tr>
        <tr>
            <td>Well</td><td>{{runWell.run_info.well.label}}</td>
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

<a :href="generateSmrtLink(runWell.metrics)">View in SMRT&reg; Link</a>

<div id="Metrics">
    <table>
        <tr>
            <th>QC property</th>
            <th>Value</th>
        </tr>
        <template v-for="(metric, key) in runWell.metrics">
            <tr v-if="key != 'smrt_link'">
                <td>{{metric.label}}</td>
                <td>{{metric.value}}</td>
            </tr>
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
</style>
