<script setup>
import { RouterView } from 'vue-router';
import { onMounted, ref } from "vue";

import useMessageStore from '@/stores/message.js';

const errorBuffer = useMessageStore();


let logout_redirect_url = ref(null);

onMounted(() => {

  // Construct a logout url, the url to which the user is redirected must be registered
  // in your OIDC provider application.
  logout_redirect_url.value = "/login-redirect?logout=" + encodeURIComponent(location.origin);
})
</script>

<template>
  <div>
    <el-container>
      <el-header direction="horizontal">
        <img alt="Sanger logo" src="@/assets/sanger-logo.png" height="50" class="logo"/>

        <h1>NPG Long Read QC</h1>

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
        </nav>

      </el-header>
      <el-main>
        <el-alert
          v-if="errorBuffer.errorMessages"
          v-for="error in errorBuffer.errorMessages"
          :key="error.id"
          title="Cannot get data"
          type="error"
          :description="error"
          show-icon
        />
        <RouterView />
      </el-main>
      <el-footer>Copyright Genome Research Ltd 2022</el-footer>
    </el-container>
  </div>
</template>

<style scoped>
.logo {
  display: inline-block;
  margin: 0 auto 1rem;
}

.el-link {
  margin-right: 8px;
}

.el-link .el-icon--right.el-icon {
  vertical-align: text-bottom;
}

.el-header {
  height: fit-content;
}

.el-footer {
  vertical-align: bottom;
}

.el-header,
.el-footer,
.el-main {
  display: block;
  justify-content: normal;
  align-items: center;
  text-align: left;
}

</style>
