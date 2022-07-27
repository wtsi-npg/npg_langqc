<script setup>
import { onMounted, ref } from "vue";

import QcView from "@/components/QcView.vue";
import LangQc from "@/utils/langqc.js";

let serviceClient = null;
let runWell = ref(null);
let runCollection = null;
let host = "https://dev-langqc.dnapipelines.sanger.ac.uk";
// Replace this with bootstrapping the data service URL
// from config or static content server

onMounted(() => {
  serviceClient = new LangQc(host);
  try {
    serviceClient.getInboxPromise().then(
      data => runCollection = data
    ).then(
      () => {
        serviceClient.getRunWellPromise(
          runCollection[0].run_name,
          runCollection[0].wells[0].label
        ).then(
          value => runWell.value = value
        );
      }
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
  Some content
</div>
<div v-if="runWell !== null">
  <h2>QC view</h2>
  <QcView :runWell="runWell"/>
</div>
<div v-else>QC data will appear here</div>
</template>