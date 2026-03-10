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
    defaultTheme: 'pratikaTheme',
    themes: {
      pratikaTheme: {
        dark: false,
        colors: {
          primary: '#006837', // verde principal do logo
          secondary: '#004225', // verde mais escuro de apoio
          background: '#F5F5F5',
        },
      },
    },
  },
})

const app = createApp(App)

app.use(router)
app.use(vuetify)

app.mount('#app')