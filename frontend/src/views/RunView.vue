<script setup>
import { onMounted, ref, provide } from "vue";

import QcView from "@/components/QcView.vue";
import LangQc from "@/utils/langqc.js";

import { useMessageStore } from '@/stores/message.js';
import { useWellStore } from '@/stores/focusWell.js';

const errorBuffer = useMessageStore();
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

provide('activeTab', activeTab);

function loadWellDetail(runName, label) {
  // Sets the runWell for the QcView component below
  serviceClient.getRunWellPromise(runName, label)
  .then(
    wells => focusWell.runWell = wells
  ).catch(
    (error) => {
      errorBuffer.addMessage(error.message);
    }
  );
}

function loadWells(status, page, pageSize) {
  serviceClient.getInboxPromise(status, page, pageSize).then(
    data => {wellCollection.value = data.wells
             totalNumberOfWells.value = data.total_number_of_items}
  ).catch(
    (error) => {
      // Reset table of wells to prevent desired tab from showing data from another
      wellCollection.value = null;
      errorBuffer.addMessage(error.message);
    }
  );
}

function changeTab(selectedTab) {
  // To be triggered from Tab elements to load different data sets
  // Reset page to 1 on tab change
  activePage.value = 1;
  activeTab.value = selectedTab;
  console.log("Changing tab to " + selectedTab);
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
    console.log("Stuff went wrong getting data from backend: "+error);
    errorBuffer.addMessage(error.message);
  }
});

</script>

<template>
<div>
  <h2>Runs</h2>
</div>
<div v-if="appConfig !== null">
  <el-tabs v-model="activeTab" type="border-card" @tab-change="changeTab">
    <el-tab-pane
      v-for="tab in appConfig.qc_flow_statuses"
      :key="tab.param"
      :label="tab.label"
      :name="tab.param"
    >
      <table>
        <tr>
          <th>Run name</th>
          <th>Well label</th>
          <th>Time started</th>
          <th>Time completed</th>
          <th>QC state</th>
          <th>QC date</th>
          <th>Assessor</th>
        </tr>
        <tr :key="wellObj.run_name + ':' + wellObj.label" v-for="wellObj in wellCollection" >
          <td>{{ wellObj.run_name }}</td>
          <td>
            <button v-on:click="loadWellDetail(wellObj.run_name, wellObj.label)">{{ wellObj.label }}</button>
          </td>
          <td>{{ wellObj.run_start_time }}</td>
          <td>{{ wellObj.run_complete_time ? wellObj.run_complete_time : '&nbsp;'}}</td>
          <td>{{ wellObj.qc_state ? wellObj.qc_state.qc_state : '&nbsp;'}}</td>
          <td>{{ wellObj.qc_state ? wellObj.qc_state.date_updated : '&nbsp;'}}</td>
          <td>{{ wellObj.qc_state ? wellObj.qc_state.user : '&nbsp;'}}</td>
        </tr>
      </table>
    </el-tab-pane>
    <el-pagination
      v-model:currentPage="activePage"
      layout="prev, pager, next"
      v-bind:total="totalNumberOfWells"
      background
      :pager-count="5"
      :page-size="pageSize"
      :hide-on-single-page="true"
      @current-change="changePage"
    ></el-pagination>
  </el-tabs>
</div>
<div v-if="focusWell.runWell !== null">
  <h2>QC view</h2>
  <QcView :runWell="focusWell.runWell" @wellChanged="externalTabChange"/>
</div>
<div v-else>QC data will appear here</div>
</template>

<style>

</style>
