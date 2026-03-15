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

      <!-- Toggle últimos 5 anos -->
      <div class="d-flex align-center gap-3 mb-5">
        <v-btn
          :color="ultimos5anos ? 'primary' : 'default'"
          :variant="ultimos5anos ? 'flat' : 'outlined'"
          size="small"
          prepend-icon="mdi-calendar-clock"
          :disabled="isExporting"
          @click="ultimos5anos = !ultimos5anos"
        >
          Últimos 5 anos
        </v-btn>
        <v-expand-transition>
          <span v-if="ultimos5anos" class="text-caption text-medium-emphasis">
            <v-icon size="13" color="primary" class="mr-1">mdi-information-outline</v-icon>
            Filtrando vencimentos a partir de {{ dataInicio5anos }}
          </span>
        </v-expand-transition>
      </div>

      <v-row align="start">
        <v-col cols="12" sm="4">
          <!-- Campo condomínio com loading visível -->
          <v-autocomplete
            v-model="idCondominio"
            :items="condominios"
            item-title="label"
            item-value="id"
            label="Condomínio (opcional)"
            variant="outlined"
            density="comfortable"
            clearable
            hide-details
            :disabled="isExporting || loadingCondominios"
            no-data-text="Nenhum condomínio encontrado"
            placeholder="Buscar por nome ou ID..."
          />
          <div style="min-height: 28px; padding-top: 4px;">
            <v-expand-transition>
              <div v-if="loadingCondominios" key="loading">
                <v-progress-linear indeterminate color="primary" height="3" rounded style="border-radius:99px;" />
                <p style="font-size:11px;color:#006837;margin-top:5px;display:flex;align-items:center;gap:4px;">
                  <v-icon size="12" color="primary">mdi-office-building-outline</v-icon>
                  Buscando condomínios na Superlógica...
                </p>
              </div>
              <p v-else-if="condominios.length > 0" key="done"
                style="font-size:11px;color:#6b7280;margin-top:5px;display:flex;align-items:center;gap:4px;">
                <v-icon size="12" color="success">mdi-check-circle-outline</v-icon>
                {{ condominios.length }} condomínios disponíveis · Deixe vazio para todos
              </p>
              <p v-else key="hint" style="font-size:11px;color:#9ca3af;margin-top:5px;">
                Deixe em branco para varrer todos os condomínios
              </p>
            </v-expand-transition>
          </div>
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
            :disabled="isExporting"
          />
        </v-col>

        <v-col cols="12" sm="4">
          <v-menu :disabled="isExporting">
            <template #activator="{ props }">
              <v-btn
                color="primary"
                block
                size="large"
                prepend-icon="mdi-file-export"
                append-icon="mdi-chevron-down"
                :loading="isExporting"
                :disabled="isExporting"
                v-bind="props"
              >
                {{ isExporting ? 'Gerando...' : 'Exportar relatório' }}
              </v-btn>
            </template>

            <v-list elevation="4" rounded="lg" min-width="200">
              <v-list-item
                prepend-icon="mdi-microsoft-excel"
                title="Excel (.xlsx)"
                subtitle="Planilha com abas Resumo e Detalhado"
                @click="startExport('xlsx')"
              />
              <v-divider />
              <v-list-item
                prepend-icon="mdi-file-pdf-box"
                title="PDF"
                subtitle="Relatório formatado por condomínio"
                color="red-darken-2"
                @click="startExport('pdf')"
              />
            </v-list>
          </v-menu>
        </v-col>
      </v-row>

      <!-- Progresso do job assíncrono -->
      <v-expand-transition>
        <div v-if="isExporting" class="mt-5">
          <div class="d-flex align-center mb-2">
            <v-icon color="primary" class="mr-2" size="small">mdi-timer-sand</v-icon>
            <span class="text-body-2 text-medium-emphasis">{{ progressMessage }}</span>
          </div>
          <v-progress-linear indeterminate color="primary" rounded height="6" />
          <p class="text-caption text-medium-emphasis mt-2">
            Para todos os condomínios esse processo pode levar alguns minutos. Não feche esta página.
          </p>
        </div>
      </v-expand-transition>

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
        a todos os números das colunas <strong>Telefone 1</strong> e <strong>Telefone 2</strong>.
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
        <div class="font-weight-bold mb-2">Disparo concluído!</div>
        <div>✅ Enviados com sucesso: <strong>{{ dispatchResult.success }}</strong></div>
        <div>❌ Falhas no envio: <strong>{{ envioFailures(dispatchResult).length }}</strong></div>
        <div>📵 Sem número cadastrado: <strong>{{ dispatchResult.sem_numero?.length || 0 }}</strong></div>

        <!-- Unidades sem número -->
        <div v-if="dispatchResult.sem_numero && dispatchResult.sem_numero.length" class="mt-3">
          <div class="text-caption font-weight-bold text-medium-emphasis mb-1">
            📵 Unidades sem número cadastrado:
          </div>
          <v-sheet color="orange-lighten-5" rounded class="pa-2">
            <div
              v-for="(f, i) in dispatchResult.sem_numero"
              :key="i"
              class="text-caption py-1"
              :style="i < dispatchResult.sem_numero.length - 1 ? 'border-bottom: 1px solid rgba(0,0,0,0.08)' : ''"
            >
              <strong>{{ f.unidade }}</strong>
              <span v-if="f.nome"> — {{ f.nome }}</span>
            </div>
          </v-sheet>
        </div>

        <!-- Falhas de envio -->
        <div v-if="envioFailures(dispatchResult).length" class="mt-3">
          <div class="text-caption font-weight-bold text-medium-emphasis mb-1">Falhas no envio:</div>
          <div v-for="f in envioFailures(dispatchResult)" :key="f.phone" class="text-caption">
            {{ f.phone }} — {{ f.error }}
          </div>
        </div>
      </v-alert>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

// ── Estado exportação ─────────────────────────────────────────────────────────
const isExporting        = ref(false)
const exportFormat       = ref('xlsx')
const exportError        = ref('')
const exportSuccess      = ref('')
const idCondominio       = ref(null)
const dataPosicao        = ref('')
const ultimos5anos       = ref(false)
const progressMessage    = ref('Iniciando geração do relatório...')
const condominios        = ref([])
const loadingCondominios = ref(false)
let   pollingInterval    = null
let   pollingSeconds     = 0

// Data de início calculada dinamicamente: hoje - 5 anos
const dataInicio5anos = computed(() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() - 5)
  return d.toLocaleDateString('pt-BR')
})

// ── Estado disparo ────────────────────────────────────────────────────────────
const isDispatching      = ref(false)
const dispatchError      = ref('')
const dispatchResult     = ref(null)
const dispatchFile       = ref(null)
const dispatchTemplateId = ref(null)

// ── Templates ─────────────────────────────────────────────────────────────────
const templates        = ref([])
const loadingTemplates = ref(false)

const selectedTemplate = computed(() =>
  templates.value.find((t) => t.id === dispatchTemplateId.value) || null
)

const authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

const renderPreview = (body) =>
  body
    .replace(/\{\{condominio\}\}/g, 'Residencial Acácias')
    .replace(/\{\{unidade\}\}/g, '315 SALA')
    .replace(/\{\{nome\}\}/g, 'João Silva')
    .replace(/\{\{qtd\}\}/g, '5')
    .replace(/\{\{competencia\}\}/g, '10/2025')
    .replace(/\{\{vencimento\}\}/g, '01/11/2025')
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

// ── Buscar condomínios ────────────────────────────────────────────────────────
const carregarCondominios = async () => {
  loadingCondominios.value = true
  try {
    const res = await fetch('/api/admin/condominios', { headers: authHeader() })
    if (res.ok) {
      const lista = await res.json()
      condominios.value = lista.map(c => ({
        id:    c.id,
        nome:  c.nome,
        label: `[${c.id}] ${c.nome}`,
      }))
    }
  } catch (_) {}
  finally { loadingCondominios.value = false }
}

// ── Exportar Excel ou PDF (assíncrono com polling) ────────────────────────────
const startExport = async (formato) => {
  exportFormat.value    = formato
  isExporting.value     = true
  exportError.value     = ''
  exportSuccess.value   = ''
  pollingSeconds        = 0
  progressMessage.value = `Iniciando geração do relatório ${formato.toUpperCase()}...`

  const baseStart    = formato === 'pdf' ? '/api/admin/export-pdf/start'   : '/api/admin/export-defaulters/start'
  const baseStatus   = formato === 'pdf' ? '/api/admin/export-pdf/status'  : '/api/admin/export-defaulters/status'
  const baseDownload = formato === 'pdf' ? '/api/admin/export-pdf/download' : '/api/admin/export-defaulters/download'

  try {
    const params = new URLSearchParams()
    if (idCondominio.value) params.append('id_condominio', idCondominio.value)
    if (dataPosicao.value) {
      const [ano, mes, dia] = dataPosicao.value.split('-')
      params.append('data_posicao', `${dia}/${mes}/${ano}`)
    }
    if (ultimos5anos.value) params.append('ultimos_5_anos', 'true')

    const query    = params.toString() ? `?${params.toString()}` : ''
    const startRes = await fetch(`${baseStart}${query}`, {
      method:  'POST',
      headers: authHeader(),
    })
    if (!startRes.ok) {
      const d = await startRes.json().catch(() => ({}))
      exportError.value = d.detail || 'Erro ao iniciar exportação.'
      isExporting.value = false
      return
    }
    const { job_id } = await startRes.json()

    pollingInterval = setInterval(async () => {
      pollingSeconds += 3
      const mins  = Math.floor(pollingSeconds / 60)
      const secs  = pollingSeconds % 60
      const tempo = mins > 0 ? `${mins}m ${secs}s` : `${secs}s`
      progressMessage.value = `Processando ${formato.toUpperCase()}... (${tempo} aguardando)`

      try {
        const statusRes = await fetch(`${baseStatus}/${job_id}`, { headers: authHeader() })
        if (!statusRes.ok) return
        const { status, filename, error } = await statusRes.json()

        if (status === 'done') {
          clearInterval(pollingInterval)
          pollingInterval = null
          await downloadJob(job_id, filename, baseDownload)
        } else if (status === 'empty') {
          clearInterval(pollingInterval)
          pollingInterval = null
          exportError.value = 'Nenhum inadimplente encontrado para os filtros informados.'
          isExporting.value = false
        } else if (status === 'error') {
          clearInterval(pollingInterval)
          pollingInterval = null
          exportError.value = error || 'Erro ao gerar relatório.'
          isExporting.value = false
        }
      } catch (_) {}
    }, 3000)

  } catch (err) {
    exportError.value = err.message || 'Erro inesperado.'
    isExporting.value = false
  }
}

const downloadJob = async (jobId, filename, baseDownload) => {
  try {
    const dlRes = await fetch(`${baseDownload}/${jobId}`, { headers: authHeader() })
    if (!dlRes.ok) {
      exportError.value = 'Erro ao baixar o arquivo gerado.'
      isExporting.value = false
      return
    }
    const disposition = dlRes.headers.get('Content-Disposition') || ''
    const match = disposition.match(/filename="(.+)"/)
    const fname = match ? match[1] : filename || 'inadimplentes'

    const blob = await dlRes.blob()
    const url  = window.URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = fname
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)

    exportSuccess.value = `Arquivo "${fname}" baixado com sucesso!`
  } catch (err) {
    exportError.value = err.message || 'Erro ao baixar arquivo.'
  } finally {
    isExporting.value = false
  }
}

// ── Disparar mensagens ────────────────────────────────────────────────────────
const dispatchMessages = async () => {
  if (!dispatchFile.value) return

  isDispatching.value  = true
  dispatchError.value  = ''
  dispatchResult.value = null

  try {
    const formData = new FormData()
    formData.append('file', dispatchFile.value)

    let url = '/api/messages/dispatch-excel'
    if (dispatchTemplateId.value) url += `?template_id=${dispatchTemplateId.value}`

    const response = await fetch(url, {
      method:  'POST',
      headers: authHeader(),
      body:    formData,
    })

    const text = await response.text()
    let data = {}
    try { data = JSON.parse(text) } catch (_) { data = { detail: text } }

    if (!response.ok) throw new Error(data.detail || 'Erro ao disparar mensagens')

    dispatchResult.value = data.details
    dispatchFile.value   = null
  } catch (error) {
    dispatchError.value = error.message
  } finally {
    isDispatching.value = false
  }
}

// Filtra apenas falhas reais de envio (exclui "sem número")
const envioFailures = (result) => {
  if (!result?.failures) return []
  return result.failures.filter(f => f.phone !== '—')
}

onMounted(() => {
  fetchTemplates()
  carregarCondominios()
})
onUnmounted(() => { if (pollingInterval) clearInterval(pollingInterval) })
</script>