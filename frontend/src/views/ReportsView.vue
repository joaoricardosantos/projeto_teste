<template>
  <v-container>
    <v-row class="mb-6">
      <v-col cols="12" md="8">
        <h1 class="text-h5 font-weight-bold mb-2">
          Relatórios de inadimplência
        </h1>
        <p class="text-body-2">
          Gere um arquivo Excel com todos os condomínios inadimplentes integrados ao sistema externo.
        </p>
      </v-col>
    </v-row>

    <v-alert v-if="errorMessage" type="error" class="mb-4" dense>
      {{ errorMessage }}
    </v-alert>

    <v-card elevation="4" class="pa-6">
      <v-btn
        color="primary"
        :loading="isExporting"
        @click="exportDefaulters"
      >
        Exportar inadimplentes (Excel)
      </v-btn>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref } from 'vue'

const isExporting = ref(false)
const errorMessage = ref('')

const exportDefaulters = async () => {
  isExporting.value = true
  errorMessage.value = ''
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('/api/admin/export-defaulters', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    if (response.status === 204) {
      throw new Error('Nenhum inadimplente encontrado para exportar')
    }

    if (!response.ok) {
      let detail = ''
      try {
        const data = await response.json()
        detail = data.detail
      } catch (e) {
        // resposta não era JSON, mantém detail vazio
      }

      if (detail === 'External_service_unavailable') {
        throw new Error('Serviço externo indisponível. Tente novamente mais tarde.')
      }

      throw new Error(detail || 'Erro ao exportar inadimplentes')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'inadimplentes_condominios.xlsx'
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isExporting.value = false
  }
}
</script>

