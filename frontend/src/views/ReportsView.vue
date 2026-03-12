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

    <!-- ── Seção 1: Gerar relatório ── -->
    <v-card elevation="4" class="pa-6 mb-6">
      <p class="text-subtitle-2 font-weight-bold text-uppercase text-medium-emphasis mb-4">
        1. Gerar planilha Excel
      </p>

      <v-row align="center">
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

      <v-alert v-if="exportError" type="error" class="mt-5" closable @click:close="exportError = ''">
        {{ exportError }}
      </v-alert>
      <v-alert v-if="exportSuccess" type="success" class="mt-5" closable @click:close="exportSuccess = ''">
        {{ exportSuccess }}
      </v-alert>
    </v-card>

    <!-- ── Seção 2: Disparar mensagens pelo Excel ── -->
    <v-card elevation="4" class="pa-6">
      <p class="text-subtitle-2 font-weight-bold text-uppercase text-medium-emphasis mb-4">
        2. Disparar WhatsApp pelo Excel
      </p>
      <p class="text-body-2 text-medium-emphasis mb-4">
        Faça upload do Excel gerado acima (aba <strong>Resumo</strong>) para enviar mensagens
        a todos os números da coluna <strong>Telefones</strong>.
      </p>

      <!-- Seleção de template -->
      <v-select
        v-model="dispatchTemplateId"
        :items="templates"
        item-title="name"
        item-value="id"
        label="Template de mensagem (opcional)"
        variant="outlined"
        density="comfortable"
        clearable
        prepend-icon="mdi-message-text"
        class="mb-4"
        :loading="loadingTemplates"
        no-data-text="Nenhum template cadastrado"
        hint="Se não selecionado, será usada a mensagem padrão"
        persistent-hint
      />

      <!-- Preview do template -->
      <v-expand-transition>
        <v-sheet
          v-if="selectedTemplate"
          color="grey-lighten-4"
          rounded
          class="pa-3 mb-4"
          style="font-size: 0.85rem; white-space: pre-wrap; word-break: break-word;"
        >
          <p class="text-caption text-medium-emphasis mb-1">Pré-visualização:</p>
          {{ renderPreview(selectedTemplate.body) }}
        </v-sheet>
      </v-expand-transition>

      <!-- Upload do Excel -->
      <v-file-input
        v-model="dispatchFile"
        accept=".csv,.xlsx"
        label="Selecione o arquivo do relatório (.csv ou .xlsx)"
        variant="outlined"
        density="comfortable"
        prepend-icon="mdi-file-excel"
        show-size
        class="mb-4"
      />

      <v-btn
        color="success"
        size="large"
        prepend-icon="mdi-whatsapp"
        :loading="isDispatching"
        :disabled="!dispatchFile"
        @click="dispatchMessages"
      >
        Enviar mensagens
      </v-btn>

      <!-- Resultado do disparo -->
      <v-alert v-if="dispatchError" type="error" class="mt-5" closable @click:close="dispatchError = ''">
        {{ dispatchError }}
      </v-alert>

      <v-alert v-if="dispatchResult" type="success" class="mt-5" closable @click:close="dispatchResult = null">
        <div class="font-weight-bold mb-1">Disparo concluído!</div>
        <div>✅ Enviados com sucesso: <strong>{{ dispatchResult.success }}</strong></div>
        <div>❌ Erros: <strong>{{ dispatchResult.errors }}</strong></div>
        <div v-if="dispatchResult.failures && dispatchResult.failures.length" class="mt-2">
          <div class="text-caption text-medium-emphasis mb-1">Números com falha:</div>
          <div
            v-for="f in dispatchResult.failures"
            :key="f.phone"
            class="text-caption"
          >
            {{ f.phone }} — {{ f.error }}
          </div>
        </div>
      </v-alert>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

// ── Exportar Excel ────────────────────────────────────────────────────────────
const isExporting   = ref(false)
const exportError   = ref('')
const exportSuccess = ref('')
const idCondominio  = ref(null)
const dataPosicao   = ref('')

// ── Disparar mensagens ────────────────────────────────────────────────────────
const isDispatching     = ref(false)
const dispatchError     = ref('')
const dispatchResult    = ref(null)
const dispatchFile      = ref(null)
const dispatchTemplateId = ref(null)

// ── Templates ─────────────────────────────────────────────────────────────────
const templates       = ref([])
const loadingTemplates = ref(false)

const selectedTemplate = computed(() =>
  templates.value.find((t) => t.id === dispatchTemplateId.value) || null
)

const authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

const renderPreview = (body) =>
  body
    .replace(/\{\{nome\}\}/g, 'João Silva')
    .replace(/\{\{condominio\}\}/g, 'Residencial Acácias')
    .replace(/\{\{valor\}\}/g, 'R$ 1.250,00')

// ── Buscar templates ──────────────────────────────────────────────────────────
const fetchTemplates = async () => {
  loadingTemplates.value = true
  try {
    const res = await fetch('/api/templates', { headers: authHeader() })
    if (res.ok) templates.value = await res.json()
  } catch (_) {}
  finally { loadingTemplates.value = false }
}

// ── Exportar Excel ────────────────────────────────────────────────────────────
const exportDefaulters = async () => {
  isExporting.value = true
  exportError.value = ''
  exportSuccess.value = ''

  try {
    const params = new URLSearchParams()
    if (idCondominio.value) params.append('id_condominio', idCondominio.value)
    if (dataPosicao.value) {
      const [ano, mes, dia] = dataPosicao.value.split('-')
      params.append('data_posicao', `${dia}/${mes}/${ano}`)
    }

    const query = params.toString() ? `?${params.toString()}` : ''
    const response = await fetch(`/api/admin/export-defaulters${query}`, {
      headers: authHeader(),
    })

    if (response.status === 204) {
      exportError.value = 'Nenhum inadimplente encontrado para os filtros informados.'
      return
    }

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      const detail = data.detail || ''
      exportError.value = detail === 'External_service_unavailable'
        ? 'Serviço externo (Superlógica) indisponível. Tente novamente mais tarde.'
        : detail || 'Erro ao exportar inadimplentes.'
      return
    }

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

    exportSuccess.value = `Arquivo "${filename}" baixado com sucesso! Agora faça o upload abaixo para disparar as mensagens.`
  } catch (error) {
    exportError.value = error.message || 'Erro inesperado ao exportar.'
  } finally {
    isExporting.value = false
  }
}

// ── Disparar mensagens ────────────────────────────────────────────────────────
const dispatchMessages = async () => {
  if (!dispatchFile.value) return

  isDispatching.value = true
  dispatchError.value = ''
  dispatchResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', dispatchFile.value)

    let url = '/api/messages/dispatch-excel'
    if (dispatchTemplateId.value) {
      url += `?template_id=${dispatchTemplateId.value}`
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: authHeader(),
      body: formData,
    })

    const text = await response.text()
    let data = {}
    try { data = JSON.parse(text) } catch (_) { data = { detail: text } }

    if (!response.ok) {
      throw new Error(data.detail || 'Erro ao disparar mensagens')
    }

    dispatchResult.value = data.details
    dispatchFile.value = null
  } catch (error) {
    dispatchError.value = error.message
  } finally {
    isDispatching.value = false
  }
}

onMounted(fetchTemplates)
</script>