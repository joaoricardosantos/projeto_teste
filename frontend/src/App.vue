<template>
  <v-app :theme="theme">

    <!-- ── Sidebar ── -->
    <v-navigation-drawer
      v-if="isAuthenticated"
      v-model="drawer"
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
          icon
          variant="text"
          size="small"
          class="toggle-btn"
          @click.stop="rail = true"
        >
          <v-icon size="18" color="rgba(255,255,255,0.5)">mdi-chevron-left</v-icon>
        </v-btn>
      </div>

      <v-divider style="border-color: rgba(255,255,255,0.08)" />

      <!-- Nav Items -->
      <v-list nav density="compact" class="sidebar-nav px-2 py-3">
        <v-list-item
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.label"
          rounded="lg"
          class="nav-item mb-1"
          active-class="nav-item-active"
          :value="item.to"
        >
          <template #prepend>
            <v-icon :icon="item.icon" size="20" />
          </template>
          <template v-if="!rail" #append>
            <v-chip
              v-if="item.badge"
              size="x-small"
              :color="item.badgeColor || 'primary'"
              variant="flat"
              class="nav-badge"
            >{{ item.badge }}</v-chip>
          </template>
        </v-list-item>
      </v-list>

      <template #append>
        <v-divider style="border-color: rgba(255,255,255,0.08)" />
        <div class="sidebar-footer">
          <!-- Dark mode toggle -->
          <v-tooltip :text="theme === 'dark' ? 'Modo claro' : 'Modo escuro'" location="right">
            <template #activator="{ props }">
              <v-btn
                v-bind="props"
                icon
                variant="text"
                size="small"
                class="footer-btn"
                @click="toggleTheme"
              >
                <v-icon size="18" color="rgba(255,255,255,0.6)">
                  {{ theme === 'dark' ? 'mdi-weather-sunny' : 'mdi-weather-night' }}
                </v-icon>
              </v-btn>
            </template>
          </v-tooltip>

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
        </div>
      </template>
    </v-navigation-drawer>

    <!-- ── Top bar (mobile) ── -->
    <v-app-bar
      v-if="isAuthenticated"
      color="surface"
      elevation="0"
      border="b"
      class="top-bar d-md-none"
    >
      <v-app-bar-nav-icon @click="mobileDrawer = !mobileDrawer" />
      <div class="logo-icon ml-2">
        <v-icon size="20" color="white">mdi-home-city</v-icon>
      </div>
      <v-app-bar-title class="text-subtitle-1 font-weight-bold ml-2">Pratika</v-app-bar-title>
    </v-app-bar>

    <!-- Mobile drawer -->
    <v-navigation-drawer
      v-if="isAuthenticated"
      v-model="mobileDrawer"
      temporary
      color="sidebar"
      width="240"
    >
      <div class="sidebar-header">
        <div class="logo-area">
          <div class="logo-icon">
            <v-icon size="22" color="white">mdi-home-city</v-icon>
          </div>
          <div class="logo-text">
            <span class="brand-name">Pratika</span>
            <span class="brand-sub">Cobranças</span>
          </div>
        </div>
      </div>
      <v-divider style="border-color: rgba(255,255,255,0.08)" />
      <v-list nav density="compact" class="sidebar-nav px-2 py-3">
        <v-list-item
          v-for="item in navItems"
          :key="item.to"
          :to="item.to"
          :prepend-icon="item.icon"
          :title="item.label"
          rounded="lg"
          class="nav-item mb-1"
          active-class="nav-item-active"
          @click="mobileDrawer = false"
        >
          <template #prepend>
            <v-icon :icon="item.icon" size="20" />
          </template>
        </v-list-item>
      </v-list>
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
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'

const route  = useRoute()
const router = useRouter()

const rail         = ref(false)
const mobileDrawer = ref(false)
const theme        = ref(localStorage.getItem('theme') || 'pratikaLight')

const isAuthenticated = computed(() => route.name !== 'Auth')

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
  router.push('/')
}
</script>

<style>
/* ── Sidebar ── */
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
  color: rgba(255, 255, 255, 0.5);
  letter-spacing: 0.05em;
  text-transform: uppercase;
}

.toggle-btn {
  opacity: 0.6;
  transition: opacity 0.2s;
}
.toggle-btn:hover { opacity: 1; }

/* Nav items */
.sidebar-nav .nav-item {
  color: rgba(255, 255, 255, 0.65) !important;
  transition: all 0.15s ease;
}
.sidebar-nav .nav-item:hover {
  color: white !important;
  background: rgba(255, 255, 255, 0.08) !important;
}
.sidebar-nav .nav-item-active {
  color: white !important;
  background: rgba(0, 168, 81, 0.25) !important;
}
.sidebar-nav .nav-item-active .v-icon {
  color: #4ade80 !important;
}
.sidebar-nav .nav-item .v-list-item__content .v-list-item-title {
  font-size: 13.5px;
  font-weight: 500;
}
.nav-badge {
  font-size: 10px !important;
  height: 18px !important;
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
  color: rgba(255, 255, 255, 0.55) !important;
  transition: color 0.15s;
}
.footer-btn:hover { color: white !important; }
.logout-btn {
  font-size: 12px;
  letter-spacing: 0.02em;
}

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
.page-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}
.page-enter-from {
  opacity: 0;
  transform: translateY(6px);
}
.page-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}

/* Fade slide (logo text) */
.fade-slide-enter-active,
.fade-slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
}
.fade-slide-enter-from,
.fade-slide-leave-to {
  opacity: 0;
  transform: translateX(-6px);
}

/* Top bar */
.top-bar {
  border-color: rgba(0,0,0,0.06) !important;
}

/* Remove background image on auth page */
.v-main:has(.auth-page) {
  padding: 0 !important;
}

/* Global improvements */
.v-card {
  border-radius: 12px !important;
}
.v-btn {
  letter-spacing: 0.01em !important;
}
</style>