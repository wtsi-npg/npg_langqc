<script setup>
import { onMounted, ref } from "vue";

import QcView from "@/components/QcView.vue";
import LangQc from "@/utils/langqc.js";

let serviceClient = null;
let runWell = ref(null);
let runCollection = ref(null);
let host = "https://dev-langqc.dnapipelines.sanger.ac.uk";
// Replace this with bootstrapping the data service URL
// from config or static content server

function loadWell(runName, label) {
  // Sets the runWell for the QcView component below
  serviceClient.getRunWellPromise(runName, label)
  .then(
    value => runWell.value = value
  );
}

onMounted(() => {
  serviceClient = new LangQc(host);
  try {
    serviceClient.getInboxPromise().then(
      data => runCollection.value = data
    );
  } catch (error) {
    console.log("Stuff went wrong getting data from backend: "+error);
  }
});

</script>

<template>
<div>
  <h2>Runs</h2>
</div>
<div>
  <table>
    <tr>
      <th>Run name</th>
      <th>Well label</th>
      <th>Time started</th>
      <th>Time completed</th>
    </tr>
    <tr :key="run.run_name" v-for="run in runCollection" >
      <td>{{ run.run_name }}</td>
      <td>
        <button :key="well.label" v-for="well in run.wells" v-on:click="loadWell(run.run_name, well.label)">{{ well.label }}</button>
      </td>
      <td>{{ run.time_start }}</td>
      <td>{{ run.time_complete ? run.time_complete : ''}}</td>
    </tr>
  </table>
</div>
<div v-if="runWell !== null">
  <h2>QC view</h2>
  <QcView :runWell="runWell"/>
</div>
<div v-else>QC data will appear here</div>
</template>
