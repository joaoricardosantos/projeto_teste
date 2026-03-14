<template>
  <v-app>
    <div class="bg-image" />

    <v-app-bar color="primary" dark flat>
      <v-container class="d-flex align-center">
        <v-spacer />
        <v-btn v-if="isAuthenticated" variant="text" class="mr-2" @click="$router.push('/dashboard')">
          Dashboard
        </v-btn>
        <v-btn v-if="isAuthenticated" variant="text" class="mr-2" @click="$router.push('/painel')">
          Enviar mensagens
        </v-btn>
        <v-btn v-if="isAuthenticated" variant="text" class="mr-2" @click="$router.push('/templates')">
          Templates
        </v-btn>
        <v-btn v-if="isAuthenticated" variant="text" class="mr-2" @click="$router.push('/admin')">
          Administração
        </v-btn>
        <v-btn v-if="isAuthenticated" variant="text" class="mr-4" @click="$router.push('/relatorios')">
          Relatórios
        </v-btn>
        <v-btn v-if="showLogout" icon @click="logout">
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
import { useRoute } from 'vue-router'

const route = useRoute()
const isAuthenticated = computed(() => route.name !== 'Auth')
const showLogout = computed(() => route.meta.requiresAuth === true)

const logout = () => {
  localStorage.removeItem('access_token')
  location.href = '/'
}
</script>

<style>
.bg-image {
  position: fixed;
  inset: 0;
  z-index: 0;
  background-image: url('/fundosistema.png');
  background-size: cover;
  background-position: center;
  opacity: 0.08;
  pointer-events: none;
}
.v-main {
  position: relative;
  z-index: 1;
}
</style>