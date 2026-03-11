<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card elevation="12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Acesso ao Sistema</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form @submit.prevent="handleLogin" ref="loginForm">
              <v-text-field
                v-model="loginData.email"
                label="E-mail"
                type="email"
                required
                variant="outlined"
                class="mb-2"
              ></v-text-field>
              <v-text-field
                v-model="loginData.password"
                label="Senha"
                type="password"
                required
                variant="outlined"
              ></v-text-field>
              <v-alert v-if="errorMessage" type="error" class="mt-3" dense>
                {{ errorMessage }}
              </v-alert>
              <v-btn
                type="submit"
                color="primary"
                block
                class="mt-4"
                :loading="loading"
              >
                Entrar
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const loading = ref(false)
const errorMessage = ref('')

const loginData = reactive({
  email: '',
  password: ''
})

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginData)
    })
    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || 'Erro ao realizar login')
    }
    localStorage.setItem('access_token', data.access_token)
    router.push('/dashboard')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}
</script>