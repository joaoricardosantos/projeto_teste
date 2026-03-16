<template>
  <v-container>

    <!-- Abas -->
    <v-tabs v-model="aba" color="primary" class="mb-4">
      <v-tab value="visao">📊 Visão Geral</v-tab>
      <v-tab value="campanhas">📨 Campanhas</v-tab>
    </v-tabs>

    <v-window v-model="aba">
      <v-window-item value="visao">

        <!-- Cabeçalho -->
        <div class="dash-header mb-4">
          <!-- Linha 1: título + ações -->
          <div class="d-flex align-center justify-space-between flex-wrap gap-3">
            <div>
              <h1 class="text-h5 font-weight-bold">Dashboard de Inadimplência</h1>
              <p class="text-body-2 text-medium-emphasis mt-1">
                Visão geral consolidada de todos os condomínios.
                <span v-if="dados">
                  Gerado em {{ dados.gerado_em }}
                  <v-chip v-if="dados.cache" size="x-small" color="blue" variant="tonal" class="ml-1">
                    <v-icon size="10" class="mr-1">mdi-lightning-bolt</v-icon>cache
                  </v-chip>
                </span>
              </p>
            </div>

            <!-- Ações -->
            <div class="d-flex align-center gap-2 flex-wrap">
              <!-- Toggle 5 anos — mesmo tamanho dos botões ao lado -->
              <v-btn
                :color="ultimos5anos ? 'primary' : 'default'"
                :variant="ultimos5anos ? 'flat' : 'outlined'"
                prepend-icon="mdi-calendar-clock"
                @click="toggleFiltro"
              >
                Últimos 5 anos
              </v-btn>

              <v-text-field
                v-model="dataPosicao"
                type="date"
                label="Data de posição"
                variant="outlined"
                density="compact"
                hide-details
                clearable
                style="max-width: 170px"
              />
              <v-btn
                color="primary"
                :loading="loading"
                prepend-icon="mdi-refresh"
                @click="carregar(false)"
              >
                Atualizar
              </v-btn>
              <v-btn
                color="secondary"
                variant="outlined"
                :loading="loading"
                prepend-icon="mdi-refresh-circle"
                @click="carregar(true)"
                title="Ignorar cache e buscar dados novos"
              >
                Forçar
              </v-btn>
            </div>
          </div>
        </div>

        <!-- Erro -->
        <v-alert v-if="erro" type="error" class="mb-4" closable @click:close="erro = ''">
          {{ erro }}
        </v-alert>

        <!-- Loading: sempre esconde os dados e mostra spinner enquanto carrega -->
        <Transition name="dados-fade" mode="out-in">
          <div v-if="loading" key="loading" class="d-flex flex-column align-center justify-center my-16">
            <v-progress-circular indeterminate color="primary" size="56" />
            <p class="text-body-2 text-medium-emphasis mt-4">Consultando todos os condomínios...</p>
            <p class="text-caption text-medium-emphasis">Isso pode levar alguns minutos</p>
          </div>

          <div v-else-if="dados" key="dados">

          <!-- KPI Cards -->
          <v-row class="mb-4">

            <!-- Total inadimplência -->
            <v-col cols="12" sm="6" md="3">
              <v-card elevation="4" class="pa-5" style="border-left: 4px solid #006837;">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Total Inadimplência</span>
                  <v-icon color="primary" size="28">mdi-currency-brl</v-icon>
                </div>
                <div class="text-h5 font-weight-bold text-primary">{{ brl(dados.total_inadimplencia) }}</div>
                <div class="text-caption text-medium-emphasis mt-1">{{ dados.total_unidades }} unidades inadimplentes</div>
              </v-card>
            </v-col>

            <!-- Condomínios -->
            <v-col cols="12" sm="6" md="3">
              <v-card elevation="4" class="pa-5" style="border-left: 4px solid #1976D2;">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Condomínios</span>
                  <v-icon color="blue" size="28">mdi-office-building</v-icon>
                </div>
                <div class="text-h5 font-weight-bold" style="color: #1976D2;">{{ dados.total_condominios }}</div>
                <div class="text-caption text-medium-emphasis mt-1">com inadimplência ativa</div>
              </v-card>
            </v-col>

            <!-- Maior inadimplente -->
            <v-col cols="12" sm="6" md="3">
              <v-card elevation="4" class="pa-5" style="border-left: 4px solid #F57C00;">
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Maior Devedor</span>
                  <v-icon color="orange-darken-2" size="28">mdi-podium-gold</v-icon>
                </div>
                <div class="text-body-2 font-weight-bold" style="color: #F57C00; line-height: 1.3;">
                  {{ dados.maior_condo_nome || '—' }}
                </div>
                <div class="text-caption text-medium-emphasis mt-1">{{ brl(dados.maior_condo_valor) }}</div>
              </v-card>
            </v-col>

            <!-- Sem número -->
            <v-col cols="12" sm="6" md="3">
              <v-card
                elevation="4"
                class="pa-5"
                style="border-left: 4px solid #D32F2F; cursor: pointer;"
                @click="dialogSemNumero = true"
              >
                <div class="d-flex align-center justify-space-between mb-2">
                  <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Sem Número</span>
                  <v-icon color="red-darken-2" size="28">mdi-phone-off</v-icon>
                </div>
                <div class="text-h5 font-weight-bold" style="color: #D32F2F;">{{ dados.sem_numero_count }}</div>
                <div class="text-caption mt-1" style="color: #D32F2F;">
                  <v-icon size="12">mdi-eye</v-icon> clique para ver detalhes
                </div>
              </v-card>
            </v-col>

          </v-row>

          <!-- Ranking condomínios -->
          <v-card elevation="4">
            <v-card-title class="pa-4 pb-2 d-flex align-center">
              <v-icon class="mr-2" color="primary">mdi-chart-bar</v-icon>
              Ranking de Inadimplência por Condomínio
            </v-card-title>
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
                    size="x-small"
                    variant="tonal"
                  >{{ index + 1 }}º</v-chip>
                </template>
                <template #item.valor="{ item }">
                  <span class="font-weight-bold text-primary">{{ brl(item.valor) }}</span>
                </template>
                <template #item.percentual="{ item }">
                  <div class="pct-cell">
                    <div class="pct-bar-bg">
                      <div
                        class="pct-bar-fill"
                        :style="{ width: pctWidth(item.percentual) }"
                      />
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

      <!-- ── Aba Campanhas ── -->
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
          <v-chip color="red-darken-2" variant="tonal" size="small">
            {{ dados?.sem_numero_count || 0 }} unidades
          </v-chip>
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
            <template #item.nome="{ item }">
              {{ item.nome || '—' }}
            </template>
          </v-data-table>
        </v-card-text>
        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="dialogSemNumero = false">Fechar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
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

// Cache local por chave — evita rebuscar ao alternar filtro
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

// Busca dados da API e salva no cache local
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
    // Limpa cache do servidor e local
    await fetch('/api/admin/dashboard/clear-cache', { method: 'POST', headers: authHeader() })
    Object.keys(localCache).forEach(k => delete localCache[k])
  }

  // Se está no cache local, usa direto (sem mostrar loading)
  if (!forceRefresh && localCache[key]) {
    dados.value = localCache[key]
    // Pré-carrega oposto em background
    preCarregarOposto()
    return
  }

  // Precisa buscar: mostra loading e esconde dados
  loading.value = true
  dados.value   = null
  erro.value    = ''
  try {
    dados.value = await fetchDados(ultimos5anos.value)
    // Pré-carrega oposto em background
    preCarregarOposto()
  } catch (e) {
    erro.value = e.message
  } finally {
    loading.value = false
  }
}

// Ao clicar no toggle
const toggleFiltro = async () => {
  ultimos5anos.value = !ultimos5anos.value
  const key = cacheKey()

  if (localCache[key]) {
    // Cache disponível — troca instantânea com animação (loading breve para acionar o fade)
    loading.value = true
    dados.value   = null
    await new Promise(r => setTimeout(r, 120))
    dados.value   = localCache[key]
    loading.value = false
  } else {
    // Precisa buscar — mostra loading completo
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

// Pré-carrega o estado oposto silenciosamente em background
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

// Percentual máximo da lista (1º item, já ordenado desc pelo backend)
const maxPercentual = computed(() => {
  if (!rankingCondominios.value.length) return 100
  return rankingCondominios.value[0].percentual || 100
})

// Largura CSS proporcional: o maior item = 100%, os demais são relativos a ele
const pctWidth = (pct) => {
  return ((pct / maxPercentual.value) * 100).toFixed(2) + '%'
}

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
/* ── Barra de percentual ── */
.pct-cell {
  display: flex;
  align-items: center;
  gap: 10px;
  width: 100%;
  padding-right: 4px;
}
.pct-bar-bg {
  flex: 1;
  height: 8px;
  background: rgba(0, 104, 55, 0.1);
  border-radius: 99px;
  overflow: hidden;
  min-width: 80px;
}
.pct-bar-fill {
  height: 100%;
  border-radius: 99px;
  background: linear-gradient(90deg, #006837, #00a651);
  transition: width 0.4s ease;
}
.pct-label {
  font-size: 12px;
  font-weight: 600;
  color: rgb(var(--v-theme-primary));
  min-width: 38px;
  text-align: right;
  flex-shrink: 0;
}



/* ── Transição suave ao trocar filtro ── */
.dados-fade-enter-active { transition: opacity 0.2s ease, transform 0.2s ease; }
.dados-fade-leave-active { transition: opacity 0.15s ease, transform 0.15s ease; }
.dados-fade-enter-from   { opacity: 0; transform: translateY(8px); }
.dados-fade-leave-to     { opacity: 0; transform: translateY(-4px); }
</style>