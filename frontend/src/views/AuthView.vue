<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="8" md="4">

        <!-- LOGIN -->
        <v-card v-if="screen === 'login'" elevation="12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Acesso ao Sistema</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form @submit.prevent="handleLogin">
              <v-text-field
                v-model="loginData.email"
                label="E-mail"
                type="email"
                required
                variant="outlined"
                class="mb-2"
              />
              <v-text-field
                v-model="loginData.password"
                label="Senha"
                type="password"
                required
                variant="outlined"
              />
              <v-alert v-if="errorMessage" type="error" class="mt-3" dense>
                {{ errorMessage }}
              </v-alert>
              <v-btn type="submit" color="primary" block class="mt-4" :loading="loading">
                Entrar
              </v-btn>
              <div class="text-center mt-3">
                <a href="#" class="text-primary text-decoration-none text-body-2"
                  @click.prevent="screen = 'forgot'">
                  Esqueci minha senha
                </a>
              </div>
            </v-form>
          </v-card-text>
        </v-card>

        <!-- ESQUECI A SENHA -->
        <v-card v-else-if="screen === 'forgot'" elevation="12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Redefinir senha</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <p class="text-body-2 mb-4 text-medium-emphasis">
              Informe seu e-mail e enviaremos um link para criar uma nova senha.
            </p>
            <v-form @submit.prevent="handleForgotPassword">
              <v-text-field
                v-model="forgotEmail"
                label="E-mail"
                type="email"
                required
                variant="outlined"
              />
              <v-alert v-if="errorMessage" type="error" class="mt-3" dense>
                {{ errorMessage }}
              </v-alert>
              <v-alert v-if="successMessage" type="success" class="mt-3" dense>
                {{ successMessage }}
              </v-alert>
              <v-btn type="submit" color="primary" block class="mt-4" :loading="loading">
                Enviar link de redefinição
              </v-btn>
              <div class="text-center mt-3">
                <a href="#" class="text-primary text-decoration-none text-body-2"
                  @click.prevent="goToLogin">
                  Voltar ao login
                </a>
              </div>
            </v-form>
          </v-card-text>
        </v-card>

        <!-- NOVA SENHA -->
        <v-card v-else-if="screen === 'reset'" elevation="12">
          <v-toolbar color="primary" dark flat>
            <v-toolbar-title>Nova senha</v-toolbar-title>
          </v-toolbar>
          <v-card-text>
            <v-form @submit.prevent="handleResetPassword">
              <v-text-field
                v-model="newPassword"
                label="Nova senha"
                type="password"
                required
                variant="outlined"
                class="mb-2"
              />
              <v-text-field
                v-model="confirmPassword"
                label="Confirmar nova senha"
                type="password"
                required
                variant="outlined"
              />
              <v-alert v-if="errorMessage" type="error" class="mt-3" dense>
                {{ errorMessage }}
              </v-alert>
              <v-alert v-if="successMessage" type="success" class="mt-3" dense>
                {{ successMessage }}
              </v-alert>
              <v-btn type="submit" color="primary" block class="mt-4" :loading="loading"
                :disabled="!!successMessage">
                Salvar nova senha
              </v-btn>
              <div v-if="successMessage" class="text-center mt-3">
                <a href="#" class="text-primary text-decoration-none text-body-2"
                  @click.prevent="goToLogin">
                  Ir para o login
                </a>
              </div>
            </v-form>
          </v-card-text>
        </v-card>

      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route = useRoute()

const screen = ref('login')
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

// Login
const loginData = reactive({ email: '', password: '' })

// Forgot
const forgotEmail = ref('')

// Reset
const newPassword = ref('')
const confirmPassword = ref('')
const resetToken = ref('')

onMounted(() => {
  const token = route.query.token
  if (token) {
    resetToken.value = token
    screen.value = 'reset'
  }
})

const goToLogin = () => {
  screen.value = 'login'
  errorMessage.value = ''
  successMessage.value = ''
}

const handleLogin = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const response = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(loginData),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || 'Erro ao realizar login')
    localStorage.setItem('access_token', data.access_token)
    router.push('/dashboard')
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const handleForgotPassword = async () => {
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  try {
    const response = await fetch('/api/auth/forgot-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email: forgotEmail.value }),
    })
    const data = await response.json()
    if (!response.ok) throw new Error(data.detail || 'Erro ao solicitar redefinição')
    successMessage.value = 'Se o e-mail estiver cadastrado, você receberá o link em breve.'
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}

const handleResetPassword = async () => {
  errorMessage.value = ''
  if (newPassword.value !== confirmPassword.value) {
    errorMessage.value = 'As senhas não coincidem.'
    return
  }
  if (newPassword.value.length < 8) {
    errorMessage.value = 'A senha deve ter pelo menos 8 caracteres.'
    return
  }
  loading.value = true
  try {
    const response = await fetch('/api/auth/reset-password', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        token: resetToken.value,
        new_password: newPassword.value,
      }),
    })
    const data = await response.json()
    if (!response.ok) {
      throw new Error(
        data.detail === 'Invalid_or_expired_token'
          ? 'Link inválido ou expirado. Solicite um novo.'
          : data.detail || 'Erro ao redefinir senha'
      )
    }
    successMessage.value = 'Senha redefinida com sucesso!'
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}
</script>