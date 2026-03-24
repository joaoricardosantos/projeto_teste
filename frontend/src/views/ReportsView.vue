<template>
  <div>

    <!-- ── Cabeçalho ── -->
    <div class="d-flex align-center gap-4 mb-6">
      <div class="page-icon">
        <v-icon size="20" color="white">mdi-file-chart-outline</v-icon>
      </div>
      <div>
        <h1 class="page-title">Relatórios de Inadimplência</h1>
        <p class="page-subtitle">Gere planilhas e PDFs, identifique unidades sem número e dispare cobranças em lote</p>
      </div>
    </div>

    <!-- ── Seção 1: Exportar relatório ── -->
    <v-card class="section-card mb-7" elevation="3">
      <div class="section-header">
        <div class="section-badge">1</div>
        <div>
          <p class="section-title">Gerar Relatório</p>
          <p class="section-subtitle">Exportar planilha Excel com abas Resumo e Detalhado, ou PDF formatado</p>
        </div>
      </div>

      <div class="pa-6">
        <!-- Filtros toggle -->
        <div class="d-flex align-center flex-wrap mb-6" style="gap: 5px;">
          <v-btn
            :color="ultimos5anos ? 'primary' : 'default'"
            :variant="ultimos5anos ? 'flat' : 'outlined'"
            size="small"
            prepend-icon="mdi-calendar-clock"
            :disabled="isExporting"
            @click="ultimos5anos = !ultimos5anos"
          >Últimos 5 anos</v-btn>

          <v-btn
            :color="ordenarDesc ? 'primary' : 'default'"
            :variant="ordenarDesc ? 'flat' : 'outlined'"
            size="small"
            prepend-icon="mdi-sort-descending"
            :disabled="isExporting"
            @click="ordenarDesc = !ordenarDesc"
          >Maior valor primeiro</v-btn>

          <v-expand-transition>
            <span v-if="ultimos5anos" class="text-caption text-medium-emphasis">
              <v-icon size="13" color="primary" class="mr-1">mdi-information-outline</v-icon>
              A partir de {{ dataInicio5anos }}
            </span>
          </v-expand-transition>
        </div>

        <v-row align="center">
          <v-col cols="12" sm="5">
            <v-autocomplete
              v-model="idCondominio"
              :items="condominios"
              item-title="label"
              item-value="id"
              label="Condomínio (opcional)"
              variant="outlined"
              density="comfortable"
              clearable
              multiple
              chips
              closable-chips
              hide-details
              :disabled="isExporting || loadingCondominios"
              no-data-text="Nenhum condomínio encontrado"
              placeholder="Buscar por nome ou ID..."
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
              hide-details
              :disabled="isExporting"
            />
          </v-col>

          <v-col cols="12" sm="3">
            <v-menu :disabled="isExporting">
              <template #activator="{ props }">
                <v-btn
                  color="primary" block size="large"
                  prepend-icon="mdi-file-export"
                  append-icon="mdi-chevron-down"
                  :loading="isExporting"
                  :disabled="isExporting"
                  v-bind="props"
                >{{ isExporting ? 'Gerando...' : 'Exportar' }}</v-btn>
              </template>
              <v-list elevation="4" rounded="lg" min-width="200">
                <v-list-item prepend-icon="mdi-microsoft-excel" title="Excel (.xlsx)" subtitle="Resumo e Detalhado" @click="startExport('xlsx')" />
                <v-divider />
                <v-list-item prepend-icon="mdi-file-pdf-box" title="PDF" subtitle="Relatório formatado" color="red-darken-2" @click="startExport('pdf')" />
              </v-list>
            </v-menu>
          </v-col>
        </v-row>

        <v-expand-transition>
          <p v-if="loadingCondominios" class="text-caption mt-3" style="color:#006837;">
            <v-icon size="12" color="primary">mdi-office-building-outline</v-icon>
            Buscando condomínios...
          </p>
          <p v-else-if="condominios.length > 0" class="text-caption mt-3" style="color:#6b7280;">
            <v-icon size="12" color="success">mdi-check-circle-outline</v-icon>
            {{ condominios.length }} disponíveis · Deixe o campo vazio para exportar todos
          </p>
        </v-expand-transition>

        <!-- Progresso -->
        <v-expand-transition>
          <div v-if="isExporting" class="mt-5">
            <div class="d-flex align-center mb-2">
              <v-icon color="primary" class="mr-2" size="small">mdi-timer-sand</v-icon>
              <span class="text-body-2 text-medium-emphasis">{{ progressMessage }}</span>
            </div>
            <v-progress-linear indeterminate color="primary" rounded height="6" />
            <p class="text-caption text-medium-emphasis mt-2">Para todos os condomínios isso pode levar alguns minutos.</p>
          </div>
        </v-expand-transition>

        <v-alert v-if="exportError"   type="error"   class="mt-4" closable @click:close="exportError = ''">{{ exportError }}</v-alert>
        <v-alert v-if="exportSuccess" type="success" class="mt-4" closable @click:close="exportSuccess = ''">{{ exportSuccess }}</v-alert>
      </div>
    </v-card>

    <!-- ── Seção 2: Sem número ── -->
    <v-card class="section-card mb-7" elevation="3">
      <div class="section-header">
        <div class="section-badge">2</div>
        <div>
          <p class="section-title">Unidades sem Número Cadastrado</p>
          <p class="section-subtitle">Identifique quem não pode receber cobranças por WhatsApp</p>
        </div>
      </div>

      <div class="pa-6">
        <v-autocomplete
          v-model="semNumeroCondominio"
          :items="condominios"
          item-title="label"
          item-value="id"
          label="Condomínio (opcional)"
          variant="outlined"
          density="comfortable"
          clearable
          multiple
          chips
          closable-chips
          hide-details
          class="mb-5"
          :disabled="isSemNumeroLoading || loadingCondominios"
          no-data-text="Nenhum condomínio encontrado"
          placeholder="Deixe vazio para todos os condomínios"
        />

        <div class="d-flex flex-wrap mb-6" style="gap: 5px;">
          <v-btn
            size="small"
            :color="semNumeroUltimos5anos ? 'primary' : 'default'"
            :variant="semNumeroUltimos5anos ? 'flat' : 'outlined'"
            prepend-icon="mdi-calendar-clock"
            :disabled="isSemNumeroLoading"
            @click.stop="semNumeroUltimos5anos = !semNumeroUltimos5anos"
          >Últimos 5 anos</v-btn>

          <v-btn
            size="small"
            :color="semNumeroMin3 ? 'warning' : 'default'"
            :variant="semNumeroMin3 ? 'flat' : 'outlined'"
            prepend-icon="mdi-alert-circle-outline"
            :disabled="isSemNumeroLoading"
            @click.stop="semNumeroMin3 = !semNumeroMin3"
          >3+ inadimplências</v-btn>

          <v-btn
            size="small"
            :color="semNumeroExcluirExterno ? 'error' : 'default'"
            :variant="semNumeroExcluirExterno ? 'flat' : 'outlined'"
            prepend-icon="mdi-gavel"
            :disabled="isSemNumeroLoading"
            @click.stop="semNumeroExcluirExterno = !semNumeroExcluirExterno"
          >Excluir jurídico externo</v-btn>
        </div>

        <div class="d-flex" style="gap: 5px;">
          <v-btn
            color="success" prepend-icon="mdi-file-excel"
            :loading="isSemNumeroLoading && semNumeroFormat === 'xlsx'"
            :disabled="isSemNumeroLoading"
            @click="exportarSemNumero('xlsx')"
          >Baixar Excel</v-btn>

          <v-btn
            color="red-darken-2" prepend-icon="mdi-file-pdf-box"
            :loading="isSemNumeroLoading && semNumeroFormat === 'pdf'"
            :disabled="isSemNumeroLoading"
            @click="exportarSemNumero('pdf')"
          >Baixar PDF</v-btn>
        </div>

        <v-alert v-if="semNumeroError" type="error" class="mt-4" closable @click:close="semNumeroError = ''">
          {{ semNumeroError }}
        </v-alert>
      </div>
    </v-card>

    <!-- ── Seção 3: Disparar pelo Excel ── -->
    <v-card class="section-card" elevation="3">
      <div class="section-header">
        <div class="section-badge">3</div>
        <div>
          <p class="section-title">Disparar WhatsApp pelo Excel</p>
          <p class="section-subtitle">Faça upload do relatório (aba Resumo) para enviar mensagens em lote</p>
        </div>
      </div>

      <div class="pa-6">
        <v-select
          v-model="dispatchTemplateId"
          :items="templates"
          item-title="name"
          item-value="id"
          label="Template de mensagem (opcional)"
          variant="outlined"
          density="comfortable"
          clearable
          prepend-inner-icon="mdi-message-text"
          class="mb-4"
          :loading="loadingTemplates"
          no-data-text="Nenhum template cadastrado"
          hint="Se não selecionado, será usada a mensagem padrão"
          persistent-hint
        />

        <v-expand-transition>
          <v-sheet
            v-if="selectedTemplate"
            color="grey-lighten-4"
            rounded="lg"
            class="pa-4 mb-4"
            style="font-size: 0.85rem; white-space: pre-wrap; word-break: break-word; border-left: 3px solid #006837;"
          >
            <p class="text-caption text-medium-emphasis mb-2 font-weight-bold text-uppercase" style="letter-spacing:.05em;">
              <v-icon size="13" class="mr-1" color="primary">mdi-eye-outline</v-icon>Pré-visualização
            </p>
            {{ renderPreview(selectedTemplate.body) }}
          </v-sheet>
        </v-expand-transition>

        <v-file-input
          v-model="dispatchFile"
          accept=".csv,.xlsx"
          label="Selecione o arquivo (.csv ou .xlsx)"
          variant="outlined"
          density="comfortable"
          prepend-icon=""
          prepend-inner-icon="mdi-file-excel"
          show-size
          class="mb-4"
        />

        <v-btn
          color="success" size="large" prepend-icon="mdi-whatsapp"
          :loading="isDispatching"
          :disabled="!dispatchFile"
          @click="dispatchMessages"
        >Enviar mensagens</v-btn>

        <v-alert v-if="dispatchError" type="error" class="mt-5" closable @click:close="dispatchError = ''">
          {{ dispatchError }}
        </v-alert>

        <v-card v-if="dispatchResult" class="result-card mt-5" elevation="2">
          <div class="result-header">
            <v-icon color="white" size="18" class="mr-2">mdi-check-circle-outline</v-icon>
            Disparo concluído!
          </div>
          <div class="pa-5">
            <v-row>
              <v-col cols="4">
                <div class="stat-box stat-box--success">
                  <p class="stat-num">{{ dispatchResult.success }}</p>
                  <p class="stat-label">Enviados</p>
                </div>
              </v-col>
              <v-col cols="4">
                <div class="stat-box stat-box--error">
                  <p class="stat-num">{{ envioFailures(dispatchResult).length }}</p>
                  <p class="stat-label">Falhas</p>
                </div>
              </v-col>
              <v-col cols="4">
                <div class="stat-box stat-box--warn">
                  <p class="stat-num">{{ dispatchResult.sem_numero?.length || 0 }}</p>
                  <p class="stat-label">Sem número</p>
                </div>
              </v-col>
            </v-row>

            <div v-if="dispatchResult.sem_numero?.length" class="mt-4">
              <p class="text-caption font-weight-bold text-medium-emphasis mb-2">Unidades sem número:</p>
              <v-sheet color="orange-lighten-5" rounded="lg" class="pa-3">
                <div v-for="(f, i) in dispatchResult.sem_numero" :key="i" class="text-caption py-1"
                  :style="i < dispatchResult.sem_numero.length - 1 ? 'border-bottom: 1px solid rgba(0,0,0,0.07)' : ''">
                  <strong>{{ f.unidade }}</strong><span v-if="f.nome"> — {{ f.nome }}</span>
                </div>
              </v-sheet>
            </div>

            <div v-if="envioFailures(dispatchResult).length" class="mt-3">
              <p class="text-caption font-weight-bold text-medium-emphasis mb-2">Falhas no envio:</p>
              <div v-for="f in envioFailures(dispatchResult)" :key="f.phone" class="text-caption">
                {{ f.phone }} — {{ f.error }}
              </div>
            </div>
          </div>
        </v-card>
      </div>
    </v-card>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

const isExporting        = ref(false)
const exportFormat       = ref('xlsx')
const exportError        = ref('')
const exportSuccess      = ref('')
const idCondominio       = ref([])
const dataPosicao        = ref('')
const ultimos5anos       = ref(false)
const ordenarDesc        = ref(false)
const progressMessage    = ref('Iniciando geração do relatório...')
const condominios        = ref([])
const loadingCondominios = ref(false)
let   pollingInterval    = null
let   pollingSeconds     = 0

const dataInicio5anos = computed(() => {
  const d = new Date()
  d.setFullYear(d.getFullYear() - 5)
  return d.toLocaleDateString('pt-BR')
})

const semNumeroCondominio     = ref([])
const isSemNumeroLoading      = ref(false)
const semNumeroError          = ref('')
const semNumeroFormat         = ref('')
const semNumeroUltimos5anos   = ref(false)
const semNumeroMin3           = ref(false)
const semNumeroExcluirExterno = ref(false)

const exportarSemNumero = async (format) => {
  isSemNumeroLoading.value = true
  semNumeroFormat.value    = format
  semNumeroError.value     = ''
  try {
    const params = new URLSearchParams()
    if (semNumeroCondominio.value?.length) params.append('id_condominio', semNumeroCondominio.value.join(','))
    if (semNumeroUltimos5anos.value) params.append('ultimos_5_anos', 'true')
    if (semNumeroMin3.value) params.append('min_inadimplencias', '3')
    if (semNumeroExcluirExterno.value) params.append('excluir_juridico_externo', 'true')
    let url = `/api/admin/sem-numero/${format}`
    const qs = params.toString()
    if (qs) url += `?${qs}`
    const res = await fetch(url, { headers: authHeader() })
    if (!res.ok) throw new Error('Erro ao gerar relatório')
    const blob = await res.blob()
    const a    = document.createElement('a')
    a.href     = URL.createObjectURL(blob)
    a.download = `sem_numero.${format}`
    document.body.appendChild(a)
    a.click()
    a.remove()
  } catch (e) {
    semNumeroError.value = e.message
  } finally {
    isSemNumeroLoading.value = false
    semNumeroFormat.value    = ''
  }
}

const isDispatching      = ref(false)
const dispatchError      = ref('')
const dispatchResult     = ref(null)
const dispatchFile       = ref(null)
const dispatchTemplateId = ref(null)

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

const fetchTemplates = async () => {
  loadingTemplates.value = true
  try {
    const res = await fetch('/api/templates', { headers: authHeader() })
    if (res.ok) templates.value = await res.json()
  } catch (_) {}
  finally { loadingTemplates.value = false }
}

const carregarCondominios = async () => {
  loadingCondominios.value = true
  try {
    const res = await fetch('/api/admin/condominios', { headers: authHeader() })
    if (res.ok) {
      const lista = await res.json()
      condominios.value = lista
        .map(c => ({ id: c.id, nome: c.nome, label: `[${c.id}] ${c.nome}` }))
        .sort((a, b) => a.id - b.id)
    }
  } catch (_) {}
  finally { loadingCondominios.value = false }
}

const startExport = async (formato) => {
  exportFormat.value    = formato
  isExporting.value     = true
  exportError.value     = ''
  exportSuccess.value   = ''
  pollingSeconds        = 0
  progressMessage.value = `Iniciando geração do relatório ${formato.toUpperCase()}...`

  const baseStart    = formato === 'pdf' ? '/api/admin/export-pdf/start'    : '/api/admin/export-defaulters/start'
  const baseStatus   = formato === 'pdf' ? '/api/admin/export-pdf/status'   : '/api/admin/export-defaulters/status'
  const baseDownload = formato === 'pdf' ? '/api/admin/export-pdf/download' : '/api/admin/export-defaulters/download'

  try {
    const params = new URLSearchParams()
    if (idCondominio.value?.length) params.append('id_condominio', idCondominio.value.join(','))
    if (dataPosicao.value) {
      const [ano, mes, dia] = dataPosicao.value.split('-')
      params.append('data_posicao', `${dia}/${mes}/${ano}`)
    }
    if (ultimos5anos.value) params.append('ultimos_5_anos', 'true')
    if (ordenarDesc.value) params.append('ordenar_desc', 'true')

    const query    = params.toString() ? `?${params.toString()}` : ''
    const startRes = await fetch(`${baseStart}${query}`, { method: 'POST', headers: authHeader() })
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
          clearInterval(pollingInterval); pollingInterval = null
          await downloadJob(job_id, filename, baseDownload)
        } else if (status === 'empty') {
          clearInterval(pollingInterval); pollingInterval = null
          exportError.value = 'Nenhum inadimplente encontrado para os filtros informados.'
          isExporting.value = false
        } else if (status === 'error') {
          clearInterval(pollingInterval); pollingInterval = null
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
    if (!dlRes.ok) { exportError.value = 'Erro ao baixar o arquivo gerado.'; isExporting.value = false; return }
    const disposition = dlRes.headers.get('Content-Disposition') || ''
    const match = disposition.match(/filename="(.+)"/)
    const fname = match ? match[1] : filename || 'inadimplentes'
    const blob = await dlRes.blob()
    const url  = window.URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href = url; a.download = fname
    document.body.appendChild(a); a.click(); a.remove()
    window.URL.revokeObjectURL(url)
    exportSuccess.value = `Arquivo "${fname}" baixado com sucesso!`
  } catch (err) {
    exportError.value = err.message || 'Erro ao baixar arquivo.'
  } finally {
    isExporting.value = false
  }
}

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
    const response = await fetch(url, { method: 'POST', headers: authHeader(), body: formData })
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

const envioFailures = (result) => {
  if (!result?.failures) return []
  return result.failures.filter(f => f.phone !== '—')
}

onMounted(() => { fetchTemplates(); carregarCondominios() })
onUnmounted(() => { if (pollingInterval) clearInterval(pollingInterval) })
</script>

<style scoped>
.page-icon {
  width: 42px; height: 42px; border-radius: 11px;
  background: linear-gradient(135deg, #00a651 0%, #006837 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(0,168,81,0.3); flex-shrink: 0;
  margin-right: 8px;
}
.page-title    { font-size: 1.2rem; font-weight: 700; line-height: 1.3; margin: 0; }
.page-subtitle { font-size: 0.82rem; opacity: .55; margin: 2px 0 0; }

.section-card { border-radius: 14px !important; overflow: hidden; }
.section-header {
  background: linear-gradient(135deg, #006837 0%, #00a651 100%);
  padding: 14px 20px;
  display: flex; align-items: center; gap: 14px;
}
.section-badge {
  width: 28px; height: 28px; border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 700; font-size: 0.85rem; flex-shrink: 0;
}
.section-title    { color: white; font-weight: 600; font-size: 0.92rem; margin: 0; }
.section-subtitle { color: rgba(255,255,255,0.7); font-size: 0.78rem; margin: 2px 0 0; }

.result-card { border-radius: 14px !important; overflow: hidden; }
.result-header {
  background: linear-gradient(135deg, #2e7d32 0%, #43a047 100%);
  padding: 14px 20px;
  display: flex; align-items: center;
  color: white; font-weight: 600; font-size: 0.92rem;
}
.stat-box { text-align: center; padding: 12px; border-radius: 10px; }
.stat-box--success { background: rgba(46,125,50,0.08); }
.stat-box--error   { background: rgba(198,40,40,0.08); }
.stat-box--warn    { background: rgba(245,127,23,0.08); }
.stat-num   { font-size: 1.6rem; font-weight: 800; margin: 0; line-height: 1; }
.stat-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: .05em; opacity: .6; margin: 4px 0 0; }
.stat-box--success .stat-num { color: #2e7d32; }
.stat-box--error   .stat-num { color: #c62828; }
.stat-box--warn    .stat-num { color: #e65100; }
</style>
