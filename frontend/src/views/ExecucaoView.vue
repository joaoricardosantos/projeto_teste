<template>
  <div>

    <!-- ── Cabeçalho ── -->
    <div class="d-flex align-center justify-space-between flex-wrap gap-3 mb-6">
      <div class="d-flex align-center gap-4">
        <div class="page-icon">
          <v-icon size="20" color="white">mdi-file-document-edit-outline</v-icon>
        </div>
        <div>
          <h1 class="page-title">Execução Condominial</h1>
          <p class="page-subtitle">Protocole ações de execução de taxas condominiais por unidade inadimplente</p>
        </div>
      </div>
    </div>

    <v-row justify="center">
      <v-col cols="12" xl="10">

        <!-- ── Passo 1: Selecionar condomínio ── -->
        <v-card class="section-card mb-4" elevation="3">
          <div class="section-header">
            <div class="section-badge">1</div>
            <div>
              <p class="section-title">Condomínio</p>
              <p class="section-subtitle">Selecione o condomínio para buscar as unidades inadimplentes</p>
            </div>
          </div>
          <div class="pa-5">
            <v-row align="center">
              <v-col cols="12" sm="8" md="7">
                <v-autocomplete
                  v-model="idCondominio"
                  :items="condominios"
                  item-title="label"
                  item-value="id"
                  label="Condomínio"
                  variant="outlined"
                  density="comfortable"
                  clearable
                  prepend-inner-icon="mdi-office-building"
                  :loading="loadingCondominios"
                  :disabled="loadingCondominios || loading"
                  no-data-text="Nenhum condomínio encontrado"
                  placeholder="Buscar por nome ou ID..."
                  :hint="loadingCondominios ? 'Buscando condomínios...' : condominios.length > 0 ? `${condominios.length} condomínios disponíveis` : ''"
                  persistent-hint
                  hide-details="auto"
                />
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <v-btn
                  color="primary" block size="large"
                  prepend-icon="mdi-magnify"
                  :loading="loading"
                  :disabled="!idCondominio || loading || loadingCondominios"
                  @click="buscarInadimplentes"
                >Buscar</v-btn>
              </v-col>
            </v-row>
            <v-alert v-if="erroBusca" type="error" class="mt-4" closable @click:close="erroBusca = ''">
              {{ erroBusca }}
            </v-alert>
          </div>
        </v-card>

        <!-- ── Passo 2: Selecionar unidades ── -->
        <v-expand-transition>
          <v-card v-if="unidades.length > 0" class="section-card mb-4" elevation="3">
            <div class="section-header">
              <div class="section-badge">2</div>
              <div class="flex-grow-1">
                <p class="section-title">
                  Unidades Inadimplentes — {{ nomeCondominio }}
                  <v-chip size="x-small" color="white" variant="tonal" class="ml-2" style="color:white;">
                    {{ unidades.length }}
                  </v-chip>
                </p>
                <p class="section-subtitle">Selecione as unidades que receberão o documento de execução</p>
              </div>
              <div class="d-flex gap-2 ml-auto">
                <v-btn size="x-small" variant="tonal" color="white" @click="selecionarTodas">
                  Todas
                </v-btn>
                <v-btn size="x-small" variant="tonal" color="white" @click="deselecionarTodas">
                  Limpar
                </v-btn>
              </div>
            </div>

            <div>
              <div
                v-for="(u, i) in unidades"
                :key="u.id_unidade"
                class="unit-row"
                :class="{ 'unit-row--even': i % 2 === 0 }"
                @click="toggleUnidade(u.id_unidade)"
                style="cursor: pointer;"
              >
                <v-checkbox
                  :model-value="unidadesSelecionadas.has(u.id_unidade)"
                  color="primary"
                  hide-details
                  density="compact"
                  @click.stop="toggleUnidade(u.id_unidade)"
                />
                <div class="unit-info">
                  <p class="unit-name font-weight-medium">
                    <span v-if="u.bloco" class="text-medium-emphasis mr-1">{{ u.bloco }} /</span>
                    {{ u.unidade }}
                  </p>
                  <p class="text-caption text-medium-emphasis">{{ u.nome }}</p>
                </div>
                <div class="unit-right">
                  <div class="text-right">
                    <p class="unit-valor">{{ u.valor }}</p>
                    <p class="text-caption text-medium-emphasis">{{ u.qtd_inadimplencias }} parcela(s)</p>
                  </div>
                  <v-chip
                    size="x-small"
                    :color="u.tem_numero ? 'success' : 'warning'"
                    variant="tonal"
                  >
                    {{ u.tem_numero ? 'Com tel.' : 'Sem tel.' }}
                  </v-chip>
                </div>
              </div>
            </div>

            <div class="pa-3 d-flex justify-space-between align-center" style="border-top: 1px solid rgba(0,0,0,0.07);">
              <span class="text-caption text-medium-emphasis">
                {{ unidadesSelecionadas.size }} de {{ unidades.length }} selecionada(s)
              </span>
            </div>
          </v-card>
        </v-expand-transition>

        <!-- ── Passo 3: Dados do condomínio (para o documento) ── -->
        <v-expand-transition>
          <v-card v-if="unidadesSelecionadas.size > 0" class="section-card mb-4" elevation="3">
            <div class="section-header">
              <div class="section-badge">3</div>
              <div>
                <p class="section-title">Dados do Condomínio</p>
                <p class="section-subtitle">Informações que aparecerão no documento de execução</p>
              </div>
            </div>
            <div class="pa-5">
              <v-row>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="dadosCondo.nome_condominio"
                    label="Nome do Condomínio *"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="mb-3"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="dadosCondo.cnpj"
                    label="CNPJ *"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="mb-3"
                    placeholder="00.000.000/0000-00"
                  />
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="dadosCondo.endereco"
                    label="Endereço do Condomínio *"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="mb-3"
                    placeholder="Rua Exemplo, 123, Bairro, Natal/RN"
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-text-field
                    v-model="dadosCondo.comarca"
                    label="Comarca *"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="mb-3"
                    placeholder="Natal"
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-text-field
                    v-model="dadosCondo.nome_sindico"
                    label="Nome do(a) Síndico(a) *"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="mb-3"
                  />
                </v-col>
                <v-col cols="12" md="4">
                  <v-text-field
                    v-model="dadosCondo.cpf_sindico"
                    label="CPF do(a) Síndico(a) *"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    class="mb-3"
                    placeholder="000.000.000-00"
                  />
                </v-col>
              </v-row>
            </div>
          </v-card>
        </v-expand-transition>

        <!-- ── Passo 4: Dados adicionais por unidade (CPF, e-mail) ── -->
        <v-expand-transition>
          <v-card v-if="unidadesSelecionadas.size > 0" class="section-card mb-4" elevation="3">
            <div class="section-header">
              <div class="section-badge">4</div>
              <div>
                <p class="section-title">Dados dos Executados</p>
                <p class="section-subtitle">CPF e e-mail das partes executadas (preencha os que estiverem em falta)</p>
              </div>
            </div>
            <div class="pa-5">
              <div
                v-for="u in unidadesSelecionadasLista"
                :key="u.id_unidade"
                class="mb-4 pb-4"
                style="border-bottom: 1px solid rgba(0,0,0,0.07);"
              >
                <p class="text-body-2 font-weight-bold mb-3">
                  <v-icon size="15" class="mr-1" color="primary">mdi-home-outline</v-icon>
                  Unidade {{ u.unidade }}<span v-if="u.bloco"> ({{ u.bloco }})</span> — {{ u.nome }}
                  <v-chip size="x-small" class="ml-2" color="error" variant="tonal">{{ u.valor }}</v-chip>
                </p>
                <v-row dense>
                  <v-col cols="12" sm="4">
                    <v-text-field
                      v-model="dadosExtras[u.id_unidade].cpf"
                      label="CPF"
                      variant="outlined"
                      density="compact"
                      hide-details
                      placeholder="000.000.000-00"
                    />
                  </v-col>
                  <v-col cols="12" sm="4">
                    <v-text-field
                      v-model="dadosExtras[u.id_unidade].telefone"
                      label="Telefone"
                      variant="outlined"
                      density="compact"
                      hide-details
                      :placeholder="u.telefone || '(00) 00000-0000'"
                    />
                  </v-col>
                  <v-col cols="12" sm="4">
                    <v-text-field
                      v-model="dadosExtras[u.id_unidade].email"
                      label="E-mail"
                      variant="outlined"
                      density="compact"
                      hide-details
                      placeholder="exemplo@email.com"
                    />
                  </v-col>
                </v-row>
              </div>
            </div>
          </v-card>
        </v-expand-transition>

        <!-- ── Ações ── -->
        <v-expand-transition>
          <div v-if="unidadesSelecionadas.size > 0" class="d-flex flex-column gap-3 mb-6">
            <v-alert v-if="erroGerar" type="error" closable @click:close="erroGerar = ''">
              {{ erroGerar }}
            </v-alert>
            <v-alert v-if="sucesso" type="success" closable @click:close="sucesso = ''">
              {{ sucesso }}
            </v-alert>

            <v-row>
              <v-col cols="12" sm="6">
                <v-btn
                  color="primary"
                  size="large"
                  block
                  :loading="gerandoDocx"
                  :disabled="!dadosCondoValidos || gerandoDocx || gerandoPdf"
                  prepend-icon="mdi-file-word-outline"
                  @click="gerarDocumentos('docx')"
                >
                  Baixar DOCX
                  <span class="text-caption ml-1 opacity-70">
                    ({{ unidadesSelecionadas.size }} unidade{{ unidadesSelecionadas.size !== 1 ? 's' : '' }})
                  </span>
                </v-btn>
              </v-col>
              <v-col cols="12" sm="6">
                <v-btn
                  color="error"
                  size="large"
                  block
                  :loading="gerandoPdf"
                  :disabled="!dadosCondoValidos || gerandoDocx || gerandoPdf"
                  prepend-icon="mdi-file-pdf-box"
                  @click="gerarDocumentos('pdf')"
                >
                  Baixar PDF
                  <span class="text-caption ml-1 opacity-70">
                    ({{ unidadesSelecionadas.size }} unidade{{ unidadesSelecionadas.size !== 1 ? 's' : '' }})
                  </span>
                </v-btn>
              </v-col>
            </v-row>

            <p class="text-caption text-medium-emphasis text-center">
              {{ unidadesSelecionadas.size > 1 ? 'Múltiplas unidades serão compactadas em um arquivo ZIP.' : 'O documento será baixado diretamente.' }}
            </p>
          </div>
        </v-expand-transition>

      </v-col>
    </v-row>

  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { useCondominios } from '../composables/useCondominios.js'

const authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

// ── Estado ──
const idCondominio       = ref(null)
const { condominios, loadingCondominios, carregarCondominios } = useCondominios()
const loading            = ref(false)
const gerandoDocx        = ref(false)
const gerandoPdf         = ref(false)
const erroBusca          = ref('')
const erroGerar          = ref('')
const sucesso            = ref('')

const nomeCondominio     = ref('')
const unidades           = ref([])
const unidadesSelecionadas = ref(new Set())

const dadosCondo = ref({
  nome_condominio: '',
  cnpj:            '',
  endereco:        '',
  comarca:         'Natal',
  nome_sindico:    '',
  cpf_sindico:     '',
})

const dadosExtras = ref({}) // id_unidade -> { cpf, telefone, email }

// ── Computed ──
const unidadesSelecionadasLista = computed(() =>
  unidades.value.filter(u => unidadesSelecionadas.value.has(u.id_unidade))
)

const dadosCondoValidos = computed(() =>
  dadosCondo.value.nome_condominio.trim() &&
  dadosCondo.value.cnpj.trim() &&
  dadosCondo.value.endereco.trim() &&
  dadosCondo.value.comarca.trim() &&
  dadosCondo.value.nome_sindico.trim() &&
  dadosCondo.value.cpf_sindico.trim()
)

// Garante inicialização de dadosExtras se alguma unidade não tiver sido inicializada
watch(unidadesSelecionadasLista, (lista) => {
  lista.forEach(u => {
    if (!dadosExtras.value[u.id_unidade]) {
      dadosExtras.value[u.id_unidade] = { cpf: u.cpf || '', telefone: u.telefone || '', email: '' }
    }
  })
})

// Nada — preenchimento automático ocorre dentro de buscarInadimplentes()

// ── Funções ──
const selecionarTodas   = () => { unidadesSelecionadas.value = new Set(unidades.value.map(u => u.id_unidade)) }
const deselecionarTodas = () => { unidadesSelecionadas.value = new Set() }

const toggleUnidade = (id) => {
  const s = new Set(unidadesSelecionadas.value)
  if (s.has(id)) s.delete(id)
  else s.add(id)
  unidadesSelecionadas.value = s
}

const buscarInadimplentes = async () => {
  if (!idCondominio.value) return
  loading.value   = true
  erroBusca.value = ''
  unidades.value  = []
  unidadesSelecionadas.value = new Set()

  try {
    const res  = await fetch(`/api/execucao/inadimplentes?id_condominio=${idCondominio.value}`, { headers: authHeader() })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || `Erro ${res.status}`)

    nomeCondominio.value = data.nome_condominio || ''
    unidades.value       = data.unidades || []

    // Preenche automaticamente dados do condomínio + síndico
    const dc = data.dados_condominio || {}
    dadosCondo.value = {
      nome_condominio: dc.nome_condominio || data.nome_condominio || '',
      cnpj:            dc.cnpj            || '',
      endereco:        dc.endereco        || '',
      comarca:         dadosCondo.value.comarca || 'Natal',
      nome_sindico:    dc.nome_sindico    || '',
      cpf_sindico:     dc.cpf_sindico     || '',
    }

    // Inicializa dados extras de cada unidade com CPF, telefone e e-mail da Superlógica
    const extras = {}
    for (const u of unidades.value) {
      extras[u.id_unidade] = {
        cpf:      u.cpf      || '',
        telefone: u.telefone || '',
        email:    u.email    || '',
      }
    }
    dadosExtras.value = extras

    if (!unidades.value.length) {
      erroBusca.value = 'Nenhuma unidade inadimplente encontrada para este condomínio.'
    }
  } catch (e) {
    erroBusca.value = e.message
  } finally {
    loading.value = false
  }
}

const _payload = () => ({
  condominio: dadosCondo.value,
  unidades: unidadesSelecionadasLista.value.map(u => {
    const extra = dadosExtras.value[u.id_unidade] || {}
    return {
      id_unidade: u.id_unidade,
      unidade:    u.unidade,
      bloco:      u.bloco || '',
      nome:       u.nome,
      valor:      u.valor,
      cpf:        extra.cpf      || u.cpf      || '',
      telefone:   extra.telefone || u.telefone || '',
      email:      extra.email    || '',
    }
  }),
})

const gerarDocumentos = async (tipo) => {
  if (!dadosCondoValidos.value || !unidadesSelecionadas.value.size) return

  const loading = tipo === 'docx' ? gerandoDocx : gerandoPdf
  loading.value   = true
  erroGerar.value = ''
  sucesso.value   = ''

  const endpoint = tipo === 'docx' ? '/api/execucao/gerar-docx' : '/api/execucao/gerar-pdf'
  const qtd      = unidadesSelecionadas.value.size
  const ext      = qtd === 1 ? tipo : 'zip'
  const nomeBase = qtd === 1
    ? `${unidadesSelecionadasLista.value[0].unidade}_execucao.${ext}`
    : `execucao_${tipo}_${new Date().toISOString().slice(0, 10)}.zip`

  try {
    const res = await fetch(endpoint, {
      method:  'POST',
      headers: { ...authHeader(), 'Content-Type': 'application/json' },
      body:    JSON.stringify(_payload()),
    })

    if (!res.ok) {
      const ct = res.headers.get('Content-Type') || ''
      if (ct.includes('application/json')) {
        const d = await res.json().catch(() => ({}))
        throw new Error(d.detail || `Erro ${res.status}`)
      }
      throw new Error(`Erro ${res.status}: falha ao gerar documentos`)
    }

    const blob = await res.blob()
    const url  = URL.createObjectURL(blob)
    const a    = document.createElement('a')
    a.href     = url
    a.download = nomeBase
    document.body.appendChild(a)
    a.click()
    a.remove()
    URL.revokeObjectURL(url)

    sucesso.value = `${tipo.toUpperCase()} gerado com sucesso para ${qtd} unidade(s).`
  } catch (e) {
    erroGerar.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(() => carregarCondominios())
</script>

<style scoped>
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

.section-card   { border-radius: 14px !important; overflow: hidden; }
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

.unit-row {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 16px;
  transition: background 0.1s;
}
.unit-row--even { background: rgba(0,0,0,0.025); }
.unit-row:hover { background: rgba(5,150,105,0.05); }
.unit-info  { flex: 1; min-width: 0; }
.unit-name  { font-size: 0.875rem; }
.unit-right { display: flex; align-items: center; gap: 8px; flex-shrink: 0; }
.unit-valor { font-size: 0.85rem; font-weight: 700; color: rgb(var(--v-theme-error)); }
</style>
