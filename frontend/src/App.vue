<script setup>
import { RouterLink, RouterView } from 'vue-router';
import { onMounted, ref } from "vue";

let logout_redirect_url = ref(null);

onMounted(() => {
  
  // Construct a logout url, the url to which the user is redirected must be registered
  // in your OIDC provider application.
  logout_redirect_url.value = "/login-redirect?logout=" + encodeURIComponent(location.origin);
  
})

</script>

<template>
  <header>
    <img alt="Sanger logo" src="@/assets/sanger-logo.png" height="50" />

    <h1>NPG Long Read QC</h1>

    <div class="wrapper">
      <nav>
        <RouterLink to="/">Home</RouterLink>
        <RouterLink to="/about">About</RouterLink>
        <!-- 
        Using anchors instead of RouterLinks to make the browser fetch the page from the server,
        triggering the login or logout series of redirects.
        -->
        <a href="/ui/login">Login</a>
        <a :href="logout_redirect_url">Logout</a>
      </nav>
    </div>
  </header>
  <div>
    <RouterView />
  </div>
</template>

<style scoped>
header {
  width: 100%;
}

.logo {
  display: inline-block;
  margin: 0 auto 2rem;
}

nav {
  width: 100%;
  font-size: 12px;
  margin-top: 2rem;
}

nav a.router-link-exact-active {
  color: var(--color-text);
}

nav a.router-link-exact-active:hover {
  background-color: transparent;
}

nav a {
  display: inline-block;
  padding: 0 1rem;
  border-left: 1px solid var(--color-border);
}

nav a:first-of-type {
  border: 0;
}

</style>
