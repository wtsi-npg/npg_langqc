<script setup>
import { onMounted, ref } from "vue";
import { getUserName } from "@/utils/session.js"

let userEmail = ref(null);

onMounted(() => {
  getUserName((email) => { userEmail.value = email })
})

</script>

<template>
  <div class="about">
    <div v-if="userEmail == null">
      <h1>You are not logged in</h1>
    </div>
    <div v-else>
      <h1>You are logged in as {{ userEmail }}</h1>
    </div>
  </div>
</template>

<style></style>
