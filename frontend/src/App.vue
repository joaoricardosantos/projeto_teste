<template>
  <v-app :theme="theme">

    <!-- ── Sidebar desktop (permanent, sempre montada) ── -->
    <v-navigation-drawer
      v-model="sidebarOpen"
      :rail="rail"
      permanent
      color="sidebar"
      width="240"
      rail-width="68"
    >
      <!-- Logo / Toggle -->
      <div class="sidebar-header" :class="{ 'rail-mode': rail }">
        <div class="logo-area" @click="rail = !rail">
          <div class="logo-icon">
            <v-icon size="22" color="white">mdi-home-city</v-icon>
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
          <v-icon size="18" color="rgba(255,255,255,0.5)">mdi-chevron-left</v-icon>
        </v-btn>
      </div>

      <v-divider style="border-color: rgba(255,255,255,0.08)" />

      <!-- Nav items — só mostra se autenticado -->
      <v-list v-if="isAuthenticated" nav density="compact" class="sidebar-nav px-2 py-3">
        <v-list-item
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          rounded="lg"
          class="nav-item mb-1"
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
        <v-divider style="border-color: rgba(255,255,255,0.08)" />
        <div class="sidebar-footer">
          <v-tooltip :text="theme === 'pratikaDark' ? 'Modo claro' : 'Modo escuro'" location="right">
            <template #activator="{ props }">
              <v-btn v-bind="props" icon variant="text" size="small" class="footer-btn" @click="toggleTheme">
                <v-icon size="18" color="rgba(255,255,255,0.6)">
                  {{ theme === 'pratikaDark' ? 'mdi-weather-sunny' : 'mdi-weather-night' }}
                </v-icon>
              </v-btn>
            </template>
          </v-tooltip>

          <template v-if="isAuthenticated">
            <v-tooltip v-if="rail" text="Sair" location="right">
              <template #activator="{ props }">
                <v-btn v-bind="props" icon variant="text" size="small" class="footer-btn" @click="logout">
                  <v-icon size="18" color="rgba(255,255,255,0.6)">mdi-logout</v-icon>
                </v-btn>
              </template>
            </v-tooltip>
            <template v-if="!rail">
              <v-spacer />
              <v-btn variant="text" size="small" class="footer-btn logout-btn" @click="logout">
                <v-icon size="16" class="mr-1">mdi-logout</v-icon>
                Sair
              </v-btn>
            </template>
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
import { ref, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'

const router = useRouter()
const route  = useRoute()

const rail         = ref(false)
const theme        = ref(localStorage.getItem('theme') || 'pratikaLight')
const isAuthenticated = ref(!!localStorage.getItem('access_token'))

// Sidebar aberta apenas quando autenticado
const sidebarOpen = ref(!!localStorage.getItem('access_token'))

// Sincroniza sidebarOpen com isAuthenticated
watch(isAuthenticated, (val) => {
  sidebarOpen.value = val
  // Esconde a sidebar na página de login
  if (!val) rail.value = false
})

// Fecha a sidebar visualmente na rota de login
watch(() => route.path, (path) => {
  if (path === '/') sidebarOpen.value = false
  else if (isAuthenticated.value) sidebarOpen.value = true
})

// Função global chamada pelo AuthView após login bem-sucedido
window.__setAuth = (val) => {
  isAuthenticated.value = val
  sidebarOpen.value = val
}

// Escuta mudanças em outras abas
window.addEventListener('storage', (e) => {
  if (e.key === 'access_token') {
    const authed = !!e.newValue
    isAuthenticated.value = authed
    sidebarOpen.value = authed
  }
})

const navItems = [
  { to: '/dashboard',  icon: 'mdi-view-dashboard-outline', label: 'Dashboard'        },
  { to: '/painel',     icon: 'mdi-send-outline',           label: 'Enviar Mensagens' },
  { to: '/templates',  icon: 'mdi-message-text-outline',   label: 'Templates'        },
  { to: '/relatorios', icon: 'mdi-file-chart-outline',     label: 'Relatórios'       },
  { to: '/admin',      icon: 'mdi-shield-account-outline', label: 'Administração'    },
]

const toggleTheme = () => {
  theme.value = theme.value === 'pratikaLight' ? 'pratikaDark' : 'pratikaLight'
  localStorage.setItem('theme', theme.value)
}

const logout = () => {
  localStorage.removeItem('access_token')
  isAuthenticated.value = false
  sidebarOpen.value = false
  router.push('/')
}
</script>

<style>
/* Sidebar */
.v-navigation-drawer.v-theme--pratikaLight .v-navigation-drawer__content,
.v-navigation-drawer.v-theme--pratikaDark .v-navigation-drawer__content {
  display: flex;
  flex-direction: column;
}

.sidebar-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 16px 16px;
  min-height: 72px;
}
.sidebar-header.rail-mode {
  justify-content: center;
  padding: 20px 8px 16px;
}
.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
  user-select: none;
}
.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  background: linear-gradient(135deg, #00a651 0%, #006837 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 4px 12px rgba(0, 168, 81, 0.35);
}
.logo-text {
  display: flex;
  flex-direction: column;
  line-height: 1.1;
}
.brand-name {
  font-size: 15px;
  font-weight: 700;
  color: white;
  letter-spacing: -0.02em;
}
.brand-sub {
  font-size: 10px;
  color: rgba(255,255,255,0.5);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}
.toggle-btn { opacity: 0.6; transition: opacity 0.2s; }
.toggle-btn:hover { opacity: 1; }

/* Nav items */
.sidebar-nav .nav-item {
  color: rgba(255,255,255,0.65) !important;
  transition: all 0.15s ease;
}
.sidebar-nav .nav-item:hover {
  color: white !important;
  background: rgba(255,255,255,0.08) !important;
}
.sidebar-nav .nav-item-active {
  color: white !important;
  background: rgba(0,168,81,0.25) !important;
}
.sidebar-nav .nav-item-active .v-icon {
  color: #4ade80 !important;
}

/* Footer */
.sidebar-footer {
  display: flex;
  align-items: center;
  padding: 10px 12px;
  gap: 4px;
  min-height: 52px;
}
.footer-btn {
  color: rgba(255,255,255,0.55) !important;
  transition: color 0.15s;
}
.footer-btn:hover { color: white !important; }
.logout-btn { font-size: 12px; }

/* Main */
.main-content {
  background: rgb(var(--v-theme-background)) !important;
}
.page-wrapper {
  min-height: 100%;
  padding: 28px;
}

/* Page transition */
.page-enter-active,
.page-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.page-enter-from { opacity: 0; transform: translateY(6px); }
.page-leave-to { opacity: 0; transform: translateY(-4px); }

/* Fade slide logo */
.fade-slide-enter-active,
.fade-slide-leave-active { transition: opacity 0.2s, transform 0.2s; }
.fade-slide-enter-from,
.fade-slide-leave-to { opacity: 0; transform: translateX(-6px); }

/* Login page — sem padding do v-main */
.v-main:has(.auth-page) { padding: 0 !important; }

/* Global */
.v-card { border-radius: 12px !important; }
.v-btn { letter-spacing: 0.01em !important; }
</style>