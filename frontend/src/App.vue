<template>
  <v-app>
    <!-- Fundo com imagem em baixa opacidade -->
    <div class="bg-image" />

    <v-app-bar color="primary" dark flat>
      <v-container class="d-flex align-center">
        <v-spacer />
        <v-btn
          v-if="isAuthenticated"
          variant="text"
          class="mr-2"
          @click="goToDashboard"
        >
          Enviar mensagens
        </v-btn>
        <v-btn
          v-if="isAuthenticated"
          variant="text"
          class="mr-2"
          @click="goToTemplates"
        >
          Templates
        </v-btn>
        <v-btn
          v-if="isAuthenticated"
          variant="text"
          class="mr-2"
          @click="goToAdmin"
        >
          Administração
        </v-btn>
        <v-btn
          v-if="isAuthenticated"
          variant="text"
          class="mr-4"
          @click="goToReports"
        >
          Relatórios
        </v-btn>
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

const isAuthenticated = computed(() => route.name !== 'Auth')
const showLogout = computed(() => route.meta.requiresAuth === true)

const goToDashboard = () => router.push('/dashboard')
const goToTemplates = () => router.push('/templates')
const goToAdmin = () => router.push('/admin')
const goToReports = () => router.push('/relatorios')

const logout = () => {
  localStorage.removeItem('access_token')
  router.push('/')
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