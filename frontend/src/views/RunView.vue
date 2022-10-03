<script setup>
import { onMounted, ref } from "vue";

import QcView from "@/components/QcView.vue";
import LangQc from "@/utils/langqc.js";

let serviceClient = null;
let runWell = ref(null);
let wellCollection = ref(null);
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
      data => wellCollection.value = data
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
    <tr v-for="wellObj in wellCollection" >
      <td>{{ wellObj.run_name }}</td>
      <td>
        <button v-on:click="loadWell(wellObj.run_name, wellObj.well.label)">{{ wellObj.well.label }}</button>
      </td>
      <td>{{ wellObj.time_start }}</td>
      <td>{{ wellObj.time_complete ? wellObj.time_complete : ''}}</td>
    </tr>
  </table>
</div>
<div v-if="runWell !== null">
  <h2>QC view</h2>
  <QcView :runWell="runWell"/>
</div>
<div v-else>QC data will appear here</div>
</template>
