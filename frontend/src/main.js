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
          // Brand
          primary: '#006837',
          'primary-darken-1': '#004d28',
          secondary: '#00a651',
          accent: '#4ade80',

          // UI
          background: '#F0F2F5',
          surface: '#FFFFFF',
          sidebar: '#0f1d14',  // verde quase preto para a sidebar

          // Status
          error: '#e53935',
          warning: '#f59e0b',
          info: '#0ea5e9',
          success: '#16a34a',

          // Text helpers
          'on-surface': '#1a2e1c',
          'on-background': '#374151',
        },
        variables: {
          'border-color': '#e5e7eb',
          'border-opacity': 1,
          'high-emphasis-opacity': 0.87,
          'medium-emphasis-opacity': 0.55,
          'hover-opacity': 0.04,
          'focus-opacity': 0.12,
          'selected-opacity': 0.08,
          'activated-opacity': 0.12,
          'pressed-opacity': 0.16,
          'dragged-opacity': 0.08,
          'theme-overlay-multiplier': 1,
          'disabled-opacity': 0.38,
          'idle-opacity': 0.04,
          'kbd-background-color': '#212529',
          'kbd-color': '#FFFFFF',
          'code-background-color': '#f3f4f6',
        },
      },
      pratikaDark: {
        dark: true,
        colors: {
          // Brand
          primary: '#4ade80',
          'primary-darken-1': '#22c55e',
          secondary: '#00a651',
          accent: '#86efac',

          // UI
          background: '#0d1117',
          surface: '#161b22',
          sidebar: '#0a0f0b',

          // Status
          error: '#f87171',
          warning: '#fbbf24',
          info: '#38bdf8',
          success: '#4ade80',

          // Text helpers
          'on-surface': '#e6edf3',
          'on-background': '#c9d1d9',
        },
        variables: {
          'border-color': '#30363d',
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