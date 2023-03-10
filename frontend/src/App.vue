<script setup>
import { RouterView } from 'vue-router';
import { onMounted, ref } from "vue";

let logout_redirect_url = ref(null);

onMounted(() => {

  // Construct a logout url, the url to which the user is redirected must be registered
  // in your OIDC provider application.
  logout_redirect_url.value = "/login-redirect?logout=" + encodeURIComponent(location.origin);
})
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
      <h2 style="float:left;color:#232642">NPG LangQC for PacBio</h2>
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
    </nav>
    <!-- Header END -->

    <RouterView />
  
  </el-main>

  <el-footer>Copyright Genome Research Ltd 2023</el-footer>

</template>

<style scoped>
.logo {
  display: inline-block;
  height: 72px;
  width: auto;
  margin: 0 auto;
}

.el-link {
  margin-right: 8px;
  margin-bottom: 30px;
}

.el-link .el-icon--right.el-icon {
  vertical-align: text-bottom;
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
