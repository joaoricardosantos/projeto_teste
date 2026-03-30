<template>
  <div class="auth-page">

    <div class="auth-bg">
      <div class="bg-orb bg-orb--1" />
      <div class="bg-orb bg-orb--2" />
      <div class="bg-orb bg-orb--3" />
      <div class="bg-grid" />
    </div>

    <div class="auth-layout">

      <!-- Painel esquerdo (visual) -->
      <div class="auth-left">
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
          <div class="mobile-brand">
            <div class="brand-icon">
              <v-icon size="24" color="white">mdi-home-city</v-icon>
            </div>
            <div class="brand-title" style="color: #059669;">Pratika</div>
          </div>

          <div class="form-header">
            <h2 class="form-title">Bem-vindo de volta</h2>
            <p class="form-subtitle">Entre com suas credenciais para continuar</p>
          </div>

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
            <label class="field-label">Senha</label>
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

          <!-- Link esqueci senha -->
          <div class="text-right mb-3" style="margin-top: -8px;">
            <a
              href="#"
              class="forgot-link"
              @click.prevent="dialogEsqueci = true"
            >Esqueci minha senha</a>
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

          <!-- Dialog: Esqueci minha senha -->
          <v-dialog v-model="dialogEsqueci" max-width="420" persistent>
            <v-card rounded="xl" class="pa-2">
              <v-card-title class="pa-4 pb-2 d-flex align-center">
                <v-icon color="primary" class="mr-2">mdi-lock-reset</v-icon>
                Recuperar senha
              </v-card-title>
              <v-card-text class="pa-4 pt-2">
                <p class="text-body-2 text-medium-emphasis mb-4">
                  Digite o e-mail da sua conta. Se ele estiver cadastrado, enviaremos um link para redefinir sua senha.
                </p>

                <v-alert
                  v-if="esqueciSucesso"
                  type="success"
                  variant="tonal"
                  density="compact"
                  class="mb-4"
                >{{ esqueciSucesso }}</v-alert>

                <v-alert
                  v-if="esqueciErro"
                  type="error"
                  variant="tonal"
                  density="compact"
                  class="mb-4"
                  closable
                  @click:close="esqueciErro = ''"
                >{{ esqueciErro }}</v-alert>

                <v-text-field
                  v-if="!esqueciSucesso"
                  v-model="esqueciEmail"
                  label="E-mail"
                  type="email"
                  variant="outlined"
                  density="comfortable"
                  prepend-inner-icon="mdi-email-outline"
                  hide-details="auto"
                  class="auth-field"
                  :disabled="esqueciLoading"
                  @keyup.enter="enviarEsqueci"
                />
              </v-card-text>
              <v-card-actions class="pa-4 pt-0">
                <v-btn
                  variant="text"
                  @click="fecharEsqueci"
                >Cancelar</v-btn>
                <v-spacer />
                <v-btn
                  v-if="!esqueciSucesso"
                  color="primary"
                  variant="flat"
                  :loading="esqueciLoading"
                  :disabled="!esqueciEmail"
                  @click="enviarEsqueci"
                >Enviar link</v-btn>
              </v-card-actions>
            </v-card>
          </v-dialog>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const email        = ref('')
const password     = ref('')
const showPassword = ref(false)
const loading      = ref(false)
const errorMessage = ref('')

// ── Esqueci minha senha ───────────────────────────────────────────────────────
const dialogEsqueci  = ref(false)
const esqueciEmail   = ref('')
const esqueciLoading = ref(false)
const esqueciSucesso = ref('')
const esqueciErro    = ref('')

const fecharEsqueci = () => {
  dialogEsqueci.value  = false
  esqueciEmail.value   = ''
  esqueciSucesso.value = ''
  esqueciErro.value    = ''
}

const enviarEsqueci = async () => {
  if (!esqueciEmail.value) return
  esqueciLoading.value = true
  esqueciErro.value    = ''
  try {
    const res = await fetch('/api/auth/forgot-password', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email: esqueciEmail.value }),
    })
    if (!res.ok) throw new Error('Erro ao enviar. Tente novamente.')
    esqueciSucesso.value = 'Se o e-mail estiver cadastrado, você receberá o link em breve. Verifique sua caixa de entrada.'
  } catch (e) {
    esqueciErro.value = e.message
  } finally {
    esqueciLoading.value = false
  }
}

const features = [
  { text: 'Disparo automático via WhatsApp' },
  { text: 'Relatórios detalhados da Superlógica' },
  { text: 'Templates personalizados com variáveis' },
  { text: 'Controle de campanhas e histórico' },
]

const handleLogin = async () => {
  loading.value      = true
  errorMessage.value = ''
  try {
    const res  = await fetch('/api/auth/login', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ email: email.value, password: password.value }),
    })
    // Parse seguro: evita crash se o backend retornar resposta vazia ou HTML de erro
    const text = await res.text()
    let data = {}
    try { data = JSON.parse(text) } catch (_) {
      throw new Error('Erro de comunicação com o servidor. Tente novamente.')
    }
    if (!res.ok) {
      const msgs = {
        Invalid_credentials:      'E-mail ou senha inválidos.',
        Account_pending_approval: 'Sua conta ainda aguarda aprovação do administrador.',
        Account_disabled:         'Sua conta está desativada. Fale com o administrador.',
      }
      // data.detail pode ser string ou array de objetos (erros de validação Pydantic)
      const errosPt = {
        'value is not a valid email address: An email address must have an @-sign.': 'Digite um e-mail válido.',
        'field required': 'Preencha todos os campos.',
        'value is not a valid email': 'Digite um e-mail válido.',
      }
      const detail = Array.isArray(data.detail)
        ? data.detail.map(e => {
            const msg = e.msg || JSON.stringify(e)
            return errosPt[msg] || msg
          }).join(' ')
        : (typeof data.detail === 'string' ? data.detail : null)
      throw new Error(msgs[detail] || msgs[data.detail] || detail || 'Erro ao fazer login.')
    }
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('is_admin', data.is_admin === true ? 'true' : 'false')
    localStorage.setItem('is_juridico', data.is_juridico === true ? 'true' : 'false')
    localStorage.setItem('is_financeiro', data.is_financeiro === true ? 'true' : 'false')
    localStorage.setItem('user_name', data.name || data.email || '')
    // Notifica o App.vue para mostrar a sidebar imediatamente (sem esperar reload)
    window.location.href = '/dashboard'
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* Cobre 100% da viewport sem espaços */
.auth-page {
  position: fixed;
  inset: 0;
  display: flex;
  overflow: hidden;
}

.auth-bg {
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  opacity: 0.3;
}
.bg-orb--1 {
  width: 480px; height: 480px;
  background: radial-gradient(circle, #059669 0%, transparent 70%);
  top: -120px; left: -80px;
}
.bg-orb--2 {
  width: 360px; height: 360px;
  background: radial-gradient(circle, #3b82f6 0%, transparent 70%);
  bottom: -60px; right: 32%;
  opacity: 0.18;
}
.bg-orb--3 {
  width: 280px; height: 280px;
  background: radial-gradient(circle, #34d399 0%, transparent 70%);
  top: 40%; left: 30%;
  opacity: 0.12;
}
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148,163,184,0.06) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148,163,184,0.06) 1px, transparent 1px);
  background-size: 44px 44px;
}

/* Layout dois painéis, altura total */
.auth-layout {
  position: relative;
  z-index: 1;
  display: flex;
  width: 100%;
  height: 100%;
}

/* Painel esquerdo: oculto em mobile, visível em ≥960px */
.auth-left {
  display: none;
  flex: 1;
  background: linear-gradient(145deg, #0f172a 0%, #1e293b 55%, #0c1a2e 100%);
  align-items: center;
  justify-content: center;
  padding: 60px 56px;
  position: relative;
  overflow: hidden;
}
@media (min-width: 960px) {
  .auth-left { display: flex; }
}
.auth-left::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url('/fundosistema.png');
  background-size: cover;
  background-position: center;
  opacity: 0.04;
}
.auth-left::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(52,211,153,0.3), transparent);
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
  width: 44px; height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #34d399 0%, #059669 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 0 0 1px rgba(52,211,153,0.25), 0 6px 20px rgba(5,150,105,0.45);
}
.brand-title {
  font-size: 18px;
  font-weight: 700;
  color: white;
  letter-spacing: -0.02em;
}
.brand-tagline {
  font-size: 11px;
  color: rgba(255,255,255,0.45);
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
.headline-accent { color: #34d399; }
.auth-desc {
  font-size: 15px;
  color: rgba(255,255,255,0.55);
  line-height: 1.65;
  margin-bottom: 36px;
}
.feature-list { display: flex; flex-direction: column; gap: 12px; }
.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(255,255,255,0.7);
  font-size: 14px;
}
.feature-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #34d399;
  flex-shrink: 0;
  box-shadow: 0 0 8px rgba(52,211,153,0.55);
}

/* Painel direito: largura fixa, altura 100% */
.auth-right {
  width: 460px;
  flex-shrink: 0;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 32px;
  background: #f8fafc;
  overflow-y: auto;
  border-left: 1px solid #e2e8f0;
}
/* Mobile: ocupa tela inteira */
@media (max-width: 959px) {
  .auth-right { width: 100%; }
}

.auth-card {
  width: 100%;
  max-width: 360px;
}

/* Logo mobile */
.mobile-brand {
  display: none;
  align-items: center;
  gap: 12px;
  margin-bottom: 36px;
}
@media (max-width: 959px) {
  .mobile-brand { display: flex; }
}

.form-header { margin-bottom: 28px; }
.form-title {
  font-size: 26px;
  font-weight: 700;
  color: #0f172a;
  letter-spacing: -0.02em;
  margin-bottom: 6px;
}
.form-subtitle {
  font-size: 14px;
  color: #6b7280;
}

.field-group { margin-bottom: 16px; }
.field-label {
  display: block;
  font-size: 13px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 6px;
}
.auth-field :deep(.v-field) { border-radius: 10px !important; }
.auth-field :deep(.v-field__outline__start) { border-radius: 10px 0 0 10px !important; }
.auth-field :deep(.v-field__outline__end) { border-radius: 0 10px 10px 0 !important; }

.submit-btn {
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  letter-spacing: 0.01em !important;
  box-shadow: 0 4px 16px rgba(5,150,105,0.3) !important;
  transition: box-shadow 0.2s, transform 0.15s !important;
}
.submit-btn:hover {
  box-shadow: 0 6px 22px rgba(5,150,105,0.42) !important;
  transform: translateY(-1px);
}
.forgot-link {
  font-size: 13px;
  color: #059669;
  text-decoration: none;
  opacity: 0.8;
  transition: opacity 0.15s;
}
.forgot-link:hover { opacity: 1; text-decoration: underline; }
</style>