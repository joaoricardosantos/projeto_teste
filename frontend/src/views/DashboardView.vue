<template>
  <div>

    <!-- ── Abas ── -->
    <v-tabs v-model="aba" color="primary" class="mb-6" density="comfortable">
      <v-tab value="visao">
        <v-icon size="16" class="mr-2">mdi-chart-bar</v-icon>
        Visão Geral
      </v-tab>
      <v-tab value="campanhas">
        <v-icon size="16" class="mr-2">mdi-send-outline</v-icon>
        Campanhas
      </v-tab>
    </v-tabs>

    <v-window v-model="aba">
      <v-window-item value="visao">

        <!-- ── Cabeçalho ── -->
        <div class="d-flex align-center justify-space-between flex-wrap gap-3 mb-7">
          <div class="d-flex align-center gap-2">
            <div class="page-icon">
              <v-icon size="20" color="white">mdi-view-dashboard-outline</v-icon>
            </div>
            <div>
              <h1 class="page-title">Dashboard de Inadimplência</h1>
              <p class="page-subtitle">
                Visão consolidada de todos os condomínios
                <template v-if="dados">
                  · {{ dados.gerado_em }}
                  <v-chip v-if="dados.cache" size="x-small" color="primary" variant="tonal" class="ml-1">
                    <v-icon size="10" class="mr-1">mdi-lightning-bolt</v-icon>cache
                  </v-chip>
                </template>
              </p>
            </div>
          </div>

          <div class="d-flex align-center flex-wrap" style="gap: 7px;">
            <v-btn
              :color="ultimos5anos ? 'primary' : 'default'"
              :variant="ultimos5anos ? 'flat' : 'outlined'"
              size="default"
              prepend-icon="mdi-calendar-clock"
              @click="toggleFiltro"
            >Últimos 5 anos</v-btn>

            <v-btn
              variant="outlined"
              size="default"
              prepend-icon="mdi-calendar-today"
              @click="$refs.dateInput.showPicker()"
            >
              {{ dataPosicao ? dataPosicao.split('-').reverse().join('/') : 'Data de posição' }}
            </v-btn>
            <input
              ref="dateInput"
              v-model="dataPosicao"
              type="date"
              style="position:absolute;visibility:hidden;width:0;height:0;"
            />

            <v-btn size="default" color="primary" :loading="loading" prepend-icon="mdi-refresh" @click="carregar(false)">
              Atualizar
            </v-btn>
            <v-btn size="default" variant="outlined" :loading="loading" prepend-icon="mdi-refresh-circle" @click="carregar(true)">
              Forçar
            </v-btn>
          </div>
        </div>

        <!-- Erro -->
        <v-alert v-if="erro" type="error" class="mb-4" closable @click:close="erro = ''">{{ erro }}</v-alert>

        <!-- Conteúdo -->
        <Transition name="dados-fade" mode="out-in">
          <div v-if="loading" key="loading" class="d-flex flex-column align-center justify-center my-16">
            <v-progress-circular indeterminate color="primary" size="56" />
            <p class="text-body-2 text-medium-emphasis mt-4">Consultando todos os condomínios...</p>
            <p class="text-caption text-medium-emphasis">Isso pode levar alguns minutos</p>
          </div>

          <div v-else-if="dados" key="dados">

            <!-- KPI Cards -->
            <v-row class="mb-6" align="stretch">
              <v-col cols="12" sm="6" md="3">
                <v-card class="kpi-card" elevation="3">
                  <div class="kpi-icon-wrap" style="background: linear-gradient(135deg, #00c853 0%, #006837 100%);">
                    <v-icon color="white" size="22">mdi-currency-brl</v-icon>
                  </div>
                  <p class="kpi-label">Total Inadimplência</p>
                  <p class="kpi-value text-primary">{{ brl(dados.total_inadimplencia) }}</p>
                  <p class="kpi-desc">{{ dados.total_unidades }} unidades inadimplentes</p>
                </v-card>
              </v-col>

              <v-col cols="12" sm="6" md="3">
                <v-card class="kpi-card" elevation="3">
                  <div class="kpi-icon-wrap" style="background: linear-gradient(135deg, #42a5f5 0%, #1565c0 100%);">
                    <v-icon color="white" size="22">mdi-office-building</v-icon>
                  </div>
                  <p class="kpi-label">Condomínios</p>
                  <p class="kpi-value" style="color:#1976D2;">{{ dados.total_condominios }}</p>
                  <p class="kpi-desc">com inadimplência ativa</p>
                </v-card>
              </v-col>

              <v-col cols="12" sm="6" md="3">
                <v-card class="kpi-card" elevation="3">
                  <div class="kpi-icon-wrap" style="background: linear-gradient(135deg, #ffb74d 0%, #e65100 100%);">
                    <v-icon color="white" size="22">mdi-podium-gold</v-icon>
                  </div>
                  <p class="kpi-label">Maior Devedor</p>
                  <p class="kpi-value kpi-value--sm" style="color:#F57C00;">{{ dados.maior_condo_nome || '—' }}</p>
                  <p class="kpi-desc">{{ brl(dados.maior_condo_valor) }}</p>
                </v-card>
              </v-col>

              <v-col cols="12" sm="6" md="3">
                <v-card class="kpi-card kpi-card--clickable" elevation="3" @click="dialogSemNumero = true">
                  <div class="kpi-icon-wrap" style="background: linear-gradient(135deg, #ef9a9a 0%, #c62828 100%);">
                    <v-icon color="white" size="22">mdi-phone-off</v-icon>
                  </div>
                  <p class="kpi-label">Sem Número</p>
                  <p class="kpi-value" style="color:#D32F2F;">{{ dados.sem_numero_count }}</p>
                  <p class="kpi-desc" style="color:#D32F2F;">
                    <v-icon size="11" class="mr-1">mdi-eye-outline</v-icon>Ver detalhes
                  </p>
                </v-card>
              </v-col>
            </v-row>

            <!-- Ranking -->
            <v-card elevation="3" class="overflow-hidden">
              <div class="card-header-bar">
                <div class="d-flex align-center gap-2">
                  <v-icon color="white" size="18">mdi-chart-bar</v-icon>
                  <span class="card-header-title">Ranking de Inadimplência por Condomínio</span>
                </div>
                <v-chip size="small" variant="tonal" color="white" style="color:white;">
                  {{ rankingCondominios.length }} condomínios
                </v-chip>
              </div>

              <v-card-text class="pa-0">
                <v-data-table
                  :headers="headersRanking"
                  :items="rankingCondominios"
                  :items-per-page="15"
                  density="comfortable"
                  class="elevation-0"
                  no-data-text="Nenhum dado disponível"
                >
                  <template #item.posicao="{ index }">
                    <v-chip
                      :color="index === 0 ? 'amber-darken-2' : index === 1 ? 'grey' : index === 2 ? 'brown-lighten-1' : 'default'"
                      size="x-small" variant="tonal"
                    >{{ index + 1 }}º</v-chip>
                  </template>
                  <template #item.valor="{ item }">
                    <span class="font-weight-bold text-primary">{{ brl(item.valor) }}</span>
                  </template>
                  <template #item.percentual="{ item }">
                    <div class="pct-cell">
                      <div class="pct-bar-bg">
                        <div class="pct-bar-fill" :style="{ width: pctWidth(item.percentual) }" />
                      </div>
                      <span class="pct-label">{{ item.percentual.toFixed(1) }}%</span>
                    </div>
                  </template>
                </v-data-table>
              </v-card-text>
            </v-card>

          </div>
        </Transition>

      </v-window-item>

      <v-window-item value="campanhas">
        <CampanhasAba />
      </v-window-item>
    </v-window>

    <!-- ── Dialog: Sem número ── -->
    <v-dialog v-model="dialogSemNumero" max-width="800" scrollable>
      <v-card>
        <v-card-title class="pa-4 d-flex align-center">
          <v-icon class="mr-2" color="red-darken-2">mdi-phone-off</v-icon>
          Unidades sem número cadastrado
          <v-spacer />
          <v-chip color="red-darken-2" variant="tonal" size="small">{{ dados?.sem_numero_count || 0 }} unidades</v-chip>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-0">
          <div class="pa-4 pb-2">
            <v-text-field
              v-model="buscaSemNumero"
              placeholder="Buscar por condomínio, unidade ou nome..."
              variant="outlined"
              density="compact"
              prepend-inner-icon="mdi-magnify"
              clearable
              hide-details
            />
          </div>
          <v-data-table
            :headers="headersSemNumero"
            :items="semNumeroFiltrado"
            :items-per-page="15"
            density="comfortable"
            class="elevation-0"
            no-data-text="Nenhuma unidade encontrada"
          >
            <template #item.unidade="{ item }">
              <v-chip size="x-small" color="primary" variant="tonal">{{ item.unidade }}</v-chip>
            </template>
            <template #item.nome="{ item }">{{ item.nome || '—' }}</template>
          </v-data-table>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="dialogSemNumero = false">Fechar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import CampanhasAba from './CampanhasAba.vue'

const aba             = ref('visao')
const loading         = ref(false)
const erro            = ref('')
const dados           = ref(null)
const dataPosicao     = ref('')
const ultimos5anos    = ref(false)
const dialogSemNumero = ref(false)
const buscaSemNumero  = ref('')

const localCache = {}

const authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

const brl = (valor) => {
  try {
    return `R$ ${Number(valor).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`
  } catch {
    return `R$ ${valor}`
  }
}

const cacheKey = (filtro5a = ultimos5anos.value) => {
  const dp = dataPosicao.value || 'hoje'
  return `${dp}_${filtro5a ? '5a' : 'all'}`
}

const fetchDados = async (filtro5a) => {
  const params = new URLSearchParams()
  if (dataPosicao.value) {
    const [ano, mes, dia] = dataPosicao.value.split('-')
    params.append('data_posicao', `${dia}/${mes}/${ano}`)
  }
  if (filtro5a) params.append('ultimos_5_anos', 'true')
  const query = params.toString() ? `?${params.toString()}` : ''
  const res = await fetch(`/api/admin/dashboard${query}`, { headers: authHeader() })
  if (!res.ok) {
    const d = await res.json().catch(() => ({}))
    throw new Error(d.detail || 'Erro ao carregar dashboard')
  }
  const resultado = await res.json()
  localCache[cacheKey(filtro5a)] = resultado
  return resultado
}

const carregar = async (forceRefresh = false) => {
  const key = cacheKey()
  if (forceRefresh) {
    await fetch('/api/admin/dashboard/clear-cache', { method: 'POST', headers: authHeader() })
    Object.keys(localCache).forEach(k => delete localCache[k])
  }
  if (!forceRefresh && localCache[key]) {
    dados.value = localCache[key]
    preCarregarOposto()
    return
  }
  loading.value = true
  dados.value   = null
  erro.value    = ''
  try {
    dados.value = await fetchDados(ultimos5anos.value)
    preCarregarOposto()
  } catch (e) {
    erro.value = e.message
  } finally {
    loading.value = false
  }
}

const toggleFiltro = async () => {
  ultimos5anos.value = !ultimos5anos.value
  const key = cacheKey()
  if (localCache[key]) {
    loading.value = true
    dados.value   = null
    await new Promise(r => setTimeout(r, 120))
    dados.value   = localCache[key]
    loading.value = false
  } else {
    loading.value = true
    dados.value   = null
    erro.value    = ''
    try {
      dados.value = await fetchDados(ultimos5anos.value)
    } catch (e) {
      erro.value = e.message
    } finally {
      loading.value = false
    }
  }
  preCarregarOposto()
}

const preCarregarOposto = () => {
  const outroFiltro = !ultimos5anos.value
  const outraKey = cacheKey(outroFiltro)
  if (localCache[outraKey]) return
  fetchDados(outroFiltro).catch(() => {})
}

const headersRanking = [
  { title: '#',          key: 'posicao',    width: 70,  sortable: false },
  { title: 'Condomínio', key: 'nome',       sortable: true },
  { title: 'Total (R$)', key: 'valor',      width: 200, sortable: true },
  { title: '% do Total', key: 'percentual', width: 280, sortable: true },
]

const rankingCondominios = computed(() => {
  if (!dados.value?.condo_ranking) return []
  const total = dados.value.total_inadimplencia || 1
  return dados.value.condo_ranking.map(c => ({
    nome:       c.nome,
    valor:      c.valor,
    percentual: total > 0 ? (c.valor / total) * 100 : 0,
  }))
})

const maxPercentual = computed(() => {
  if (!rankingCondominios.value.length) return 100
  return rankingCondominios.value[0].percentual || 100
})

const pctWidth = (pct) => ((pct / maxPercentual.value) * 100).toFixed(2) + '%'

const headersSemNumero = [
  { title: 'Condomínio', key: 'condominio', sortable: true  },
  { title: 'Unidade',    key: 'unidade',    width: 120      },
  { title: 'Nome',       key: 'nome',       sortable: false },
]

const semNumeroFiltrado = computed(() => {
  if (!dados.value?.sem_numero) return []
  const q = buscaSemNumero.value.toLowerCase().trim()
  if (!q) return dados.value.sem_numero
  return dados.value.sem_numero.filter(u =>
    u.condominio.toLowerCase().includes(q) ||
    u.unidade.toLowerCase().includes(q) ||
    (u.nome || '').toLowerCase().includes(q)
  )
})

onMounted(carregar)
</script>

<style scoped>
/* ── Page header ── */
.page-icon {
  width: 42px; height: 42px;
  border-radius: 11px;
  background: linear-gradient(135deg, #00a651 0%, #006837 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(0,168,81,0.3);
  flex-shrink: 0; margin-right: 8px;
}
.page-title   { font-size: 1.2rem; font-weight: 700; line-height: 1.3; margin: 0; }
.page-subtitle { font-size: 0.82rem; color: rgb(var(--v-theme-on-surface)); opacity: .55; margin: 2px 0 0; }

/* ── KPI cards ── */
.kpi-card {
  padding: 24px !important;
  border-radius: 14px !important;
  display: flex;
  flex-direction: column;
  gap: 6px;
  height: 100%;
}
.kpi-card--clickable { cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }
.kpi-card--clickable:hover { transform: translateY(-2px); box-shadow: 0 8px 24px rgba(0,0,0,.12) !important; }

.kpi-icon-wrap {
  width: 48px; height: 48px;
  border-radius: 13px;
  display: flex; align-items: center; justify-content: center;
  margin-bottom: 10px;
  box-shadow: 0 4px 12px rgba(0,0,0,.18);
  flex-shrink: 0;
}
.kpi-label { font-size: 0.72rem; font-weight: 700; text-transform: uppercase; letter-spacing: .05em; opacity: .55; margin: 0 0 2px; }
.kpi-value { font-size: 1.65rem; font-weight: 800; line-height: 1.15; margin: 0; }
.kpi-value--sm { font-size: 1rem !important; line-height: 1.4 !important; display: -webkit-box; -webkit-line-clamp: 2; line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
.kpi-desc  { font-size: 0.75rem; opacity: .6; margin: 4px 0 0; }

/* ── Card header bar ── */
.card-header-bar {
  background: linear-gradient(135deg, #006837 0%, #00a651 100%);
  padding: 14px 20px;
  display: flex; align-items: center; justify-content: space-between;
}
.card-header-title { color: white; font-weight: 600; font-size: 0.92rem; }

/* ── Percentual bar ── */
.pct-cell { display: flex; align-items: center; gap: 10px; width: 100%; padding-right: 4px; }
.pct-bar-bg { flex: 1; height: 8px; background: rgba(0,104,55,.1); border-radius: 99px; overflow: hidden; min-width: 80px; }
.pct-bar-fill { height: 100%; border-radius: 99px; background: linear-gradient(90deg, #006837, #00a651); transition: width 0.4s ease; }
.pct-label { font-size: 12px; font-weight: 600; color: rgb(var(--v-theme-primary)); min-width: 38px; text-align: right; flex-shrink: 0; }

/* ── Transições ── */
.dados-fade-enter-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.dados-fade-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.dados-fade-enter-from   { opacity: 0; transform: translateY(8px); }
.dados-fade-leave-to     { opacity: 0; transform: translateY(-4px); }
</style>
