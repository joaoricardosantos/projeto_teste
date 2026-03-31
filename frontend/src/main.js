import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'
import '@mdi/font/css/materialdesignicons.css'

const vuetify = createVuetify({
  components,
  directives,
  theme: {
    defaultTheme: localStorage.getItem('theme') || 'pratikaLight',
    themes: {
      pratikaLight: {
        dark: false,
        colors: {
          // Brand — emerald moderno
          primary: '#059669',
          'primary-darken-1': '#047857',
          secondary: '#10b981',
          accent: '#34d399',

          // UI — slate limpo
          background: '#f1f5f9',
          surface: '#ffffff',
          sidebar: '#0f172a',   // slate-900

          // Status
          error: '#ef4444',
          warning: '#f59e0b',
          info: '#3b82f6',
          success: '#10b981',

          // Text helpers
          'on-surface': '#0f172a',
          'on-background': '#64748b',
        },
        variables: {
          'border-color': '#e2e8f0',
          'border-opacity': 1,
          'high-emphasis-opacity': 0.9,
          'medium-emphasis-opacity': 0.6,
          'hover-opacity': 0.04,
          'focus-opacity': 0.1,
          'selected-opacity': 0.08,
          'activated-opacity': 0.1,
          'pressed-opacity': 0.14,
          'dragged-opacity': 0.08,
          'theme-overlay-multiplier': 1,
          'disabled-opacity': 0.38,
          'idle-opacity': 0.04,
          'kbd-background-color': '#1e293b',
          'kbd-color': '#f8fafc',
          'code-background-color': '#f8fafc',
        },
      },
      pratikaDark: {
        dark: true,
        colors: {
          // Brand
          primary: '#34d399',
          'primary-darken-1': '#10b981',
          secondary: '#10b981',
          accent: '#6ee7b7',

          // UI
          background: '#0f172a',
          surface: '#1e293b',
          sidebar: '#020617',   // slate-950

          // Status
          error: '#f87171',
          warning: '#fbbf24',
          info: '#60a5fa',
          success: '#34d399',

          // Text helpers
          'on-surface': '#f1f5f9',
          'on-background': '#94a3b8',
        },
        variables: {
          'border-color': '#334155',
          'border-opacity': 1,
        },
      },
    },
  },
  defaults: {
    VCard: {
      elevation: 0,
      border: true,
    },
    VBtn: {
      style: 'font-weight: 500; letter-spacing: 0.01em;',
    },
    VTextField: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VSelect: {
      variant: 'outlined',
      density: 'comfortable',
    },
    VTextarea: {
      variant: 'outlined',
      density: 'comfortable',
    },
  },
})

const app = createApp(App)

app.use(router)
app.use(vuetify)

app.mount('#app')