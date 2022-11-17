<script setup>
import { onMounted, ref } from "vue";

let user_email = ref(null);

onMounted(() => {
  // Get the user information from the apache OIDC module
  // see https://github.com/zmartzone/mod_auth_openidc/wiki/Single-Page-Applications#session-info
  fetch(location.origin + "/login-redirect?info=json")
    .then((response) => {
      if (response.ok) {
        response.json()
          .then((content) => {
            user_email.value = content.userinfo.email;
          })
      }
    })
})

</script>

<template>
  <div class="about">
    <div v-if="user_email == null">
      <h1>You are not logged in</h1>
    </div>
    <div v-else>
      <h1>You are logged in as {{ user_email }}</h1>
    </div>
  </div>
</template>

<style>
</style>
