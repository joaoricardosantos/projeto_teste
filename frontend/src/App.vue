<template>
  <v-app>
    <v-app-bar color="primary" dark flat>
      <v-container class="d-flex align-center">
        <v-img
          src="/logo-pratika.png"
          alt="Pratika Administradora de Condomínios"
          max-height="56"
          max-width="200"
          contain
        />
        <v-spacer />
        <v-btn
          v-if="showLogout"
          icon
          @click="logout"
        >
          <v-icon>mdi-logout</v-icon>
        </v-btn>
      </v-container>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const showLogout = computed(() => route.meta.requiresAuth === true)

const logout = () => {
  localStorage.removeItem('access_token')
  router.push('/')
}
</script>