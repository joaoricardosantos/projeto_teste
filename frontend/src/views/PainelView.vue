<template>
  <div>

    <!-- ── Cabeçalho ── -->
    <div class="d-flex align-center justify-space-between flex-wrap gap-3 mb-6">
      <div class="d-flex align-center gap-4">
        <div class="page-icon">
          <v-icon size="20" color="white">mdi-send-outline</v-icon>
        </div>
        <div>
          <h1 class="page-title">Enviar Mensagens</h1>
          <p class="page-subtitle">Selecione os condomínios, unidades e dispare cobranças via WhatsApp</p>
        </div>
      </div>
    </div>

    <v-row justify="center">
      <v-col cols="12" lg="8" xl="7">

        <!-- ── Seção 1: Condomínio e Template ── -->
        <v-card class="section-card mb-4" elevation="3">
          <div class="section-header">
            <div class="section-badge">1</div>
            <div>
              <p class="section-title">Condomínio e Mensagem</p>
              <p class="section-subtitle">Selecione o(s) condomínio(s) e o template de cobrança</p>
            </div>
          </div>

          <div class="pa-5">
            <v-autocomplete
              v-model="selectedCondominioIds"
              :items="condominios"
              item-title="label"
              item-value="id"
              label="Condomínio"
              variant="outlined"
              density="comfortable"
              clearable
              multiple
              chips
              closable-chips
              prepend-inner-icon="mdi-office-building"
              class="mb-4"
              :loading="loadingCondominios"
              :disabled="loadingCondominios || loading"
              no-data-text="Nenhum condomínio encontrado"
              placeholder="Buscar por nome ou ID..."
              :hint="loadingCondominios ? 'Buscando condomínios...' : condominios.length > 0 ? condominios.length + ' condomínios disponíveis' : ''"
              persistent-hint
              @update:model-value="onCondominioChange"
            />

            <v-select
              v-model="selectedTemplateId"
              :items="templates"
              item-title="name"
              item-value="id"
              label="Template de mensagem"
              variant="outlined"
              density="comfortable"
              clearable
              prepend-inner-icon="mdi-message-text"
              :loading="loadingTemplates"
              :disabled="loading"
              no-data-text="Nenhum template cadastrado"
              hint="Se não selecionado, será usada a mensagem padrão"
              persistent-hint
            />

            <!-- Preview do template -->
            <v-expand-transition>
              <v-sheet
                v-if="selectedTemplate"
                rounded="lg"
                class="pa-4 mt-4 template-preview"
                style="font-size: 0.85rem; white-space: pre-wrap; word-break: break-word; border-left: 3px solid #34d399;"
              >
                <p class="text-caption text-medium-emphasis mb-2 font-weight-bold text-uppercase" style="letter-spacing:.05em;">
                  <v-icon size="13" class="mr-1" color="primary">mdi-eye-outline</v-icon>
                  Pré-visualização
                </p>
                {{ renderPreview(selectedTemplate.body) }}
              </v-sheet>
            </v-expand-transition>
          </div>
        </v-card>

        <!-- ── Seção 2: Unidades ── -->
        <v-expand-transition>
          <v-card v-if="unidades.length > 0 || loadingUnidades" class="section-card mb-4" elevation="3">
            <div class="section-header">
              <div class="section-badge">2</div>
              <div class="flex-grow-1">
                <p class="section-title">
                  Unidades Inadimplentes
                  <v-chip v-if="unidades.length" size="x-small" color="white" variant="tonal" class="ml-2" style="color:white;">
                    {{ unidades.length }}
                  </v-chip>
                </p>
                <p class="section-subtitle">Selecione quais unidades receberão a mensagem</p>
              </div>
              <div v-if="unidades.length" class="d-flex gap-2">
                <v-btn
                  size="small" variant="tonal" color="white"
                  style="color:white;"
                  @click="selecionarTresMais"
                >3+ cobranças</v-btn>
                <v-btn
                  size="small" variant="tonal" color="white"
                  style="color:white;"
                  @click="toggleSelecionarTodas"
                >{{ todasSelecionadas ? 'Desmarcar todas' : 'Marcar todas' }}</v-btn>
              </div>
            </div>

            <div class="pa-5">
              <!-- Loading -->
              <div v-if="loadingUnidades" class="d-flex align-center justify-center pa-8">
                <v-progress-circular indeterminate color="primary" size="32" class="mr-3" />
                <span class="text-body-2 text-medium-emphasis">Buscando inadimplentes...</span>
              </div>

              <!-- Lista -->
              <v-sheet v-else border rounded="lg" class="overflow-hidden">
                <div
                  v-for="(u, i) in unidades"
                  :key="u.id_unidade"
                  class="unit-row"
                  :class="{ 'unit-row--even': i % 2 === 0 }"
                >
                  <v-checkbox
                    v-model="selectedUnidades"
                    :value="u.id_unidade"
                    hide-details
                    density="compact"
                    :disabled="!u.tem_numero"
                    class="flex-shrink-0"
                  />

                  <div class="unit-info">
                    <span class="unit-name">
                      <strong>{{ u.bloco ? u.bloco + ' ' + u.unidade : u.unidade }}</strong>
                      <span class="text-medium-emphasis ml-1">— {{ u.nome }}</span>
                    </span>
                    <v-chip
                      v-if="u.qtd_inadimplencias > 1"
                      size="x-small" color="warning" variant="tonal" class="ml-2"
                    >{{ u.qtd_inadimplencias }} cobranças</v-chip>
                  </div>

                  <div class="unit-right">
                    <span class="unit-valor">{{ u.valor }}</span>
                    <v-chip v-if="!u.tem_numero" size="x-small" color="error" variant="tonal">Sem número</v-chip>
                  </div>
                </div>
              </v-sheet>

              <p v-if="!loadingUnidades && unidades.length" class="text-caption text-medium-emphasis mt-3">
                <v-icon size="13" class="mr-1">mdi-check-circle-outline</v-icon>
                {{ selectedUnidades.length }} de {{ unidadesComNumero.length }} selecionadas
                <span v-if="unidadesSemNumero.length" class="ml-3 text-error">
                  <v-icon size="13" class="mr-1">mdi-phone-off</v-icon>
                  {{ unidadesSemNumero.length }} sem número
                </span>
              </p>
            </div>
          </v-card>
        </v-expand-transition>

        <!-- ── Erros / Resultado ── -->
        <v-alert v-if="errorMessage" type="error" class="mb-4" closable @click:close="errorMessage = ''">
          {{ errorMessage }}
        </v-alert>

        <v-card v-if="resultDetails" class="result-card mb-4" elevation="3">
          <div class="result-header">
            <v-icon color="white" size="20" class="mr-2">mdi-check-circle-outline</v-icon>
            <span>{{ successMessage }}</span>
          </div>
          <div class="pa-5">
            <v-row>
              <v-col cols="4">
                <div class="stat-box stat-box--success">
                  <p class="stat-num">{{ resultDetails.success }}</p>
                  <p class="stat-label">Enviados</p>
                </div>
              </v-col>
              <v-col cols="4">
                <div class="stat-box stat-box--error">
                  <p class="stat-num">{{ envioFailures.length }}</p>
                  <p class="stat-label">Falhas</p>
                </div>
              </v-col>
              <v-col cols="4">
                <div class="stat-box stat-box--warn">
                  <p class="stat-num">{{ resultDetails.sem_numero?.length || 0 }}</p>
                  <p class="stat-label">Sem número</p>
                </div>
              </v-col>
            </v-row>

            <div v-if="resultDetails.sem_numero?.length" class="mt-4">
              <p class="text-caption font-weight-bold text-medium-emphasis mb-2">
                <v-icon size="13" class="mr-1">mdi-phone-off</v-icon>Unidades sem número:
              </p>
              <v-sheet color="orange-lighten-5" rounded="lg" class="pa-3">
                <div v-for="(f, i) in resultDetails.sem_numero" :key="i" class="text-caption py-1"
                  :style="i < resultDetails.sem_numero.length - 1 ? 'border-bottom: 1px solid rgba(0,0,0,0.07)' : ''">
                  <strong>{{ f.unidade }}</strong><span v-if="f.nome"> — {{ f.nome }}</span>
                </div>
              </v-sheet>
            </div>

            <div v-if="envioFailures.length" class="mt-3">
              <p class="text-caption font-weight-bold text-medium-emphasis mb-2">
                <v-icon size="13" class="mr-1">mdi-alert-circle-outline</v-icon>Falhas no envio:
              </p>
              <div v-for="f in envioFailures" :key="f.phone" class="text-caption py-1">
                <strong>{{ f.unidade || f.phone }}</strong>
                <span v-if="f.nome"> — {{ f.nome }}</span>: {{ friendlyError(f.error) }}
              </div>
            </div>
          </div>
        </v-card>

        <!-- ── Ações ── -->
        <div class="d-flex gap-3 flex-column">
          <v-btn
            v-if="resultDetails"
            variant="outlined"
            color="grey-darken-1"
            size="large"
            prepend-icon="mdi-file-pdf-box"
            @click="baixarRelatorio"
          >Baixar relatório de envio (PDF)</v-btn>

          <v-btn
            color="primary"
            size="large"
            :loading="loading"
            :disabled="!selectedCondominioIds.length || loadingCondominios || loadingUnidades || selectedUnidades.length === 0"
            @click="dialogConfirmar = true"
          >
            <v-icon start>mdi-whatsapp</v-icon>
            Enviar para {{ selectedUnidades.length }} unidade{{ selectedUnidades.length !== 1 ? 's' : '' }}
          </v-btn>
        </div>

      </v-col>
    </v-row>

    <!-- ── Modal de confirmação ── -->
    <v-dialog v-model="dialogConfirmar" max-width="440" persistent>
      <v-card rounded="xl" elevation="12" class="confirm-card">

        <!-- Header no padrão dialog-header global -->
        <div class="dialog-header d-flex align-center gap-3">
          <div class="page-icon" style="width:36px;height:36px;border-radius:9px;flex-shrink:0;">
            <v-icon size="18" color="white">mdi-whatsapp</v-icon>
          </div>
          <div>
            <p class="confirm-title">Confirmar disparo</p>
            <p class="confirm-subtitle">Revise os dados antes de enviar</p>
          </div>
        </div>

        <v-divider class="confirm-divider" />

        <div class="pa-5">

          <!-- Itens de resumo -->
          <div class="confirm-items">
            <div class="confirm-item">
              <div class="confirm-item__left">
                <v-icon size="15" color="primary" class="mr-2">mdi-office-building</v-icon>
                <span>Condomínio{{ selectedCondominioIds.length > 1 ? 's' : '' }}</span>
              </div>
              <span class="confirm-item__val">
                {{ selectedCondominioIds.length }} selecionado{{ selectedCondominioIds.length !== 1 ? 's' : '' }}
              </span>
            </div>

            <div class="confirm-item">
              <div class="confirm-item__left">
                <v-icon size="15" color="primary" class="mr-2">mdi-home-group</v-icon>
                <span>Unidades a receber</span>
              </div>
              <span class="confirm-item__val confirm-item__val--green">{{ selectedUnidades.length }}</span>
            </div>

            <div class="confirm-item">
              <div class="confirm-item__left">
                <v-icon size="15" color="primary" class="mr-2">mdi-message-text-outline</v-icon>
                <span>Template</span>
              </div>
              <span class="confirm-item__val">{{ selectedTemplate ? selectedTemplate.name : 'Padrão' }}</span>
            </div>

            <div v-if="unidadesSemNumero.length" class="confirm-item">
              <div class="confirm-item__left">
                <v-icon size="15" color="error" class="mr-2">mdi-phone-off</v-icon>
                <span>Sem número</span>
              </div>
              <span class="confirm-item__val confirm-item__val--red">
                {{ unidadesSemNumero.length }} unidade{{ unidadesSemNumero.length !== 1 ? 's' : '' }}
              </span>
            </div>
          </div>

          <!-- Avisos inline -->
          <div v-if="unidadesSemNumero.length" class="confirm-notice confirm-notice--warn mt-3">
            <v-icon size="14" color="#d97706" class="mr-2 flex-shrink-0">mdi-phone-off</v-icon>
            <span>{{ unidadesSemNumero.length }} unidade{{ unidadesSemNumero.length !== 1 ? 's' : '' }} sem número não receberão mensagem.</span>
          </div>

          <div class="confirm-notice mt-2">
            <v-icon size="14" color="primary" class="mr-2 flex-shrink-0">mdi-information-outline</v-icon>
            <span>Esta ação envia mensagens reais via WhatsApp e não pode ser desfeita.</span>
          </div>
        </div>

        <v-divider class="confirm-divider" />

        <div class="d-flex justify-end gap-2 pa-4">
          <v-btn variant="text" color="grey" size="small" @click="dialogConfirmar = false">
            Cancelar
          </v-btn>
          <v-btn color="primary" size="small" :loading="loading" @click="confirmarEnvio">
            <v-icon start size="16">mdi-send</v-icon>
            Confirmar envio
          </v-btn>
        </div>
      </v-card>
    </v-dialog>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const loading              = ref(false)
const errorMessage         = ref('')
const successMessage       = ref('')
const resultDetails        = ref(null)
const lastEnvioData        = ref(null)
const dialogConfirmar      = ref(false)

const condominios           = ref([])
const loadingCondominios    = ref(false)
const selectedCondominioIds = ref([])

const templates            = ref([])
const loadingTemplates     = ref(false)
const selectedTemplateId   = ref(null)

const unidades             = ref([])
const loadingUnidades      = ref(false)
const selectedUnidades     = ref([])

const selectedTemplate = computed(() =>
  templates.value.find(t => t.id === selectedTemplateId.value) || null
)

const unidadesComNumero = computed(() => unidades.value.filter(u => u.tem_numero))
const unidadesSemNumero = computed(() => unidades.value.filter(u => !u.tem_numero))

const todasSelecionadas = computed(() =>
  unidadesComNumero.value.length > 0 &&
  selectedUnidades.value.length === unidadesComNumero.value.length
)

const envioFailures = computed(() => {
  if (!resultDetails.value?.failures) return []
  return resultDetails.value.failures.filter(f => f.phone && f.phone !== '-' && f.phone !== '—')
})

const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` })

const friendlyError = (error) => {
  if (!error) return 'Não foi possível enviar'
  const e = error.toLowerCase()
  if (e.includes('instance does not exist') || e.includes('instance')) return 'WhatsApp não conectado'
  if (error.includes('400') || error.includes('404')) return 'Número sem WhatsApp'
  if (error.includes('500')) return 'Erro interno'
  if (e.includes('timeout') || e.includes('timed out')) return 'Tempo de conexão esgotado'
  return 'Não foi possível enviar'
}

const renderPreview = (body) =>
  body
    .replace(/\{\{condominio\}\}/g, 'Residencial Acácias')
    .replace(/\{\{unidade\}\}/g, '315 SALA')
    .replace(/\{\{nome\}\}/g, 'João Silva')
    .replace(/\{\{qtd\}\}/g, '5')
    .replace(/\{\{competencia\}\}/g, '10/2025')
    .replace(/\{\{vencimento\}\}/g, '01/11/2025')
    .replace(/\{\{valor\}\}/g, 'R$ 1.250,00')

const toggleSelecionarTodas = () => {
  if (todasSelecionadas.value) {
    selectedUnidades.value = []
  } else {
    selectedUnidades.value = unidadesComNumero.value.map(u => u.id_unidade)
  }
}

const selecionarTresMais = () => {
  selectedUnidades.value = unidadesComNumero.value
    .filter(u => (u.qtd_inadimplencias || 1) >= 3)
    .map(u => u.id_unidade)
}

const fetchTemplates = async () => {
  loadingTemplates.value = true
  try {
    const res = await fetch('/api/templates', { headers: authHeader() })
    if (res.ok) templates.value = await res.json()
  } catch (_) {}
  finally { loadingTemplates.value = false }
}

const fetchCondominios = async () => {
  loadingCondominios.value = true
  try {
    const res = await fetch('/api/admin/condominios', { headers: authHeader() })
    if (res.ok) {
      const lista = await res.json()
      condominios.value = lista
        .map(c => ({ id: c.id, label: `[${c.id}] ${c.nome}` }))
        .sort((a, b) => a.id - b.id)
    }
  } catch (_) {}
  finally { loadingCondominios.value = false }
}

const fetchUnidades = async (ids) => {
  if (!ids || !ids.length) { unidades.value = []; selectedUnidades.value = []; return }
  loadingUnidades.value = true
  unidades.value = []
  selectedUnidades.value = []
  try {
    const res = await fetch(
      `/api/messages/unidades-inadimplentes?id_condominio=${ids.join(',')}`,
      { headers: authHeader() }
    )
    if (res.ok) {
      unidades.value = await res.json()
      selectedUnidades.value = unidades.value
        .filter(u => u.tem_numero)
        .map(u => u.id_unidade)
    }
  } catch (_) {}
  finally { loadingUnidades.value = false }
}

const onCondominioChange = (val) => {
  resultDetails.value = null
  errorMessage.value = ''
  fetchUnidades(val)
}

const baixarRelatorio = async () => {
  if (!lastEnvioData.value) return
  const { condominioNome, templateNome, details, contatos } = lastEnvioData.value

  const falhas = (details.failures || [])
    .filter(f => f.phone && f.phone !== '-' && f.phone !== '—')
    .map(f => ({ phone: f.phone || '', error: f.error || '', unidade: f.unidade || '', nome: f.nome || '' }))

  const semNumeroResult = details.sem_numero || []
  const semNumeroKeys   = new Set(semNumeroResult.map(s => s.unidade))
  const semNumeroExtra  = unidadesSemNumero.value
    .filter(u => !semNumeroKeys.has(u.unidade))
    .map(u => ({ unidade: u.unidade, nome: u.nome, motivo: 'Sem número cadastrado' }))
  const semNumero = [...semNumeroResult, ...semNumeroExtra]

  const phonesFalharam = new Set(falhas.map(f => f.phone))
  const enviados = (contatos || [])
    .filter(c => !phonesFalharam.has(c.telefone || ''))
    .map(c => ({ unidade: c.unidade, nome: c.nome, telefone: c.telefone || '' }))

  try {
    const res = await fetch('/api/messages/relatorio-envio-pdf', {
      method: 'POST',
      headers: { ...authHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify({ condominio_nome: condominioNome, template_nome: templateNome || '', enviados, falhas, sem_numero: semNumero }),
    })
    if (!res.ok) throw new Error('Erro ao gerar PDF')
    const blob = await res.blob()
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = `relatorio_envio_${new Date().toISOString().slice(0,10)}.pdf`
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)
  } catch (e) {
    errorMessage.value = 'Erro ao gerar relatório PDF: ' + e.message
  }
}

const confirmarEnvio = () => {
  dialogConfirmar.value = false
  handleEnvio()
}

const handleEnvio = async () => {
  if (!selectedCondominioIds.value.length || selectedUnidades.value.length === 0) return
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  resultDetails.value = null

  try {
    const selectedSet = new Set(selectedUnidades.value)
    const porCondo = {}
    for (const u of unidades.value) {
      if (selectedSet.has(u.id_unidade)) {
        const cid = u.condominio_id
        if (!porCondo[cid]) porCondo[cid] = []
        porCondo[cid].push(u.id_unidade)
      }
    }

    const resultadoAgregado = { success: 0, failures: [], sem_numero: [] }
    const todoContatos = []

    for (const [cidStr, ids] of Object.entries(porCondo)) {
      let url = `/api/messages/send-selected?id_condominio=${cidStr}`
      if (selectedTemplateId.value) url += `&template_id=${selectedTemplateId.value}`
      url += `&unidades_ids=${ids.join(',')}`

      const res  = await fetch(url, { method: 'POST', headers: authHeader() })
      const data = await res.json()
      if (!res.ok) throw new Error(data.detail || 'Erro ao enviar mensagens')

      const d = data.details
      resultadoAgregado.success += d.success || 0
      resultadoAgregado.failures.push(...(d.failures || []))
      resultadoAgregado.sem_numero.push(...(d.sem_numero || []))

      const condoUnidades = unidades.value.filter(
        u => u.condominio_id === Number(cidStr) && ids.includes(u.id_unidade) && u.tem_numero
      )
      todoContatos.push(...condoUnidades.map(u => ({ ...u, telefone: u.telefone || '' })))
    }

    successMessage.value = 'Envio concluído!'
    resultDetails.value  = resultadoAgregado

    const nomesCondos = selectedCondominioIds.value
      .map(id => condominios.value.find(c => c.id === id)?.label || String(id))
      .join(', ')
    const templateSelecionado = templates.value.find(t => t.id === selectedTemplateId.value)
    lastEnvioData.value = {
      condominioNome: nomesCondos,
      templateNome:   templateSelecionado?.name || null,
      details:        resultadoAgregado,
      contatos:       todoContatos,
    }
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  fetchTemplates()
  fetchCondominios()
})
</script>

<style scoped>
/* ── Page header ── */
.page-icon {
  width: 42px; height: 42px;
  border-radius: 11px;
  background: linear-gradient(135deg, #34d399 0%, #059669 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(5,150,105,0.28);
  flex-shrink: 0; margin-right: 8px;
}
.page-title    { font-size: 1.2rem; font-weight: 700; line-height: 1.3; margin: 0; }
.page-subtitle { font-size: 0.82rem; opacity: .55; margin: 2px 0 0; }

/* ── Section card ── */
.section-card { border-radius: 14px !important; overflow: hidden; }

.section-header {
  background: linear-gradient(135deg, #059669 0%, #34d399 100%);
  padding: 14px 20px;
  display: flex; align-items: center; gap: 14px;
}
.section-badge {
  width: 28px; height: 28px; border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex; align-items: center; justify-content: center;
  color: white; font-weight: 700; font-size: 0.85rem;
  flex-shrink: 0;
}
.section-title    { color: white; font-weight: 600; font-size: 0.92rem; margin: 0; }
.section-subtitle { color: rgba(255,255,255,0.7); font-size: 0.78rem; margin: 2px 0 0; }

/* ── Unit row ── */
.unit-row {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px;
  transition: background 0.1s;
}
.unit-row--even { background: rgba(0,0,0,0.025); }
.unit-row:hover { background: rgba(5,150,105,0.05); }
.unit-info { flex: 1; min-width: 0; }
.unit-name { font-size: 0.875rem; }
.unit-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.unit-valor { font-size: 0.85rem; font-weight: 700; color: rgb(var(--v-theme-primary)); }

/* ── Result card ── */
.result-card { border-radius: 14px !important; overflow: hidden; }
.result-header {
  background: linear-gradient(135deg, #059669 0%, #34d399 100%);
  padding: 14px 20px;
  display: flex; align-items: center;
  color: white; font-weight: 600; font-size: 0.92rem;
}
.stat-box { text-align: center; padding: 12px; border-radius: 10px; }
.stat-box--success { background: rgba(5,150,105,0.08); }
.stat-box--error   { background: rgba(198,40,40,0.08); }
.stat-box--warn    { background: rgba(245,127,23,0.08); }
.stat-num   { font-size: 1.6rem; font-weight: 800; margin: 0; line-height: 1; }
.stat-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: .05em; opacity: .6; margin: 4px 0 0; }
.stat-box--success .stat-num { color: #059669; }
.stat-box--error   .stat-num { color: #c62828; }
.stat-box--warn    .stat-num { color: #e65100; }

/* ── Confirmation dialog ── */
.confirm-card { overflow: hidden; }

.dialog-header {
  padding: 16px 20px;
  background: rgb(var(--v-theme-surface));
  border-left: 3px solid #34d399;
  border-bottom: 1px solid rgba(var(--v-border-color), var(--v-border-opacity));
}
.confirm-title    { font-weight: 700; font-size: 0.95rem; margin: 0; color: rgb(var(--v-theme-on-surface)); }
.confirm-subtitle { font-size: 0.75rem; opacity: .5; margin: 2px 0 0; }
.confirm-divider  { opacity: 0.08; }

/* Itens de resumo */
.confirm-items { display: flex; flex-direction: column; gap: 2px; }
.confirm-item {
  display: flex; align-items: center; justify-content: space-between;
  padding: 9px 12px; border-radius: 8px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-border-color), 0.06);
}
.confirm-item + .confirm-item { margin-top: 4px; }
.confirm-item__left {
  display: flex; align-items: center;
  font-size: 0.82rem; opacity: .65;
}
.confirm-item__val {
  font-size: 0.83rem; font-weight: 600;
  color: rgb(var(--v-theme-on-surface));
}
.confirm-item__val--green { color: #059669; font-size: 0.95rem; }
.confirm-item__val--red   { color: #dc2626; }

/* Avisos inline */
.confirm-notice {
  display: flex; align-items: flex-start;
  padding: 9px 12px; border-radius: 8px;
  font-size: 0.78rem; line-height: 1.45;
  background: rgba(var(--v-theme-primary), 0.06);
  color: rgb(var(--v-theme-on-surface));
  opacity: .85;
}
.confirm-notice--warn { background: rgba(217, 119, 6, 0.08); }
</style>
