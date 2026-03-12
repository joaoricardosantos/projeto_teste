<template>
  <v-container>
    <v-row class="mb-6">
      <v-col cols="12">
        <h1 class="text-h5 font-weight-bold mb-1">Relatórios de inadimplência</h1>
        <p class="text-body-2 text-medium-emphasis">
          Gere um Excel com abas <strong>Resumo</strong> e <strong>Detalhado</strong> por condomínio.
          Deixe os filtros em branco para varrer todos os condomínios com a data de hoje.
        </p>
      </v-col>
    </v-row>

    <v-card elevation="4" class="pa-6">
      <v-row align="center" :gutter="4">
        <!-- ID do condomínio -->
        <v-col cols="12" sm="4">
          <v-text-field
            v-model.number="idCondominio"
            label="ID do condomínio (opcional)"
            type="number"
            variant="outlined"
            density="comfortable"
            clearable
            hide-details="auto"
            hint="Deixe em branco para todos"
            persistent-hint
          />
        </v-col>

        <!-- Data de posição -->
        <v-col cols="12" sm="4">
          <v-text-field
            v-model="dataPosicao"
            label="Data de posição (opcional)"
            type="date"
            variant="outlined"
            density="comfortable"
            clearable
            hide-details="auto"
            hint="Deixe em branco para hoje"
            persistent-hint
          />
        </v-col>

        <!-- Botão exportar -->
        <v-col cols="12" sm="4">
          <v-btn
            color="primary"
            block
            size="large"
            prepend-icon="mdi-microsoft-excel"
            :loading="isExporting"
            @click="exportDefaulters"
          >
            Exportar Excel
          </v-btn>
        </v-col>
      </v-row>

      <!-- Alertas -->
      <v-alert v-if="errorMessage" type="error" class="mt-5" closable @click:close="errorMessage = ''">
        {{ errorMessage }}
      </v-alert>

      <v-alert v-if="successMessage" type="success" class="mt-5" closable @click:close="successMessage = ''">
        {{ successMessage }}
      </v-alert>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'

const isExporting = ref(false)
const errorMessage = ref('')
const successMessage = ref('')

const idCondominio = ref(null)
const dataPosicao = ref('')

const exportDefaulters = async () => {
  isExporting.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const token = localStorage.getItem('access_token')

    // Monta query string apenas com parâmetros preenchidos
    const params = new URLSearchParams()
    if (idCondominio.value) {
      params.append('id_condominio', idCondominio.value)
    }
    if (dataPosicao.value) {
      // Converte YYYY-MM-DD (input date) → DD/MM/YYYY (formato da API)
      const [ano, mes, dia] = dataPosicao.value.split('-')
      params.append('data_posicao', `${dia}/${mes}/${ano}`)
    }

    const query = params.toString() ? `?${params.toString()}` : ''
    const response = await fetch(`/api/admin/export-defaulters${query}`, {
      method: 'GET',
      headers: { Authorization: `Bearer ${token}` },
    })

    if (response.status === 204) {
      errorMessage.value = 'Nenhum inadimplente encontrado para os filtros informados.'
      return
    }

    if (!response.ok) {
      let detail = ''
      try {
        const data = await response.json()
        detail = data.detail || ''
      } catch (_) {}

      if (detail === 'External_service_unavailable') {
        errorMessage.value = 'Serviço externo (Superlógica) indisponível. Tente novamente mais tarde.'
      } else {
        errorMessage.value = detail || 'Erro ao exportar inadimplentes.'
      }
      return
    }

    // Extrai nome do arquivo do header ou usa fallback
    const disposition = response.headers.get('Content-Disposition') || ''
    const match = disposition.match(/filename="(.+)"/)
    const filename = match ? match[1] : 'inadimplentes.xlsx'

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)

    successMessage.value = `Arquivo "${filename}" baixado com sucesso!`
  } catch (error) {
    errorMessage.value = error.message || 'Erro inesperado ao exportar.'
  } finally {
    isExporting.value = false
  }
}
</script>