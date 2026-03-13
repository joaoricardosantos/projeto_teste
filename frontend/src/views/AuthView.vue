<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="5" lg="4">
        <v-card elevation="8" class="pa-4">

          <v-card-title class="text-h5 font-weight-bold text-center pa-4 pb-2">
            Entrar no Sistema
          </v-card-title>
          <v-card-subtitle class="text-center pb-4">
            Sistema de Inadimplentes
          </v-card-subtitle>

          <v-card-text>
            <v-form @submit.prevent="handleLogin">

              <v-text-field
                v-model="email"
                label="E-mail"
                type="email"
                variant="outlined"
                prepend-inner-icon="mdi-email-outline"
                class="mb-3"
                required
                :disabled="loading"
              />

              <v-text-field
                v-model="password"
                label="Senha"
                :type="showPassword ? 'text' : 'password'"
                variant="outlined"
                prepend-inner-icon="mdi-lock-outline"
                :append-inner-icon="showPassword ? 'mdi-eye-off' : 'mdi-eye'"
                @click:append-inner="showPassword = !showPassword"
                class="mb-4"
                required
                :disabled="loading"
              />

              <v-alert v-if="errorMessage" type="error" class="mb-4" dense closable @click:close="errorMessage = ''">
                {{ errorMessage }}
              </v-alert>

              <v-btn
                type="submit"
                color="primary"
                block
                size="large"
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const email = ref('')
const password = ref('')
const showPassword = ref(false)
const loading = ref(false)
const errorMessage = ref('')

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''

  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: email.value, password: password.value }),
    })

    const data = await response.json()

    if (!response.ok) {
      const msgs = {
        Invalid_credentials: 'E-mail ou senha inválidos.',
        Account_pending_approval: 'Sua conta ainda aguarda aprovação do administrador.',
        Account_disabled: 'Sua conta está desativada. Entre em contato com o administrador.',
      }
      throw new Error(msgs[data.detail] || data.detail || 'Erro ao fazer login.')
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