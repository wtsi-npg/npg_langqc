<script setup>
import { onMounted, ref, provide, reactive, readonly, watch } from "vue";
import { ElMessage } from 'element-plus';

import QcView from "@/components/QcView.vue";
import LangQc from "@/utils/langqc.js";
import QcControls from "@/components/QcControls.vue";
import { useWellStore } from "@/stores/focusWell.js";
import { getUserName } from "@/utils/session.js"

const focusWell = useWellStore();

let serviceClient = null;

// Don't try to render much of anything until data arrives
// by reacting to these two vars
let appConfig = ref(null); // cache this I suppose
let wellCollection = ref(null);

let activeTab = ref('inbox'); // aka paneName in element-plus
let activePage = ref(1);
let pageSize = 10;
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

watch(() => this.$route.params, (after, before) => {
  if (after['label']) {
    activeWell.label = after.label
  }
  if (after['run']) {
    activeWell.runName = after.run
  }
  if (after['activeTab']) {
    activeTab.value = after.activeTab
  }
  if (after['page']) {
    activePage.value = after.page
  }
  if (after['userFilter']) {
    console.log(after.userFilter)
  }
  if (after['runFilter']) {
    console.log(after.runFilter)
  }
})

provide('activeTab', activeTab);
provide('config', appConfig);
provide('activeWell', readonly(activeWell));


function loadWellDetail(runName, label) {
  // Sets the runWell and QC state for the QcView components below

  serviceClient.getRunWellPromise(runName, label)
    .then(
      (well) => {
        focusWell.runWell = well;
      }
    ).catch(
      (error) => {
        ElMessage({
          message: error.message,
          type: error,
          duration: 5000
        })
      }
    );
  activeWell.runName = runName;
  activeWell.label = label;
}

function loadWells(status, page, pageSize) {
  serviceClient.getInboxPromise(status, page, pageSize).then(
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

function changeTab(selectedTab) {
  // To be triggered from Tab elements to load different data sets
  // Reset page to 1 on tab change
  activePage.value = 1;
  activeTab.value = selectedTab;
  loadWells(selectedTab, activePage.value, pageSize);
}

function changePage(pageNumber) {
  loadWells(activeTab.value, pageNumber, pageSize);
}

function externalTabChange(tabName) {
  // Triggered in response to events from other components
  activeTab.value = tabName;
}

onMounted(() => {
  serviceClient = new LangQc();
  try {
    loadWells(activeTab.value, activePage.value, pageSize);
    serviceClient.getClientConfig().then(
      data => appConfig.value = data
    );
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
    <el-tabs v-model="activeTab" type="border-card" @tab-change="changeTab">
      <el-tab-pane v-for="tab in appConfig.qc_flow_statuses" :key="tab.param" :label="tab.label" :name="tab.param">
        <table id="run_wells">
          <tr>
            <th>Run name</th>
            <th>Well label</th>
            <th>QC state</th>
            <th>QC date</th>
            <th>Assessor</th>
            <th>Well status</th>
            <th>Run status</th>
            <th>Well time start</th>
            <th>Well time complete</th>
          </tr>
          <tr :key="wellObj.run_name + ':' + wellObj.label" v-for="wellObj in wellCollection">
            <td>{{ wellObj.run_name }}</td>
            <td class="well_selector">
              <button v-on:click="loadWellDetail(wellObj.run_name, wellObj.label)">{{ wellObj.label }}</button>
            </td>
            <td>{{ wellObj.qc_state ? wellObj.qc_state.qc_state : '&nbsp;'}}</td>
            <td>{{ wellObj.qc_state ? wellObj.qc_state.date_updated : '&nbsp;'}}</td>
            <td>{{ wellObj.qc_state ? wellObj.qc_state.user : '&nbsp;'}}</td>
            <td>{{ wellObj.well_status ? wellObj.well_status : '&nbsp;'}}</td>
            <td>{{ wellObj.run_status ? wellObj.run_status : '&nbsp;'}}</td>
            <td>{{ wellObj.well_start_time ? wellObj.well_start_time : '&nbsp;'}}</td>
            <td>{{ wellObj.well_complete_time ? wellObj.well_complete_time : '&nbsp;'}}</td>
          </tr>
        </table>
      </el-tab-pane>
      <el-pagination v-model:currentPage="activePage" layout="prev, pager, next" v-bind:total="totalNumberOfWells"
        background :pager-count="5" :page-size="pageSize" :hide-on-single-page="true"
        @current-change="changePage"></el-pagination>
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

#run_wells {
  width: 100%;
}

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
