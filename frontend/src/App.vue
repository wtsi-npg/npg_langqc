<script setup>
import { RouterView } from 'vue-router';
import { onMounted, provide, ref } from "vue";
import { ElMessage } from "element-plus";

import router from "@/router/index.js";
import LangQc from "@/utils/langqc.js";

let logout_redirect_url = ref(null);
let input = ref('');
let appConfig = ref(null);
const apiClient = new LangQc();

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
  catch(error) {
    console.error("Couldn't get app config from backend API")
    ElMessage({
      message: error.message,
      type: "error"
    });
  }
})

function goToRun(runName) {
  if (runName != '') {
    router.push({ name: 'WellsByRun', params: { runName: runName }})
  }
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
      <img alt="Sanger logo" src="@/assets/sanger-logo.png" style="float:right" class="logo"/>
      <h2 style="float:left">NPG LangQC for PacBio</h2>
    </div>
    <div style="clear:both"/>

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

      <el-input v-model="input" placeholder="Run Name" @change="goToRun"/>
      <el-icon><Search-icon @click="goToRun(input)"/></el-icon>
    </nav>
    <!-- Header END -->


    <RouterView />

  </el-main>

  <el-footer>Copyright Genome Research Ltd 2023</el-footer>

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
  width: 15pc;
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
