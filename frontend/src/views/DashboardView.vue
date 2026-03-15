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
        <v-row class="mb-4" align="center">
          <v-col cols="12" sm="7">
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
          </v-col>
          <v-col cols="12" sm="5" class="d-flex gap-2 justify-sm-end align-center flex-wrap">
            <v-text-field
              v-model="dataPosicao"
              type="date"
              label="Data de posição"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              style="max-width: 180px"
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
          </v-col>
        </v-row>

        <!-- Erro -->
        <v-alert v-if="erro" type="error" class="mb-4" closable @click:close="erro = ''">
          {{ erro }}
        </v-alert>

        <!-- Loading inicial -->
        <v-row v-if="loading && !dados" justify="center" class="my-16">
          <v-col cols="12" class="text-center">
            <v-progress-circular indeterminate color="primary" size="56" />
            <p class="text-body-2 text-medium-emphasis mt-4">Consultando todos os condomínios...</p>
            <p class="text-caption text-medium-emphasis">Isso pode levar alguns minutos</p>
          </v-col>
        </v-row>

        <template v-if="dados">

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

        </template>

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
const dialogSemNumero = ref(false)
const buscaSemNumero  = ref('')

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

const carregar = async (forceRefresh = false) => {
  loading.value = true
  erro.value    = ''
  try {
    if (forceRefresh) {
      await fetch('/api/admin/dashboard/clear-cache', {
        method:  'POST',
        headers: authHeader(),
      })
    }
    const params = new URLSearchParams()
    if (dataPosicao.value) {
      const [ano, mes, dia] = dataPosicao.value.split('-')
      params.append('data_posicao', `${dia}/${mes}/${ano}`)
    }
    const query = params.toString() ? `?${params.toString()}` : ''
    const res = await fetch(`/api/admin/dashboard${query}`, { headers: authHeader() })
    if (!res.ok) {
      const d = await res.json().catch(() => ({}))
      throw new Error(d.detail || 'Erro ao carregar dashboard')
    }
    dados.value = await res.json()
  } catch (e) {
    erro.value = e.message
  } finally {
    loading.value = false
  }
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
</style>