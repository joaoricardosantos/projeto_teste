<template>
  <v-container fluid>
    <v-row justify="center">
      <v-col cols="12" sm="11" md="9" lg="7">
        <v-card elevation="8">
          <v-card-title class="text-h5 font-weight-bold pa-4">
            Enviar Mensagens
          </v-card-title>
          <v-card-text class="pa-4">

            <!-- Seleção de Condomínio -->
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
              prepend-icon="mdi-office-building"
              class="mb-2"
              :loading="loadingCondominios"
              :disabled="loadingCondominios || loading"
              no-data-text="Nenhum condomínio encontrado"
              placeholder="Buscar por nome ou ID..."
              :hint="loadingCondominios ? 'Buscando condomínios...' : condominios.length > 0 ? condominios.length + ' condomínios disponíveis' : ''"
              persistent-hint
              @update:model-value="onCondominioChange"
            />

            <!-- Seleção de Template -->
            <v-select
              v-model="selectedTemplateId"
              :items="templates"
              item-title="name"
              item-value="id"
              label="Template de mensagem"
              variant="outlined"
              density="comfortable"
              clearable
              prepend-icon="mdi-message-text"
              class="mb-2 mt-2"
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
                color="grey-lighten-4"
                rounded
                class="pa-3 mb-4 mt-2"
                style="font-size: 0.85rem; white-space: pre-wrap; word-break: break-word;"
              >
                <p class="text-caption text-medium-emphasis mb-1">Pré-visualização:</p>
                {{ renderPreview(selectedTemplate.body) }}
              </v-sheet>
            </v-expand-transition>

            <!-- Lista de unidades inadimplentes -->
            <v-expand-transition>
              <div v-if="unidades.length > 0 || loadingUnidades" class="mb-4 mt-2">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-subtitle-2 font-weight-bold">
                    Unidades inadimplentes
                    <v-chip v-if="unidades.length" size="x-small" color="primary" class="ml-1">
                      {{ unidades.length }}
                    </v-chip>
                  </span>
                  <div class="d-flex" style="gap:8px;">
                    <v-btn
                      v-if="unidades.length"
                      size="small"
                      variant="tonal"
                      color="warning"
                      @click="selecionarTresMais"
                    >
                      3+ cobranças
                    </v-btn>
                    <v-btn
                      v-if="unidades.length"
                      size="small"
                      variant="tonal"
                      color="primary"
                      @click="toggleSelecionarTodas"
                    >
                      {{ todasSelecionadas ? 'Desmarcar todas' : 'Marcar todas' }}
                    </v-btn>
                  </div>
                </div>

                <!-- Loading unidades -->
                <div v-if="loadingUnidades" class="d-flex align-center justify-center pa-6">
                  <v-progress-circular indeterminate color="primary" size="32" class="mr-3" />
                  <span class="text-body-2 text-medium-emphasis">Buscando inadimplentes...</span>
                </div>

                <!-- Tabela de unidades -->
                <v-sheet v-else border rounded>
                  <v-list density="compact" class="pa-0">
                    <v-list-item
                      v-for="(u, i) in unidades"
                      :key="u.id_unidade"
                      :class="i % 2 === 0 ? 'bg-grey-lighten-5' : ''"
                      style="min-height: 48px;"
                    >
                      <template #prepend>
                        <v-checkbox
                          v-model="selectedUnidades"
                          :value="u.id_unidade"
                          hide-details
                          density="compact"
                          :disabled="!u.tem_numero"
                        />
                      </template>

                      <v-list-item-title class="text-body-2">
                        <strong>{{ u.unidade }}</strong>
                        <span class="text-medium-emphasis ml-1">— {{ u.nome }}</span>
                        <v-chip
                          v-if="u.qtd_inadimplencias > 1"
                          size="x-small"
                          color="warning"
                          variant="tonal"
                          class="ml-1"
                        >{{ u.qtd_inadimplencias }} cobranças</v-chip>
                      </v-list-item-title>

                      <template #append>
                        <div class="d-flex align-center" style="gap:8px;">
                          <span class="text-caption font-weight-bold text-primary">{{ u.valor }}</span>
                          <v-chip
                            v-if="!u.tem_numero"
                            size="x-small"
                            color="error"
                            variant="tonal"
                          >
                            Sem número
                          </v-chip>
                        </div>
                      </template>
                    </v-list-item>
                  </v-list>
                </v-sheet>

                <p v-if="!loadingUnidades && unidades.length" class="text-caption text-medium-emphasis mt-1">
                  {{ selectedUnidades.length }} de {{ unidadesComNumero.length }} selecionadas
                  <span v-if="unidadesSemNumero.length" class="ml-2 text-error">
                    · {{ unidadesSemNumero.length }} sem número
                  </span>
                </p>
              </div>
            </v-expand-transition>

            <!-- Erros -->
            <v-alert v-if="errorMessage" type="error" class="mt-4" closable @click:close="errorMessage = ''">
              {{ errorMessage }}
            </v-alert>

            <!-- Resultado -->
            <v-alert
              v-if="resultDetails"
              type="success"
              class="mt-4"
              closable
              @click:close="resultDetails = null; successMessage = ''"
            >
              <div class="font-weight-bold mb-2">{{ successMessage }}</div>
              <div>✅ Enviados com sucesso: <strong>{{ resultDetails.success }}</strong></div>
              <div>❌ Falhas no envio: <strong>{{ envioFailures.length }}</strong></div>
              <div>📵 Sem número cadastrado: <strong>{{ resultDetails.sem_numero?.length || 0 }}</strong></div>

              <div v-if="resultDetails.sem_numero?.length" class="mt-3">
                <div class="text-caption font-weight-bold text-medium-emphasis mb-1">📵 Unidades sem número:</div>
                <v-sheet color="orange-lighten-5" rounded class="pa-2">
                  <div
                    v-for="(f, i) in resultDetails.sem_numero"
                    :key="i"
                    class="text-caption py-1"
                    :style="i < resultDetails.sem_numero.length - 1 ? 'border-bottom: 1px solid rgba(0,0,0,0.08)' : ''"
                  >
                    <strong>{{ f.unidade }}</strong>
                    <span v-if="f.nome"> — {{ f.nome }}</span>
                  </div>
                </v-sheet>
              </div>

              <div v-if="envioFailures.length" class="mt-3">
                <div class="text-caption font-weight-bold text-medium-emphasis mb-1">❌ Falhas no envio:</div>
                <div v-for="f in envioFailures" :key="f.phone" class="text-caption">
                  <strong>{{ f.unidade || f.phone }}</strong>
                  <span v-if="f.nome"> — {{ f.nome }}</span>
                  : {{ friendlyError(f.error) }}
                </div>
              </div>
            </v-alert>

            <v-btn
              v-if="resultDetails"
              color="grey-darken-1"
              block
              size="large"
              class="mt-3"
              variant="outlined"
              @click="baixarRelatorio"
            >
              <v-icon start>mdi-file-pdf-box</v-icon>
              Baixar relatório de envio (PDF)
            </v-btn>

            <v-btn
              color="primary"
              block
              size="large"
              class="mt-3"
              :loading="loading"
              :disabled="!selectedCondominioIds.length || loadingCondominios || loadingUnidades || selectedUnidades.length === 0"
              @click="handleEnvio"
            >
              <v-icon start>mdi-whatsapp</v-icon>
              Enviar para {{ selectedUnidades.length }} unidade{{ selectedUnidades.length !== 1 ? 's' : '' }}
            </v-btn>

          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const loading              = ref(false)
const errorMessage         = ref('')
const successMessage       = ref('')
const resultDetails        = ref(null)
const lastEnvioData        = ref(null)

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
    .map(f => ({
      phone:   f.phone   || '',
      error:   f.error   || '',
      unidade: f.unidade || '',
      nome:    f.nome    || '',
    }))

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
      body: JSON.stringify({
        condominio_nome: condominioNome,
        template_nome:   templateNome || '',
        enviados,
        falhas,
        sem_numero: semNumero,
      }),
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

const handleEnvio = async () => {
  if (!selectedCondominioIds.value.length || selectedUnidades.value.length === 0) return
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  resultDetails.value = null

  try {
    // Agrupar unidades selecionadas por condomínio
    const selectedSet = new Set(selectedUnidades.value)
    const porCondo = {}
    for (const u of unidades.value) {
      if (selectedSet.has(u.id_unidade)) {
        const cid = u.condominio_id
        if (!porCondo[cid]) porCondo[cid] = []
        porCondo[cid].push(u.id_unidade)
      }
    }

    // Enviar uma chamada por condomínio e acumular resultados
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
