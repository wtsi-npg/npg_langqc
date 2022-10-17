<script setup>
import { onMounted, ref } from "vue";

import QcView from "@/components/QcView.vue";
import LangQc from "@/utils/langqc.js";

let serviceClient = null;

// Don't try to render much of anything until data arrives
// by reacting to these three vars
let appConfig = ref(null); // cache this I suppose

let runWell = ref(null);
let wellCollection = ref(null);

let activeTab = ref('inbox'); // aka paneName in element-plus
let activePage = ref(1);

function loadWellDetail(runName, label) {
  // Sets the runWell for the QcView component below
  serviceClient.getRunWellPromise(runName, label)
  .then(
    wells => runWell.value = wells
  );
}

function loadWells(status, page, pageSize) {
  serviceClient.getInboxPromise(status, 1, page, pageSize).then(
    data => wellCollection.value = data
  ).catch(
    (error) => {
      // Reset table of wells to prevent desired tab from showing data from another
      wellCollection.value = null;
    }
  );
}

function changeTab(selectedTab) {
  // To be triggered from Tab elements to load different data sets
  activePage.value = 1;
  loadWells(selectedTab);
}

function changePage(pageNumber) {
  loadWells(activeTab.value, pageNumber);
}

onMounted(() => {
  serviceClient = new LangQc();
  try {
    loadWells(activeTab.value, activePage.value, 10);
    serviceClient.getClientConfig().then(
      data => appConfig.value = data
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
        </tr>
        <tr :key="wellObj.run_name + ':' + wellObj.label" v-for="wellObj in wellCollection" >
          <td>{{ wellObj.run_name }}</td>
          <td>
            <button v-on:click="loadWellDetail(wellObj.run_name, wellObj.label)">{{ wellObj.label }}</button>
          </td>
          <td>{{ wellObj.run_start_time }}</td>
          <td>{{ wellObj.run_complete_time ? wellObj.run_complete_time : ''}}</td>
        </tr>
      </table>
    </el-tab-pane>
    <el-pagination
      v-model:currentPage="activePage"
      layout="prev, pager, next"
      :total="20"
      background
      :pager-count="5"
      :page-size="10"
      :hide-on-single-page="true"
      @current-change="changePage"
    ></el-pagination>
  </el-tabs>
</div>
<div v-if="runWell !== null">
  <h2>QC view</h2>
  <QcView :runWell="runWell"/>
</div>
<div v-else>QC data will appear here</div>
</template>

<style>

</style>
