<script setup>
/*
* A view for wells selected from a one or more instrument runs.
* Allows QC of individual wells. Page state is managed via the URL
*/
import { watch, ref } from "vue"
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
const props = defineProps({"runName": Array})
const focusWell = useWellStore()
const serviceClient = new LangQc()

let wellCollection = ref([])
let user = ref(null)

function flatten_data(values) {
  let collection = []
  for (let data of values) {
    collection.push(...data.wells)
  }
  return collection
}

getUserName((email) => { user.value = email }).then();

watch(() => route.query, (after, before) => {
    if ((after['idProduct']) && qcQueryChanged(before, after)) {
      focusWell.loadWellDetail(after.idProduct)
    }
  },
  { immediate: true }
)

watch(() => props.runName, () => {
  let promises = []
  for (let run of props.runName) {
    promises.push(serviceClient.getWellsForRunPromise(run))
  }
  Promise.all(promises).then(
      (values) => (wellCollection.value = flatten_data(values))
  ).catch(error => {
      ElMessage({
        message: error.message,
        type: "warning",
        duration: 10000
      })
    })
  },
  { immediate: true }
)

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

function wellSelected(idProduct) {
  updateUrlQuery({idProduct: idProduct})
}

</script>

<template>
  <h2 v-if="wellCollection.length > 0">Wells for run {{ props.runName.toString() }}</h2>
  <WellTable v-if="wellCollection.length > 0" :wellCollection="wellCollection" @wellSelected="wellSelected"/>
  <h2 v-else>No wells found for run. Search again</h2>
  <h2>Well QC View</h2>
  <div class="qcview" v-if="focusWell.well !== null">
    <div class="data">
      <QcView :well="focusWell.well" />
    </div>
    <aside class="controls">
      <QcControls :user="user" />
    </aside>
  </div>
  <div v-else>
    <p>Well QC data will appear here</p>
  </div>
</template>
