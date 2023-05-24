<script setup>
import { onMounted, ref, provide, reactive, readonly, watch } from "vue";
import { useRoute, useRouter } from "vue-router";
import { ElMessage } from 'element-plus';

import QcView from "@/components/QcView.vue";
import LangQc from "@/utils/langqc.js";
import QcControls from "@/components/QcControls.vue";
import WellTable from "@/components/WellTable.vue";
import { useWellStore } from "@/stores/focusWell.js";
import { getUserName } from "@/utils/session.js"
import { generateUrl, qcQueryChanged } from "@/utils/url.js";

const focusWell = useWellStore();
const route = useRoute();
const router = useRouter();

const serviceClient = new LangQc();

// Don't try to render much of anything until data arrives
// by reacting to these two vars
let appConfig = ref(null); // cache this I suppose
let wellCollection = ref(null);

let activeTab = ref('inbox'); // aka paneName in element-plus
let activePage = ref(1);
let pageSize = ref(10);
let totalNumberOfWells = ref(0);
// Inform app-wide elements when focus has changed.
// Perhaps we can watch the store instead? We're not transmitting the data
// this way
let activeWell = reactive({
  runName: null,
  label: null
});

let user = ref(null);
getUserName((email) => { user.value = email }).then();

// Page configuration is dictated by URL query ?param
// Other parts of this component update the URL to trigger navigation within
// the page.
// This allows users to bookmark the view and retain the configuration.

// Tricky stuff. Reactivity and URL updates readily create cascades and loops
// of loading data. Change with caution!

watch(() => route.query, (after, before) => {
  // URL numbers are strings. Convert to int for the pagination widget
  let newPage = undefined
  if (after.page) {
    newPage = parseInt(after.page)
  }

  // Handle the run and well to show in the QC Viewer
  if (after && (after.qcLabel || after.qcRun) && qcQueryChanged(before, after)) {
    // Somehow we need to capture the other parameter in case both have not been set
    loadWellDetail(after.qcRun, after.qcLabel)
  }

  // Handle changes of tab in the table of wells.
  // Changes to selected tab negates a page change operation
  if (after.activeTab && (before === undefined || after.activeTab != before.activeTab)) {
    loadWells(after.activeTab, newPage)
    activeTab.value = after.activeTab;
    if (before == undefined || after.page != before.page) {
      activePage.value = newPage;
    }
  } else if (after.page && (before == undefined || after.page != before.page)) {
    loadWells(activeTab.value, newPage)
    activePage.value = newPage;
  }
},
  // The watch process begins immediately on component load in order to catch
  // a user-supplied query in the URL
  { immediate: true }
)

provide('activeTab', activeTab);
provide('config', appConfig);
provide('activeWell', readonly(activeWell));


function loadWellDetail(runName, label) {
  // Sets the runWell and QC state for the QcView components below

  focusWell.loadWellDetail(runName, label)
  activeWell.runName = runName;
  activeWell.label = label;
}

function loadWells(status, page) {
  // Gets data for the current page of wells in the tab

  serviceClient.getInboxPromise(status, page, pageSize.value).then(
    data => {
      wellCollection.value = data.wells
      totalNumberOfWells.value = data.total_number_of_items
    }
  ).catch(
    (error) => {
      // Reset table of wells to prevent desired tab from showing data from another
      wellCollection.value = null;
      ElMessage({
        message: error.message,
        type: "warning",
        duration: 5000
      })
    }
  );
}

function clickTabChange(selectedTab) {
  updateUrlQuery({ activeTab: selectedTab, page: 1 })
}

function clickPageChange(pageNumber) {
  updateUrlQuery({ page: pageNumber })
}

function externalTabChange(tabName) {
  // Triggered in response to events from other components
  activeTab.value = tabName;
}

function changePageSize(size) {
  // pageSize.value = size
  loadWells(activeTab.value, activePage.value)
}

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

onMounted(() => {
  try {
    serviceClient.getClientConfig().then(
      data => {
        appConfig.value = data
      }
    );
    // If there are no query properties in the URL, we can "redirect" to a
    // sensible default
    if (!route.query['activeTab']) {
      updateUrlQuery({activeTab: 'inbox', page: 1})
    }
  } catch (error) {
    console.log("Stuff went wrong getting data from backend: " + error);
    ElMessage({
      message: error.message,
      type: "error"
    });
  }
});

</script>

<template>
  <div v-if="appConfig !== null">
    <el-tabs v-model="activeTab" type="border-card" @tab-change="clickTabChange">
      <el-tab-pane v-for="tab in appConfig.qc_flow_statuses" :key="tab.param" :label="tab.label" :name="tab.param">
        <WellTable :wellCollection="wellCollection" @wellSelected="updateUrlQuery"/>
      </el-tab-pane>
      <el-pagination v-model:currentPage="activePage" layout="prev, pager, next, sizes" v-bind:total="totalNumberOfWells"
        background :pager-count="5" v-model:page-size="pageSize" :hide-on-single-page="true"
        @current-change="clickPageChange" @size-change="changePageSize"></el-pagination>
    </el-tabs>
  </div>
  <h2>Well QC View</h2>
  <div class="qcview" v-if="focusWell.runWell !== null">
    <div class="data">
      <QcView :runWell="focusWell.runWell" />
    </div>
    <aside class="controls">
      <QcControls @wellChanged="externalTabChange" :user="user" />
    </aside>
  </div>
  <div v-else>
    <p>Well QC data will appear here</p>
  </div>
</template>

<style>
.qcview {
  display: grid;
  grid-template-columns: 3fr 1fr;
  grid-template-areas:
    "metric control";
  grid-column-gap: 10px;
}

.controls {
  grid-area: control;
}

.data {
  grid-area: metric;
}
</style>
