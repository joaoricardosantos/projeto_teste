<template>
  <v-container>
    <v-row class="mb-4">
      <v-col cols="12" md="8">
        <h1 class="text-h5 font-weight-bold mb-1">Relatórios de inadimplência</h1>
        <p class="text-body-2 text-medium-emphasis">
          Gere um Excel com abas <strong>Resumo</strong> e <strong>Detalhado</strong>
          por condomínio. Deixe os filtros em branco para varrer todos os condomínios
          com a data de hoje.
        </p>
      </v-col>
    </v-row>

    <v-card elevation="4" class="pa-6">
      <v-row>
        <v-col cols="12" sm="4">
          <v-text-field
            v-model="idCondominio"
            label="ID do condomínio (opcional)"
            type="number"
            min="1"
            variant="outlined"
            clearable
            hint="Deixe em branco para todos"
            persistent-hint
          />
        </v-col>
        <v-col cols="12" sm="4">
          <v-text-field
            v-model="dataPosicao"
            label="Data de posição (opcional)"
            type="date"
            variant="outlined"
            clearable
            hint="Deixe em branco para hoje"
            persistent-hint
          />
        </v-col>
        <v-col cols="12" sm="4" class="d-flex align-center">
          <v-btn
            color="primary"
            block
            size="large"
            :loading="isExporting"
            :disabled="isExporting"
            prepend-icon="mdi-microsoft-excel"
            @click="exportDefaulters"
          >
            Exportar Excel
          </v-btn>
        </v-col>
      </v-row>

      <v-alert v-if="errorMessage" type="error" class="mt-4" dense>
        {{ errorMessage }}
      </v-alert>

      <v-alert v-if="successMessage" type="success" class="mt-4" dense>
        {{ successMessage }}
      </v-alert>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'

const isExporting   = ref(false)
const errorMessage  = ref('')
const successMessage = ref('')
const idCondominio  = ref('')
const dataPosicao   = ref('')

const exportDefaulters = async () => {
  isExporting.value   = true
  errorMessage.value  = ''
  successMessage.value = ''

  try {
    const token = localStorage.getItem('access_token')

    // Monta query string apenas com os parâmetros preenchidos
    const params = new URLSearchParams()
    if (idCondominio.value) params.set('id_condominio', idCondominio.value)
    if (dataPosicao.value) {
      // Converte de yyyy-mm-dd (input[type=date]) para dd/mm/yyyy (API)
      const [y, m, d] = dataPosicao.value.split('-')
      params.set('data_posicao', `${d}/${m}/${y}`)
    }

    const qs  = params.toString() ? `?${params.toString()}` : ''
    const url = `/api/admin/export-defaulters${qs}`

    const response = await fetch(url, {
      method: 'GET',
      headers: { Authorization: `Bearer ${token}` },
    })

    if (response.status === 204) {
      throw new Error('Nenhum inadimplente encontrado para os filtros informados.')
    }

    if (!response.ok) {
      let detail = ''
      try {
        const data = await response.json()
        detail = data.detail
      } catch (_) { /* resposta não era JSON */ }

      if (detail === 'External_service_unavailable') {
        throw new Error('Serviço externo indisponível. Tente novamente mais tarde.')
      }
      throw new Error(detail || 'Erro ao exportar inadimplentes.')
    }

    // Dispara download do arquivo
    const blob = await response.blob()
    const blobUrl = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = blobUrl

    // Tenta ler o nome do arquivo retornado pelo backend
    const disposition = response.headers.get('Content-Disposition') || ''
    const match = disposition.match(/filename="?([^"]+)"?/)
    a.download = match ? match[1] : 'inadimplentes.xlsx'

    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(blobUrl)

    successMessage.value = 'Arquivo gerado e baixado com sucesso!'
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isExporting.value = false
  }
}
</script>