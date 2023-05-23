<script setup>
import { onMounted, watch, ref, provide } from "vue"
import { ElMessage } from "element-plus"
import { useRoute, useRouter } from "vue-router"

import LangQc from "@/utils/langqc"
import WellTable from "@/components/WellTable.vue"
import QcView from "@/components/QcView.vue"
import QcControls from "@/components/QcControls.vue"

import { generateUrl, qcQueryChanged } from "@/utils/url"
import { useWellStore } from "@/stores/focusWell";
import { getUserName } from "@/utils/session.js"

const route = useRoute()
const router = useRouter()
const props = defineProps(["runName"])
const focusWell = useWellStore()
const serviceClient = new LangQc()

let wellCollection = ref(null)
let user = ref(null);
let appConfig = ref(null)

getUserName((email) => { user.value = email }).then();

watch(() => route.query, (after, before) => {
    if ((after['qcLabel'] || after['qcRun']) && qcQueryChanged(before, after)) {
      focusWell.loadWellDetail(after.qcRun, after.qcLabel)
    }
  },
  { immediate: true }
)

watch(() => props.runName, () => {
  serviceClient.getWellsForRunPromise(props.runName).then(
    (data) => wellCollection.value = data.wells
  ).catch(error => {
    ElMessage({
      message: error.message,
      type: "warning",
      duration: 5000
    })
    // Stop table remaining with out of date content
    wellCollection.value = null
  })},
  { immediate: true }
)

onMounted(() => {
  serviceClient.getClientConfig().then(
    data => {
      appConfig.value = data
    }
  )
})

provide('config', appConfig); // Needed by the QC widget

function updateUrlQuery(newParams) {
  // Merges the current URL query with new parameters
  // The calling code does not need to replicate all properties from the
  // previous URL query.
  // route.query is read-only. We must copy it before modifying
  const newUrl = generateUrl(Object.assign({}, route.query), newParams, route.path)

  if (newUrl) {
    router.push(newUrl)
  }
}

function wellSelected(well) {
  updateUrlQuery({qcRun: well.qcRun, qcLabel: well.qcLabel})
}

</script>

<template>
  <h2 v-if="wellCollection">Wells for run {{ props.runName }}</h2>
  <WellTable v-if="wellCollection" :wellCollection="wellCollection" @wellSelected="wellSelected"/>
  <h2 v-else>No wells found for run. Search again</h2>
  <h2>Well QC View</h2>
  <div class="qcview" v-if="focusWell.runWell !== null">
    <div class="data">
      <QcView :runWell="focusWell.runWell" />
    </div>
    <aside class="controls">
      <QcControls :user="user" />
    </aside>
  </div>
  <div v-else>
    <p>Well QC data will appear here</p>
  </div>
</template>
