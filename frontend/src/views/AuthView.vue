<template>
  <div class="auth-page">

    <!-- Background decorativo -->
    <div class="auth-bg">
      <div class="bg-orb bg-orb--1" />
      <div class="bg-orb bg-orb--2" />
      <div class="bg-grid" />
    </div>

    <div class="auth-layout">

      <!-- Painel esquerdo (visual) -->
      <div class="auth-left d-none d-md-flex">
        <div class="auth-left-content">
          <div class="brand-badge">
            <div class="brand-icon">
              <v-icon size="28" color="white">mdi-home-city</v-icon>
            </div>
            <div>
              <div class="brand-title">Pratika</div>
              <div class="brand-tagline">Sistema de Cobranças</div>
            </div>
          </div>

          <h1 class="auth-headline">
            Automatize suas<br>
            <span class="headline-accent">cobranças</span><br>
            com inteligência.
          </h1>

          <p class="auth-desc">
            Disparo em massa via WhatsApp, relatórios em tempo real e
            gestão completa da inadimplência do seu condomínio.
          </p>

          <div class="feature-list">
            <div v-for="f in features" :key="f.text" class="feature-item">
              <div class="feature-dot" />
              <span>{{ f.text }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Painel direito (form) -->
      <div class="auth-right">
        <div class="auth-card">

          <!-- Logo mobile -->
          <div class="d-flex d-md-none align-center gap-3 mb-8">
            <div class="brand-icon">
              <v-icon size="24" color="white">mdi-home-city</v-icon>
            </div>
            <div>
              <div class="brand-title" style="color: #006837;">Pratika</div>
            </div>
          </div>

          <div class="mb-8">
            <h2 class="form-title">Bem-vindo de volta</h2>
            <p class="form-subtitle">Entre com suas credenciais para continuar</p>
          </div>

          <!-- Tabs Login / Cadastro -->
          <div class="auth-tabs mb-6">
            <button
              class="auth-tab"
              :class="{ active: mode === 'login' }"
              @click="switchMode('login')"
            >Entrar</button>
            <button
              class="auth-tab"
              :class="{ active: mode === 'register' }"
              @click="switchMode('register')"
            >Criar conta</button>
          </div>

          <!-- Login form -->
          <Transition name="form-fade" mode="out-in">
            <div v-if="mode === 'login'" key="login">
              <div class="field-group">
                <label class="field-label">E-mail</label>
                <v-text-field
                  v-model="email"
                  type="email"
                  placeholder="seu@email.com"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-email-outline"
                  hide-details="auto"
                  class="auth-field"
                  :disabled="loading"
                  @keyup.enter="handleLogin"
                />
              </div>

              <div class="field-group">
                <div class="d-flex justify-space-between align-center mb-1">
                  <label class="field-label">Senha</label>
                </div>
                <v-text-field
                  v-model="password"
                  :type="showPassword ? 'text' : 'password'"
                  placeholder="••••••••"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-lock-outline"
                  :append-inner-icon="showPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
                  hide-details="auto"
                  class="auth-field"
                  :disabled="loading"
                  @click:append-inner="showPassword = !showPassword"
                  @keyup.enter="handleLogin"
                />
              </div>

              <v-alert
                v-if="errorMessage"
                type="error"
                variant="tonal"
                density="compact"
                class="mb-4"
                closable
                @click:close="errorMessage = ''"
              >{{ errorMessage }}</v-alert>

              <v-btn
                block
                size="large"
                color="primary"
                class="submit-btn mt-2"
                :loading="loading"
                @click="handleLogin"
              >
                <v-icon start>mdi-login</v-icon>
                Entrar no sistema
              </v-btn>
            </div>

            <!-- Register form -->
            <div v-else key="register">
              <div class="field-group">
                <label class="field-label">Nome completo</label>
                <v-text-field
                  v-model="regName"
                  placeholder="Seu nome"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-account-outline"
                  hide-details="auto"
                  class="auth-field"
                  :disabled="loading"
                />
              </div>

              <div class="field-group">
                <label class="field-label">E-mail</label>
                <v-text-field
                  v-model="regEmail"
                  type="email"
                  placeholder="seu@email.com"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-email-outline"
                  hide-details="auto"
                  class="auth-field"
                  :disabled="loading"
                />
              </div>

              <div class="field-group">
                <label class="field-label">Senha</label>
                <v-text-field
                  v-model="regPassword"
                  :type="showRegPassword ? 'text' : 'password'"
                  placeholder="Mínimo 8 caracteres"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-lock-outline"
                  :append-inner-icon="showRegPassword ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
                  hide-details="auto"
                  class="auth-field"
                  :disabled="loading"
                  @click:append-inner="showRegPassword = !showRegPassword"
                />
              </div>

              <v-alert v-if="regSuccess" type="success" variant="tonal" density="compact" class="mb-4">
                {{ regSuccess }}
              </v-alert>
              <v-alert v-if="regError" type="error" variant="tonal" density="compact" class="mb-4" closable @click:close="regError = ''">
                {{ regError }}
              </v-alert>

              <v-btn
                block
                size="large"
                color="primary"
                class="submit-btn mt-2"
                :loading="loading"
                @click="handleRegister"
              >
                <v-icon start>mdi-account-plus</v-icon>
                Criar minha conta
              </v-btn>

              <p class="pending-note mt-4">
                <v-icon size="14" color="warning" class="mr-1">mdi-information-outline</v-icon>
                Após o cadastro, aguarde a aprovação do administrador.
              </p>
            </div>
          </Transition>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const mode          = ref('login')
const email         = ref('')
const password      = ref('')
const showPassword  = ref(false)
const loading       = ref(false)
const errorMessage  = ref('')

const regName        = ref('')
const regEmail       = ref('')
const regPassword    = ref('')
const showRegPassword = ref(false)
const regSuccess     = ref('')
const regError       = ref('')

const features = [
  { text: 'Disparo automático via WhatsApp' },
  { text: 'Relatórios detalhados da Superlógica' },
  { text: 'Templates personalizados com variáveis' },
  { text: 'Controle de campanhas e histórico' },
]

const switchMode = (m) => {
  mode.value = m
  errorMessage.value = ''
  regSuccess.value   = ''
  regError.value     = ''
}

const handleLogin = async () => {
  loading.value      = true
  errorMessage.value = ''
  try {
    const res  = await fetch('/api/auth/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email: email.value, password: password.value }),
    })
    const data = await res.json()
    if (!res.ok) {
      const msgs = {
        Invalid_credentials:       'E-mail ou senha inválidos.',
        Account_pending_approval:  'Sua conta ainda aguarda aprovação do administrador.',
        Account_disabled:          'Sua conta está desativada. Fale com o administrador.',
      }
      throw new Error(msgs[data.detail] || data.detail || 'Erro ao fazer login.')
    }
    localStorage.setItem('access_token', data.access_token)
    router.push('/dashboard')
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    loading.value = false
  }
}

const handleRegister = async () => {
  loading.value    = true
  regSuccess.value = ''
  regError.value   = ''
  try {
    const res  = await fetch('/api/auth/register', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ name: regName.value, email: regEmail.value, password: regPassword.value }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Erro ao criar conta.')
    regSuccess.value  = 'Conta criada! Aguarde aprovação do administrador.'
    regName.value     = ''
    regEmail.value    = ''
    regPassword.value = ''
  } catch (e) {
    regError.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ── Layout ── */
.auth-page {
  min-height: 100vh;
  position: relative;
  overflow: hidden;
  background: #f0f2f5;
  display: flex;
}

/* Background decorativo */
.auth-bg {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.35;
}
.bg-orb--1 {
  width: 500px; height: 500px;
  background: radial-gradient(circle, #00a651 0%, transparent 70%);
  top: -100px; left: -100px;
}
.bg-orb--2 {
  width: 400px; height: 400px;
  background: radial-gradient(circle, #006837 0%, transparent 70%);
  bottom: -80px; right: 35%;
  opacity: 0.2;
}
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0,104,55,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0,104,55,0.04) 1px, transparent 1px);
  background-size: 40px 40px;
}

/* Layout */
.auth-layout {
  position: relative;
  z-index: 1;
  display: flex;
  width: 100%;
  min-height: 100vh;
}

/* Painel esquerdo */
.auth-left {
  flex: 1;
  background: linear-gradient(150deg, #0f1d14 0%, #1a3a23 60%, #0a2e12 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 60px 56px;
  position: relative;
  overflow: hidden;
}
.auth-left::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url('/fundosistema.png');
  background-size: cover;
  background-position: center;
  opacity: 0.06;
}
.auth-left-content {
  position: relative;
  z-index: 1;
  max-width: 420px;
}
.brand-badge {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 52px;
}
.brand-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #00a651 0%, #006837 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 6px 20px rgba(0, 168, 81, 0.4);
}
.brand-title {
  font-size: 18px;
  font-weight: 700;
  color: white;
  letter-spacing: -0.02em;
}
.brand-tagline {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  text-transform: uppercase;
  letter-spacing: 0.1em;
}
.auth-headline {
  font-size: 40px;
  font-weight: 800;
  color: white;
  line-height: 1.15;
  letter-spacing: -0.03em;
  margin-bottom: 20px;
}
.headline-accent {
  color: #4ade80;
}
.auth-desc {
  font-size: 15px;
  color: rgba(255, 255, 255, 0.55);
  line-height: 1.65;
  margin-bottom: 36px;
}
.feature-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}
.feature-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: #4ade80;
  flex-shrink: 0;
  box-shadow: 0 0 8px rgba(74, 222, 128, 0.6);
}

/* Painel direito */
.auth-right {
  width: 100%;
  max-width: 480px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 32px;
  background: white;
}
@media (min-width: 960px) {
  .auth-right {
    flex-shrink: 0;
  }
}

.auth-card {
  width: 100%;
  max-width: 380px;
}

.form-title {
  font-size: 26px;
  font-weight: 700;
  color: #0f1d14;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}
.form-subtitle {
  font-size: 14px;
  color: #6b7280;
}

/* Tabs */
.auth-tabs {
  display: flex;
  background: #f3f4f6;
  border-radius: 10px;
  padding: 3px;
  gap: 2px;
}
.auth-tab {
  flex: 1;
  padding: 9px 16px;
  border: none;
  border-radius: 8px;
  background: transparent;
  font-size: 13.5px;
  font-weight: 500;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s ease;
}
.auth-tab.active {
  background: white;
  color: #006837;
  font-weight: 600;
  box-shadow: 0 1px 4px rgba(0,0,0,0.1);
}

/* Fields */
.field-group {
  margin-bottom: 16px;
}
.field-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}
.auth-field :deep(.v-field) {
  border-radius: 10px !important;
}
.auth-field :deep(.v-field__outline__start) {
  border-radius: 10px 0 0 10px !important;
}
.auth-field :deep(.v-field__outline__end) {
  border-radius: 0 10px 10px 0 !important;
}

/* Submit */
.submit-btn {
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  letter-spacing: 0.01em !important;
  box-shadow: 0 4px 16px rgba(0, 104, 55, 0.3) !important;
  transition: box-shadow 0.2s, transform 0.15s !important;
}
.submit-btn:hover {
  box-shadow: 0 6px 20px rgba(0, 104, 55, 0.4) !important;
  transform: translateY(-1px);
}

.pending-note {
  font-size: 12px;
  color: #9ca3af;
  text-align: center;
}

/* Form transition */
.form-fade-enter-active,
.form-fade-leave-active {
  transition: opacity 0.2s ease, transform 0.2s ease;
}
.form-fade-enter-from {
  opacity: 0;
  transform: translateX(12px);
}
.form-fade-leave-to {
  opacity: 0;
  transform: translateX(-12px);
}
</style>