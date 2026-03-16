<template>
  <div class="auth-page">

    <div class="auth-bg">
      <div class="bg-orb bg-orb--1" />
      <div class="bg-orb bg-orb--2" />
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
            Redefinição<br>
            de <span class="headline-accent">senha</span>
          </h1>
          <p class="auth-desc">
            Crie uma nova senha segura para sua conta.
          </p>
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
            <div class="brand-title" style="color: #006837;">Pratika</div>
          </div>

          <!-- Token inválido -->
          <div v-if="tokenInvalido" class="text-center">
            <v-icon size="56" color="error" class="mb-4">mdi-link-off</v-icon>
            <h2 class="form-title mb-2">Link inválido ou expirado</h2>
            <p class="text-body-2 text-medium-emphasis mb-6">
              Este link de recuperação já foi usado ou expirou.<br>
              Solicite um novo link na tela de login.
            </p>
            <v-btn color="primary" variant="flat" class="submit-btn" @click="router.push('/')">
              Voltar ao login
            </v-btn>
          </div>

          <!-- Sucesso -->
          <div v-else-if="sucesso" class="text-center">
            <v-icon size="56" color="success" class="mb-4">mdi-check-circle-outline</v-icon>
            <h2 class="form-title mb-2">Senha redefinida!</h2>
            <p class="text-body-2 text-medium-emphasis mb-6">
              Sua senha foi alterada com sucesso.<br>
              Você já pode entrar com a nova senha.
            </p>
            <v-btn color="primary" variant="flat" class="submit-btn" @click="router.push('/')">
              Ir para o login
            </v-btn>
          </div>

          <!-- Form redefinição -->
          <div v-else>
            <div class="form-header">
              <h2 class="form-title">Nova senha</h2>
              <p class="form-subtitle">Digite e confirme sua nova senha</p>
            </div>

            <div class="field-group">
              <label class="field-label">Nova senha</label>
              <v-text-field
                v-model="novaSenha"
                :type="showNova ? 'text' : 'password'"
                placeholder="••••••••"
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-lock-outline"
                :append-inner-icon="showNova ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
                hide-details="auto"
                class="auth-field"
                :disabled="loading"
                @click:append-inner="showNova = !showNova"
              />
            </div>

            <div class="field-group">
              <label class="field-label">Confirmar senha</label>
              <v-text-field
                v-model="confirmarSenha"
                :type="showConfirmar ? 'text' : 'password'"
                placeholder="••••••••"
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-lock-check-outline"
                :append-inner-icon="showConfirmar ? 'mdi-eye-off-outline' : 'mdi-eye-outline'"
                hide-details="auto"
                class="auth-field"
                :disabled="loading"
                @click:append-inner="showConfirmar = !showConfirmar"
                @keyup.enter="redefinir"
              />
            </div>

            <v-alert
              v-if="erro"
              type="error"
              variant="tonal"
              density="compact"
              class="mb-4"
              closable
              @click:close="erro = ''"
            >{{ erro }}</v-alert>

            <v-btn
              block
              size="large"
              color="primary"
              class="submit-btn mt-2"
              :loading="loading"
              :disabled="!novaSenha || !confirmarSenha"
              @click="redefinir"
            >
              <v-icon start>mdi-lock-reset</v-icon>
              Redefinir senha
            </v-btn>

            <div class="text-center mt-4">
              <a href="#" class="forgot-link" @click.prevent="router.push('/')">
                Voltar ao login
              </a>
            </div>
          </div>

        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router        = useRouter()
const route         = useRoute()
const token         = ref('')
const novaSenha     = ref('')
const confirmarSenha = ref('')
const showNova      = ref(false)
const showConfirmar = ref(false)
const loading       = ref(false)
const erro          = ref('')
const sucesso       = ref(false)
const tokenInvalido = ref(false)

onMounted(() => {
  token.value = route.query.token || ''
  if (!token.value) tokenInvalido.value = true
})

const redefinir = async () => {
  erro.value = ''

  if (novaSenha.value.length < 6) {
    erro.value = 'A senha deve ter pelo menos 6 caracteres.'
    return
  }
  if (novaSenha.value !== confirmarSenha.value) {
    erro.value = 'As senhas não coincidem.'
    return
  }

  loading.value = true
  try {
    const res = await fetch('/api/auth/reset-password', {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify({ token: token.value, new_password: novaSenha.value }),
    })
    const text = await res.text()
    let data = {}
    try { data = JSON.parse(text) } catch (_) {}

    if (!res.ok) {
      if (data.detail === 'Invalid_or_expired_token') {
        tokenInvalido.value = true
      } else {
        erro.value = data.detail || 'Erro ao redefinir senha. Tente novamente.'
      }
      return
    }
    sucesso.value = true
  } catch (e) {
    erro.value = 'Erro de comunicação com o servidor.'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
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
.auth-layout {
  position: relative;
  z-index: 1;
  display: flex;
  width: 100%;
  height: 100%;
}
.auth-left {
  display: none;
  flex: 1;
  background: linear-gradient(150deg, #0f1d14 0%, #1a3a23 60%, #0a2e12 100%);
  align-items: center;
  justify-content: center;
  padding: 60px 56px;
  position: relative;
  overflow: hidden;
}
@media (min-width: 960px) { .auth-left { display: flex; } }
.auth-left::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image: url('/fundosistema.png');
  background-size: cover;
  background-position: center;
  opacity: 0.06;
}
.auth-left-content { position: relative; z-index: 1; max-width: 420px; }
.brand-badge { display: flex; align-items: center; gap: 12px; margin-bottom: 52px; }
.brand-icon {
  width: 44px; height: 44px;
  border-radius: 12px;
  background: linear-gradient(135deg, #00a651 0%, #006837 100%);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 6px 20px rgba(0,168,81,0.4);
}
.brand-title { font-size: 18px; font-weight: 700; color: white; letter-spacing: -0.02em; }
.brand-tagline { font-size: 11px; color: rgba(255,255,255,0.45); text-transform: uppercase; letter-spacing: 0.1em; }
.auth-headline { font-size: 40px; font-weight: 800; color: white; line-height: 1.15; letter-spacing: -0.03em; margin-bottom: 20px; }
.headline-accent { color: #4ade80; }
.auth-desc { font-size: 15px; color: rgba(255,255,255,0.55); line-height: 1.65; }
.auth-right {
  width: 460px; flex-shrink: 0; height: 100%;
  display: flex; align-items: center; justify-content: center;
  padding: 40px 32px;
  background: white;
  overflow-y: auto;
}
@media (max-width: 959px) { .auth-right { width: 100%; } }
.auth-card { width: 100%; max-width: 360px; }
.mobile-brand { display: none; align-items: center; gap: 12px; margin-bottom: 36px; }
@media (max-width: 959px) { .mobile-brand { display: flex; } }
.form-header { margin-bottom: 28px; }
.form-title { font-size: 26px; font-weight: 700; color: #0f1d14; letter-spacing: -0.02em; margin-bottom: 6px; }
.form-subtitle { font-size: 14px; color: #6b7280; }
.field-group { margin-bottom: 16px; }
.field-label { display: block; font-size: 13px; font-weight: 500; color: #374151; margin-bottom: 6px; }
.auth-field :deep(.v-field) { border-radius: 10px !important; }
.submit-btn {
  border-radius: 10px !important;
  font-weight: 600 !important;
  font-size: 14px !important;
  letter-spacing: 0.01em !important;
  box-shadow: 0 4px 16px rgba(0,104,55,0.3) !important;
}
.submit-btn:hover {
  box-shadow: 0 6px 20px rgba(0,104,55,0.4) !important;
  transform: translateY(-1px);
}
.forgot-link { font-size: 13px; color: #006837; text-decoration: none; opacity: 0.8; }
.forgot-link:hover { opacity: 1; text-decoration: underline; }
</style>