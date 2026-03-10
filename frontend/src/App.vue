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
      </v-container>
    </v-app-bar>

    <v-main>
      <router-view />
    </v-main>
  </v-app>
</template>

<script setup>
</script>