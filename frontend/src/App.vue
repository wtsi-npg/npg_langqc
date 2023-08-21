<script setup>
import { RouterView, useRoute } from 'vue-router';
import { onMounted, provide, ref } from "vue";
import { ElMessage } from "element-plus";
import { Search } from '@element-plus/icons-vue';

import router from "@/router/index.js";
import LangQc from "@/utils/langqc.js";

let logout_redirect_url = ref(null);
let input = ref('');
let searchMode = ref('search');
let appConfig = ref(null);
const apiClient = new LangQc();
const VERSION = APP_VERSION; // defined in vite.config.js
const DEVMODE = import.meta.env.DEV

let route = useRoute()

provide('appConfig', appConfig)

onMounted(() => {
  // Construct a logout url, the url to which the user is redirected must be registered
  // in your OIDC provider application.
  logout_redirect_url.value = "/login-redirect?logout=" + encodeURIComponent(location.origin);

  // Load app config
  try {
    apiClient.getClientConfig().then(
      data => {
        appConfig.value = data
      }
    )
  }
  catch (error) {
    console.error("Couldn't get app config from backend API")
    ElMessage({
      message: error.message,
      type: "error"
    });
  }
})

function goToRun(runName) {
  if (runName != '') {
    if (searchMode.value == 'search') {
      router.push({ name: 'WellsByRun', params: { runName: [runName] } })
    } else {
      compareAnotherRun(runName)
    }
  }
}

function compareAnotherRun(supplementalRunName) {
  if (supplementalRunName != '') {
    let previousRuns = [...route.params.runName]
    // Copying runName list to force vue-router to notice a change to
    // the array

    if (previousRuns.length > 5) {
      ElMessage({
        message: "Too many runs",
        type: "error"
      })
    } else if (!previousRuns.includes(supplementalRunName)) {
      previousRuns.push(supplementalRunName)
      console.log(`Now ${previousRuns}`)
      router.push({ name: 'WellsByRun', params: { runName: previousRuns } })
    }
  }
}

function notInWellsByRun() {
  return route.name == 'WellsByRun' ? false : true
}
</script>

<template>
  <!--
  Setting overflow style here required to unblock an unhelpful default in
  Element Plus layout container
  -->
  <el-main style="overflow:visible">

    <!-- Header -->
    <div>
      <img alt="Sanger logo" src="@/assets/sanger-logo.png" style="float:right" class="logo" />
      <h2 style="float:left">NPG LangQC for PacBio</h2>
    </div>
    <div style="clear:both" />

    <nav>
      <!-- Make these RouterLinks again somehow so we don't reload the whole app for nothing -->
      <el-link type="primary" href="/">Home</el-link>
      <el-link type="primary" href="about">About</el-link>
      <!--
      Using anchors instead of RouterLinks to make the browser fetch the page from the server,
      triggering the login or logout series of redirects.
      -->
      <el-link type="primary" href="/ui/login">Login</el-link>
      <el-link type="primary" :href="logout_redirect_url">Logout</el-link>

      <el-input v-model="input" placeholder="Run Name" @change="goToRun">
        <template #prepend>
          <el-tooltip content="Top center" placement="top">
            <template #content>Display one run (search)<br />Add one more run (also)</template>
            <el-select v-model="searchMode">
              <el-option value="search" />
              <el-option :disabled="notInWellsByRun()" label="also" value="also" />
            </el-select>
          </el-tooltip>
        </template>
        <template #append>
          <el-button :icon="Search" @click="goToRun(input)" />
        </template>
      </el-input>
    </nav>
    <!-- Header END -->

    <RouterView v-if="appConfig !== null" />

  </el-main>

  <el-footer>Copyright Genome Research Ltd 2023 - client version: {{ VERSION.replace(/['"]+/g) + (DEVMODE ? "+DEV" : "")
  }}</el-footer>
</template>

<style scoped>
h2 {
  color: #232642;
}

.logo {
  display: inline-block;
  height: 72px;
  width: auto;
  margin: 0 auto;
}

.el-link {
  margin-right: 8px;
}

.el-input {
  width: 250pt;
}

.el-select {
  width: 70pt;
}

.button {
  padding: 2pt;
}

.el-link .el-icon--right.el-icon {
  vertical-align: text-bottom;
}

nav {
  margin-bottom: 2pc;
}

.el-footer {
  vertical-align: bottom;
}

.el-footer,
.el-main {
  display: block;
  justify-content: normal;
  align-items: center;
  text-align: left;
}
</style>
