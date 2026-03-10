<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">
        <v-card elevation="12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Acesso ao Sistema</v-toolbar-title>
          </v-toolbar>
          <v-tabs v-model="tab" grow>
            <v-tab value="login">Login</v-tab>
            <v-tab value="register">Cadastro</v-tab>
          </v-tabs>
          <v-card-text>
            <v-window v-model="tab">
              <v-window-item value="login">
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
              </v-window-item>
              <v-window-item value="register">
                <v-form @submit.prevent="handleRegister" ref="registerForm">
                  <v-text-field
                    v-model="registerData.name"
                    label="Nome Completo"
                    required
                    variant="outlined"
                    class="mb-2"
                  ></v-text-field>
                  <v-text-field
                    v-model="registerData.email"
                    label="E-mail"
                    type="email"
                    required
                    variant="outlined"
                    class="mb-2"
                  ></v-text-field>
                  <v-text-field
                    v-model="registerData.password"
                    label="Senha"
                    type="password"
                    required
                    variant="outlined"
                  ></v-text-field>
                  <v-alert v-if="successMessage" type="success" class="mt-3" dense>
                    {{ successMessage }}
                  </v-alert>
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
                    Cadastrar
                  </v-btn>
                </v-form>
              </v-window-item>
            </v-window>
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
const tab = ref('login')
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const loginData = reactive({
  email: '',
  password: ''
})

const registerData = reactive({
  name: '',
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

const handleRegister = async () => {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const response = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(registerData)
    })
    const data = await response.json()
    if (!response.ok) {
      throw new Error(data.detail || 'Erro ao realizar cadastro')
    }
    successMessage.value = 'Cadastro realizado. Aguarde a aprovação do administrador.'
    registerData.name = ''
    registerData.email = ''
    registerData.password = ''
    setTimeout(() => {
      tab.value = 'login'
      successMessage.value = ''
    }, 3000)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}
</script>