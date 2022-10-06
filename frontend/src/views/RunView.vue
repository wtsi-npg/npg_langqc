<script setup>
import { onMounted, ref } from "vue";

import QcView from "@/components/QcView.vue";
import LangQc from "@/utils/langqc.js";

let serviceClient = null;

// Don't try to render much of anything until data arrives
// by reacting to these three vars
let appConfig = ref(null); // cache this I suppose

let qcStatusTabs = ref(null);

let runWell = ref(null);
let wellCollection = ref(null);

// Pagination parameters
let startPage = 1;
let numWellsPerPage = 5;
let numPagesInWidget = 5;
let pager = ref(null)

function loadWellDetail(runName, label) {
  // Sets the runWell for the QcView component below
  serviceClient.getRunWellPromise(runName, label)
  .then(
    value => runWell.value = value
  );
}

function loadWellsByStatus(selectedTab) {
  // To be triggered from Tab elements to load different data sets
  let qc_status = selectedTab.tab.computedId;
  serviceClient.getInboxPromise(numWellsPerPage, startPage, qc_status).then(
    data => wellCollection.value = data
  );
  // console.log(pager.value.currentPage); //always 1 )
  // TODO - Have to reset pagination, make page 1 active page.
  // Alternatively to request the currently active page.
}

onMounted(() => {
  serviceClient = new LangQc();
  try {
    serviceClient.getInboxPromise(numWellsPerPage, startPage, 'inbox').then(
      data => wellCollection.value = data
    );
    serviceClient.getClientConfig().then(
      data => appConfig.value = data
    );
  } catch (error) {
    console.log("Stuff went wrong getting data from backend: "+error);
  }
});

function onClickPageHandler(page) {
    //At the end remove the leading hash character.
    let qc_status = qcStatusTabs.value.activeTabHash.substring(1)
    try {
      serviceClient.getInboxPromise(numWellsPerPage, page, qc_status).then(
        data => wellCollection.value = data
    );
    } catch (error) {
      console.log("Stuff went wrong getting data from backend: "+error);
    }
};

</script>

<template>
<div>
  <h2>Runs</h2>
</div>
<div v-if="appConfig !== null">
  <tabs ref="qcStatusTabs" @clicked="loadWellsByStatus">
    <tab
      v-for="tab in appConfig.qc_flow_statuses"
      :key="tab.param"
      :name="tab.label"
      :id="tab.param"
      nav-item-class="nav-item"
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
    </tab>
  </tabs>
</div>

<vue-awesome-paginate ref="pager"
  :total-items="100"
  :items-per-page="numWellsPerPage"
  :max-pages-shown="numPagesInWidget"
  :current-page="startPage"
  :show-jump-buttons="false"
  :show-breakpoint-buttons="true"
  :show-ending-buttons:="true"
  :on-click="onClickPageHandler"
/>

<div v-if="runWell !== null">
  <h2>QC view</h2>
  <QcView :runWell="runWell"/>
</div>
<div v-else>QC data will appear here</div>
</template>

<style>
  .tabs-component {
    margin: 4em 0;
  }

  .tabs-component-tabs {
    border: solid 1px #ddd;
    border-radius: 6px;
    margin-bottom: 5px;
  }

  @media (min-width: 700px) {
    .tabs-component-tabs {
      border: 0;
      align-items: stretch;
      display: flex;
      justify-content: flex-start;
      margin-bottom: -1px;
    }
  }

  .tabs-component-tab {
    color: #999;
    font-size: 14px;
    font-weight: 600;
    margin-right: 0;
    list-style: none;
  }

  .tabs-component-tab:not(:last-child) {
    border-bottom: dotted 1px #ddd;
  }

  .tabs-component-tab:hover {
    color: #666;
  }

  .tabs-component-tab.is-active {
    color: #000;
  }

  .tabs-component-tab.is-disabled * {
    color: #cdcdcd;
    cursor: not-allowed !important;
  }

  @media (min-width: 700px) {
    .tabs-component-tab {
      background-color: #fff;
      border: solid 1px #ddd;
      border-radius: 3px 3px 0 0;
      margin-right: .5em;
      transform: translateY(2px);
      transition: transform .3s ease;
    }

    .tabs-component-tab.is-active {
      border-bottom: solid 1px #fff;
      z-index: 2;
      transform: translateY(0);
    }
  }

  .tabs-component-tab-a {
    align-items: center;
    color: inherit;
    display: flex;
    padding: .75em 1em;
    text-decoration: none;
  }

  .tabs-component-panels {
    padding: 4em 0;
  }

  @media (min-width: 700px) {
    .tabs-component-panels {
      background-color: #fff;
      border: solid 1px #ddd;
      border-radius: 0 6px 6px 6px;
      box-shadow: 0 0 10px rgba(0, 0, 0, .05);
      padding: 4em 2em;
    }
  }

  .tabs-component-btn {
    cursor: pointer;
    background: #e1ecf4;
    border-radius: 3px;
    border: 1px solid #7aa7c7;
    padding: 4px 8px;
    color: #39739d;
  }

  .tabs-component-btn:hover {
    background-color: #b3d3ea;
    color: #2c5777;
  }

  .tabs-component-btn:active {
    background-color: #a0c7e4;
    box-shadow: none;
    color: #2c5777;
  }

  .pagination-container {
    display: flex;
    column-gap: 10px;
    margin-top: 30px;
    margin-bottom: 30px;
  }

  .paginate-buttons {
    height: 40px;
    width: 40px;
    border-radius: 20px;
    cursor: pointer;
    background-color: rgb(242, 242, 242);
    border: 1px solid rgb(217, 217, 217);
    color: black;
  }

  .paginate-buttons:hover {
    background-color: #d8d8d8;
  }

  .active-page {
    background-color: #3498db;
    border: 1px solid #3498db;
    color: white;
  }

  .active-page:hover {
    background-color: #2988c8;
  }
</style>
