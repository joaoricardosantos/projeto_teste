<template>
  <v-app :theme="theme">

    <!-- ── App bar mobile ── -->
    <v-app-bar
      v-if="isAuthenticated && isMobile"
      color="sidebar"
      elevation="0"
      height="56"
    >
      <v-btn icon variant="text" @click="sidebarOpen = !sidebarOpen">
        <v-icon color="rgba(148,163,184,0.9)">mdi-menu</v-icon>
      </v-btn>
      <div class="d-flex align-center" style="gap:8px; margin-left:4px;">
        <div class="logo-icon" style="width:28px;height:28px;border-radius:7px;">
          <span class="logo-letter" style="font-size:12px;">P</span>
        </div>
        <span class="brand-name">Pratika</span>
      </div>
      <template #append>
        <v-btn icon variant="text" @click="toggleTheme">
          <v-icon size="18" color="rgba(148,163,184,0.7)">{{ theme === 'pratikaDark' ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
        </v-btn>
      </template>
    </v-app-bar>

    <!-- ── Sidebar (desktop: permanent rail; mobile: temporary overlay) ── -->
    <v-navigation-drawer
      v-if="isAuthenticated"
      v-model="sidebarOpen"
      :rail="rail && !isMobile"
      :permanent="!isMobile"
      :temporary="isMobile"
      color="sidebar"
      width="240"
      rail-width="68"
    >
      <!-- Logo / Toggle -->
      <div class="sidebar-header" :class="{ 'rail-mode': rail }">
        <div class="logo-area" @click="rail = !rail">
          <div class="logo-icon">
            <span class="logo-letter">P</span>
          </div>
          <Transition name="fade-slide">
            <div v-if="!rail" class="logo-text">
              <span class="brand-name">Pratika</span>
              <span class="brand-sub">Cobranças</span>
            </div>
          </Transition>
        </div>
        <v-btn
          v-if="!rail"
          icon variant="text" size="small"
          class="toggle-btn"
          @click.stop="rail = true"
        >
          <v-icon size="18" color="rgba(148,163,184,0.6)">mdi-chevron-left</v-icon>
        </v-btn>
      </div>

      <v-divider style="border-color: rgba(255,255,255,0.08)" />

      <!-- Nav items — só mostra se autenticado -->
      <v-list v-if="isAuthenticated" nav density="comfortable" class="sidebar-nav px-2 py-3">
        <v-list-item
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          rounded="lg"
          class="nav-item mb-2"
          active-class="nav-item-active"
          :value="item.to"
        >
          <template #prepend>
            <v-icon :icon="item.icon" size="20" />
          </template>
          <template #title>
            <span v-if="!rail">{{ item.label }}</span>
          </template>
        </v-list-item>
      </v-list>

      <template #append>
        <v-divider style="border-color: rgba(255,255,255,0.06)" />

        <!-- Usuário + ações -->
        <div class="sidebar-footer" :class="{ 'rail-mode': rail }">
          <template v-if="!rail">
            <div class="user-info">
              <div class="user-avatar">
                <span>{{ userInitials }}</span>
              </div>
              <div class="user-details">
                <span class="user-name">{{ userName }}</span>
                <span class="user-role">{{ userRole }}</span>
              </div>
            </div>
            <div class="footer-actions">
              <v-tooltip :text="theme === 'pratikaDark' ? 'Modo claro' : 'Modo escuro'" location="top">
                <template #activator="{ props }">
                  <v-btn v-bind="props" icon variant="text" size="x-small" class="footer-btn" @click="toggleTheme">
                    <v-icon size="16">{{ theme === 'pratikaDark' ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
              <v-tooltip text="Sair" location="top">
                <template #activator="{ props }">
                  <v-btn v-bind="props" icon variant="text" size="x-small" class="footer-btn" @click="logout">
                    <v-icon size="16">mdi-logout</v-icon>
                  </v-btn>
                </template>
              </v-tooltip>
            </div>
          </template>

          <template v-else>
            <v-tooltip :text="theme === 'pratikaDark' ? 'Modo claro' : 'Modo escuro'" location="right">
              <template #activator="{ props }">
                <v-btn v-bind="props" icon variant="text" size="small" class="footer-btn" @click="toggleTheme">
                  <v-icon size="16">{{ theme === 'pratikaDark' ? 'mdi-weather-sunny' : 'mdi-weather-night' }}</v-icon>
                </v-btn>
              </template>
            </v-tooltip>
            <v-tooltip text="Sair" location="right">
              <template #activator="{ props }">
                <v-btn v-bind="props" icon variant="text" size="small" class="footer-btn" @click="logout">
                  <v-icon size="16">mdi-logout</v-icon>
                </v-btn>
              </template>
            </v-tooltip>
          </template>
        </div>
      </template>
    </v-navigation-drawer>

    <!-- ── Main ── -->
    <v-main class="main-content">
      <div class="page-wrapper">
        <router-view v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" />
          </Transition>
        </router-view>
      </div>
    </v-main>

  </v-app>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { useCondominios } from './composables/useCondominios.js'
import { useRouter, useRoute } from 'vue-router'
import { useDisplay } from 'vuetify'

const router = useRouter()
const route  = useRoute()
const { mobile: isMobile } = useDisplay()

const rail         = ref(false)
const theme        = ref(
  // Tela de login sempre usa tema claro
  route.meta.requiresAuth ? (localStorage.getItem('theme') || 'pratikaLight') : 'pratikaLight'
)
const sidebarOpen  = ref(true)

// Usa a rota como fonte de verdade — sidebar só aparece em rotas autenticadas
const isAuthenticated = computed(() => !!route.meta.requiresAuth)

// sidebar atualiza via isAuthenticated (rota) e isAdminUser (localStorage)

// Logout em outra aba redireciona para login
window.addEventListener('storage', (e) => {
  if (e.key === 'access_token' && !e.newValue) router.push('/')
})

// Fecha drawer no mobile ao navegar
watch(() => route.path, () => {
  if (isMobile.value) sidebarOpen.value = false
})

// Sincroniza drawer com breakpoint
watch(isMobile, (mobile) => {
  sidebarOpen.value = !mobile
})

// Atualiza tema ao mudar de rota (login sempre claro, resto salvo)
watch(() => route.meta.requiresAuth, (authed) => {
  if (!authed) {
    theme.value = 'pratikaLight'
  } else {
    theme.value = localStorage.getItem('theme') || 'pratikaLight'
  }
})

const isAdmin      = computed(() => localStorage.getItem('is_admin')      === 'true')
const isJuridico   = computed(() => localStorage.getItem('is_juridico')   === 'true')
const isFinanceiro = computed(() => localStorage.getItem('is_financeiro') === 'true')

const userName     = computed(() => localStorage.getItem('user_name') || 'Usuário')
const userInitials = computed(() => {
  const n = userName.value.trim().split(' ')
  return n.length >= 2 ? (n[0][0] + n[n.length - 1][0]).toUpperCase() : n[0].slice(0, 2).toUpperCase()
})
const userRole = computed(() => {
  if (isAdmin.value)      return 'Administrador'
  if (isJuridico.value)   return 'Jurídico'
  if (isFinanceiro.value) return 'Financeiro'
  return 'Usuário'
})

const allNavItems = [
  { to: '/dashboard',    icon: 'mdi-view-dashboard-outline', label: 'Dashboard',        adminOnly: false, juridicoAllowed: true,  financeiroAllowed: true,  usuarioAllowed: false },
  { to: '/painel',       icon: 'mdi-send-outline',           label: 'Enviar Mensagens', adminOnly: false, juridicoAllowed: false, financeiroAllowed: false, usuarioAllowed: false },
  { to: '/templates',    icon: 'mdi-message-text-outline',   label: 'Templates',        adminOnly: false, juridicoAllowed: false, financeiroAllowed: false, usuarioAllowed: false },
  { to: '/sheets',       icon: 'mdi-google-spreadsheet',     label: 'Google Sheets',    adminOnly: false, juridicoAllowed: false, financeiroAllowed: true,  usuarioAllowed: false },
  { to: '/financeiro',   icon: 'mdi-currency-usd',           label: 'Financeiro',       adminOnly: true,  juridicoAllowed: false, financeiroAllowed: true,  usuarioAllowed: false },
  { to: '/levantamento', icon: 'mdi-magnify-scan',           label: 'Levantamento',     adminOnly: true,  juridicoAllowed: true,  financeiroAllowed: false, usuarioAllowed: false },
  { to: '/relatorios',   icon: 'mdi-file-chart-outline',     label: 'Relatórios',       adminOnly: true,  juridicoAllowed: true,  financeiroAllowed: false, usuarioAllowed: false },
  { to: '/juridico',     icon: 'mdi-gavel',                  label: 'Jurídico',         adminOnly: false, juridicoAllowed: true,  financeiroAllowed: false, usuarioAllowed: false },
  { to: '/execucao',     icon: 'mdi-file-document-edit-outline', label: 'Execução',     adminOnly: false, juridicoAllowed: true,  financeiroAllowed: false, usuarioAllowed: false },
  { to: '/agenda',       icon: 'mdi-calendar-month-outline', label: 'Agenda',           adminOnly: false, juridicoAllowed: true,  financeiroAllowed: true,  usuarioAllowed: true  },
  { to: '/sindicos',     icon: 'mdi-account-group-outline',  label: 'Sindicos',         adminOnly: false, juridicoAllowed: false, financeiroAllowed: true,  usuarioAllowed: false },
  { to: '/admin',        icon: 'mdi-shield-account-outline', label: 'Administração',    adminOnly: true,  juridicoAllowed: false, financeiroAllowed: false, usuarioAllowed: false },
]

const navItems = computed(() => {
  const isUsuario = !isAdmin.value && !isJuridico.value && !isFinanceiro.value
  return allNavItems.filter(item => {
    if (isUsuario)          return item.usuarioAllowed
    if (isJuridico.value)   return item.juridicoAllowed
    if (isFinanceiro.value) return item.financeiroAllowed
    return !item.adminOnly || isAdmin.value
  })
})

const toggleTheme = () => {
  theme.value = theme.value === 'pratikaLight' ? 'pratikaDark' : 'pratikaLight'
  localStorage.setItem('theme', theme.value)
}

const { invalidarCondominios } = useCondominios()

const logout = () => {
  localStorage.removeItem('access_token')
  localStorage.removeItem('is_admin')
  localStorage.removeItem('is_juridico')
  localStorage.removeItem('is_financeiro')
  localStorage.removeItem('user_name')
  invalidarCondominios()
  sidebarOpen.value = false
  router.push('/')
}
</script>

<style>
/* ── Sidebar container ── */
.v-navigation-drawer.v-theme--pratikaLight .v-navigation-drawer__content,
.v-navigation-drawer.v-theme--pratikaDark .v-navigation-drawer__content {
  display: flex;
  flex-direction: column;
}

/* ── Header ── */
.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 14px 14px;
  min-height: 68px;
}
.sidebar-header.rail-mode {
  justify-content: center;
  padding: 18px 8px 14px;
}
.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}
.logo-icon {
  width: 34px;
  height: 34px;
  border-radius: 9px;
  background: linear-gradient(135deg, #34d399 0%, #059669 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 0 0 1px rgba(52,211,153,0.3), 0 4px 14px rgba(5,150,105,0.45);
}
.logo-letter {
  font-size: 15px;
  font-weight: 800;
  color: white;
  letter-spacing: -0.03em;
  line-height: 1;
}
.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.15;
}
.brand-name {
  font-size: 14px;
  font-weight: 700;
  color: #f8fafc;
  letter-spacing: -0.02em;
}
.brand-sub {
  font-size: 10px;
  color: rgba(148,163,184,0.7);
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.toggle-btn { opacity: 0.5; transition: opacity 0.2s; }
.toggle-btn:hover { opacity: 1; }

/* ── Nav items ── */
.sidebar-nav .nav-item {
  color: rgba(148,163,184,0.9) !important;
  transition: all 0.15s ease;
  position: relative;
  min-height: 44px !important;
}
.sidebar-nav .nav-item:hover {
  color: #f8fafc !important;
  background: rgba(255,255,255,0.06) !important;
}
.sidebar-nav .nav-item-active {
  color: #f8fafc !important;
  background: rgba(52,211,153,0.1) !important;
}
.sidebar-nav .nav-item-active::before {
  content: '';
  position: absolute;
  left: 0;
  top: 6px;
  bottom: 6px;
  width: 3px;
  border-radius: 0 3px 3px 0;
  background: #34d399;
}
.sidebar-nav .nav-item-active .v-icon {
  color: #34d399 !important;
}

/* ── Footer ── */
.sidebar-footer {
  padding: 10px 12px 14px;
  min-height: 60px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.sidebar-footer.rail-mode {
  flex-direction: column;
  gap: 4px;
  justify-content: center;
}

/* Usuário */
.user-info {
  display: flex;
  align-items: center;
  gap: 9px;
  min-width: 0;
  flex: 1;
}
.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
  border: 1px solid rgba(148,163,184,0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.user-avatar span {
  font-size: 11px;
  font-weight: 700;
  color: #94a3b8;
  letter-spacing: 0.02em;
}
.user-details {
  display: flex;
  flex-direction: column;
  line-height: 1.2;
  min-width: 0;
}
.user-name {
  font-size: 12px;
  font-weight: 600;
  color: #e2e8f0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 110px;
}
.user-role {
  font-size: 10px;
  color: rgba(148,163,184,0.6);
}
.footer-actions {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}
.footer-btn {
  color: rgba(148,163,184,0.6) !important;
  transition: color 0.15s;
}
.footer-btn:hover { color: #f8fafc !important; }

/* ── Main ── */
.main-content {
  background: rgb(var(--v-theme-background)) !important;
}
.page-wrapper {
  min-height: 100%;
  padding: 28px;
}

/* ── Page transition ── */
.page-enter-active,
.page-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.page-enter-from { opacity: 0; transform: translateY(5px); }
.page-leave-to   { opacity: 0; transform: translateY(-3px); }

/* ── Fade slide logo ── */
.fade-slide-enter-active,
.fade-slide-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-slide-enter-from,
.fade-slide-leave-to { opacity: 0; transform: translateX(-6px); }

/* ── Login page — sem padding do v-main ── */
.v-main:has(.auth-page) { padding: 0 !important; }

/* ── Mobile ── */
@media (max-width: 959px) {
  .page-wrapper { padding: 16px; }
}

/* ── Global ── */
.v-card { border-radius: 14px !important; }
.v-btn  { letter-spacing: 0.01em !important; }

/* ──────────────────────────────────────────────────────────
   Page headers — padrão global para todos os views
   ────────────────────────────────────────────────────────── */
.page-icon {
  width: 40px !important; height: 40px !important;
  border-radius: 11px !important;
  background: linear-gradient(135deg, #34d399 0%, #059669 100%) !important;
  display: flex !important; align-items: center !important;
  justify-content: center !important; flex-shrink: 0 !important;
  box-shadow: 0 0 0 1px rgba(52,211,153,0.2), 0 4px 12px rgba(5,150,105,0.28) !important;
  margin-right: 8px;
}
.page-title {
  font-size: 1.15rem !important; font-weight: 700 !important;
  letter-spacing: -0.02em !important; line-height: 1.3 !important; margin: 0 !important;
}
.page-subtitle { font-size: 0.8rem !important; opacity: .55 !important; margin: 2px 0 0 !important; }

/* ──────────────────────────────────────────────────────────
   Section cards — substituição do banner verde por design moderno
   ────────────────────────────────────────────────────────── */
.section-header {
  background: #f8fafc !important;
  border-bottom: 1px solid #e2e8f0 !important;
  border-left: 3px solid #34d399 !important;
  padding: 13px 20px !important;
}
.section-badge {
  background: linear-gradient(135deg, #34d399, #059669) !important;
  box-shadow: 0 2px 8px rgba(5,150,105,0.3) !important;
  border-radius: 8px !important;
  color: white !important;
  font-weight: 700 !important;
}
.section-title    { color: #0f172a !important; }
.section-subtitle { color: #64748b !important; }

.v-theme--pratikaDark .section-header {
  background: #1e293b !important;
  border-bottom-color: #334155 !important;
}
.v-theme--pratikaDark .section-title    { color: #f1f5f9 !important; }
.v-theme--pratikaDark .section-subtitle { color: #94a3b8 !important; }

/* ── Template preview ── */
.template-preview { background: #f1f5f9 !important; }
.v-theme--pratikaDark .template-preview { background: #0f172a !important; }

/* ── Templates dark mode ── */
.v-theme--pratikaDark .template-card-header {
  background: #1e293b !important;
  border-bottom-color: #334155 !important;
}
.v-theme--pratikaDark .template-name  { color: #f1f5f9 !important; }
.v-theme--pratikaDark .dialog-header  {
  background: #1e293b !important;
  border-bottom-color: #334155 !important;
  color: #f1f5f9 !important;
}
</style>