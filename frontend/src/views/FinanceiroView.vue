<template>
  <div>
    <!-- Cabeçalho -->
    <div class="d-flex align-center gap-4 mb-6">
      <div class="page-icon">
        <v-icon size="20" color="white">mdi-currency-usd</v-icon>
      </div>
      <div>
        <h1 class="page-title">Financeiro</h1>
        <p class="page-subtitle">Despesas por condomínio via Superlógica</p>
      </div>
    </div>

    <!-- Filtros -->
    <v-card class="section-card mb-6" elevation="3">
      <div class="section-header">
        <div class="section-badge">
          <v-icon size="16" color="white">mdi-filter-outline</v-icon>
        </div>
        <div>
          <p class="section-title">Filtros</p>
          <p class="section-subtitle">Selecione o condomínio e período</p>
        </div>
      </div>

      <div class="pa-6">
        <v-row>
          <v-col cols="12" md="4">
            <v-autocomplete
              v-model="condominioSelecionado"
              :items="condominios"
              item-title="nome"
              item-value="id"
              label="Loja"
              variant="outlined"
              density="comfortable"
              clearable
              hide-details
              multiple
              chips
              closable-chips
              :disabled="loadingCondominios || loading"
              no-data-text="Nenhum condomínio encontrado"
              placeholder="Selecione um ou mais condomínios..."
            />
          </v-col>

          <v-col cols="12" sm="6" md="2">
            <v-text-field
              v-model="dtInicio"
              label="Data início"
              variant="outlined"
              density="comfortable"
              placeholder="DD/MM/AAAA"
              hide-details
              :disabled="loading"
            />
          </v-col>

          <v-col cols="12" sm="6" md="2">
            <v-text-field
              v-model="dtFim"
              label="Data fim"
              variant="outlined"
              density="comfortable"
              placeholder="DD/MM/AAAA"
              hide-details
              :disabled="loading"
            />
          </v-col>

          <v-col cols="12" sm="6" md="2">
            <v-select
              v-model="comStatus"
              :items="[
                { title: 'Todas', value: 'todas' },
                { title: 'Pendentes', value: 'pendentes' },
                { title: 'Liquidadas', value: 'liquidadas' },
              ]"
              item-title="title"
              item-value="value"
              label="Status"
              variant="outlined"
              density="comfortable"
              hide-details
              :disabled="loading"
            />
          </v-col>

          <v-col cols="12" sm="6" md="2" class="d-flex align-start">
            <v-btn
              color="primary"
              block
              size="large"
              prepend-icon="mdi-magnify"
              :loading="loading"
              :disabled="!condominioSelecionado.length || !dtInicio || !dtFim || loading"
              @click="buscar"
            >Buscar despesas</v-btn>
          </v-col>
        </v-row>
      </div>
    </v-card>

    <!-- Erro -->
    <v-alert v-if="erro" type="error" class="mb-4" closable @click:close="erro = ''">
      {{ erro }}
    </v-alert>

    <!-- Loading -->
    <div v-if="loading" class="d-flex flex-column align-center my-12">
      <v-progress-circular indeterminate color="primary" size="56" />
      <p class="text-body-2 text-medium-emphasis mt-4">Buscando despesas...</p>
    </div>

    <!-- Resultados -->
    <div v-if="dados && !loading">

      <!-- KPIs -->
      <v-row class="mb-4">
        <v-col cols="12" sm="6" md="3">
          <v-card elevation="4" class="kpi-card kpi-clickable" style="border-left: 4px solid #2196F3;" @click="abrirDialog('todas')">
            <div class="d-flex align-center justify-space-between mb-2">
              <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Total Geral</span>
              <v-icon color="blue" size="28">mdi-cash-multiple</v-icon>
            </div>
            <div class="text-h5 font-weight-bold" style="color:#2196F3">{{ brl(dados.resumo.total_geral) }}</div>
            <div class="text-caption text-medium-emphasis mt-1">{{ dados.resumo.quantidade }} despesas</div>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card elevation="4" class="kpi-card kpi-clickable" style="border-left: 4px solid #4CAF50;" @click="abrirDialog('liquidada')">
            <div class="d-flex align-center justify-space-between mb-2">
              <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Liquidado</span>
              <v-icon color="green" size="28">mdi-check-circle-outline</v-icon>
            </div>
            <div class="text-h5 font-weight-bold" style="color:#4CAF50">{{ brl(dados.resumo.total_liquidado) }}</div>
            <div class="text-caption text-medium-emphasis mt-1">
              {{ pct(dados.resumo.total_liquidado, dados.resumo.total_geral) }}% do total
            </div>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card elevation="4" class="kpi-card kpi-clickable" style="border-left: 4px solid #F44336;" @click="abrirDialog('pendente')">
            <div class="d-flex align-center justify-space-between mb-2">
              <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Pendente</span>
              <v-icon color="red" size="28">mdi-alert-circle-outline</v-icon>
            </div>
            <div class="text-h5 font-weight-bold" style="color:#F44336">{{ brl(dados.resumo.total_pendente) }}</div>
            <div class="text-caption text-medium-emphasis mt-1">
              {{ pct(dados.resumo.total_pendente, dados.resumo.total_geral) }}% do total
            </div>
          </v-card>
        </v-col>

        <v-col cols="12" sm="6" md="3">
          <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #FF9800;">
            <div class="d-flex align-center justify-space-between mb-2">
              <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Atualizado em</span>
              <v-icon color="orange" size="28">mdi-clock-outline</v-icon>
            </div>
            <div class="text-h6 font-weight-bold" style="color:#FF9800">{{ dados.atualizado_em }}</div>
            <div class="text-caption text-medium-emphasis mt-1">última consulta</div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Dialog KPI -->
      <v-dialog v-model="dialogKpi" max-width="900">
        <v-card>
          <v-card-title class="pa-4 d-flex align-center justify-space-between">
            <div class="d-flex align-center gap-2">
              <v-icon :color="dialogConfig.cor">{{ dialogConfig.icone }}</v-icon>
              <span>{{ dialogConfig.titulo }}</span>
              <v-chip size="small" :color="dialogConfig.cor" variant="tonal">{{ dialogItens.length }} despesas</v-chip>
            </div>
            <v-btn icon variant="text" @click="dialogKpi = false"><v-icon>mdi-close</v-icon></v-btn>
          </v-card-title>
          <v-divider />
          <v-card-text class="pa-4">
            <v-data-table
              :headers="dialogFiltro === 'pendente' ? headersPendentes : headersDialog"
              :items="dialogItens"
              :items-per-page="15"
              density="compact"
              class="text-body-2"
            >
              <template #item.valor="{ item }">{{ brl(item.valor) }}</template>
              <template #item.valor_pago="{ item }">{{ item.valor_pago > 0 ? brl(item.valor_pago) : '-' }}</template>
              <template #item.dias_atraso="{ item }">
                <v-chip
                  v-if="item.dias_atraso > 0"
                  :color="item.dias_atraso > 30 ? 'red' : item.dias_atraso > 10 ? 'orange' : 'yellow-darken-3'"
                  size="x-small"
                  variant="tonal"
                >{{ item.dias_atraso }} dias</v-chip>
                <span v-else class="text-medium-emphasis">-</span>
              </template>
              <template #item.status="{ item }">
                <v-chip :color="item.status === 'liquidada' ? 'green' : 'red'" size="x-small" variant="tonal">
                  {{ item.status }}
                </v-chip>
              </template>
            </v-data-table>

            <div class="d-flex justify-end mt-3">
              <strong>Total: {{ brl(dialogItens.reduce((s, d) => s + d.valor, 0)) }}</strong>
            </div>
          </v-card-text>
        </v-card>
      </v-dialog>

      <v-row class="mb-6">
        <!-- Por Categoria -->
        <v-col cols="12" md="6">
          <v-card elevation="3" class="h-100" style="border-radius:12px; overflow:hidden;">
            <div class="section-header">
              <div class="section-badge" style="background: linear-gradient(135deg,#5C6BC0,#3949AB);">
                <v-icon size="16" color="white">mdi-tag-multiple-outline</v-icon>
              </div>
              <p class="section-title">Por Categoria</p>
            </div>
            <div class="pa-4">
              <div
                v-for="(cat, i) in dados.resumo.por_categoria"
                :key="cat.categoria"
                class="ranking-item"
                :class="{ 'mt-3': i > 0 }"
              >
                <div class="d-flex justify-space-between align-center mb-1">
                  <div class="d-flex align-center gap-2">
                    <span class="ranking-num">{{ i + 1 }}</span>
                    <span class="text-body-2 ml-1">{{ cat.categoria }}</span>
                    <v-chip size="x-small" color="indigo" variant="tonal" class="ml-2">{{ cat.quantidade }}x</v-chip>
                  </div>
                  <span class="text-body-2 font-weight-bold">{{ brl(cat.total) }}</span>
                </div>
                <v-progress-linear
                  :model-value="pct(cat.total, dados.resumo.total_geral)"
                  color="indigo"
                  height="6"
                  rounded
                  bg-color="rgba(92,107,192,0.15)"
                />
              </div>
            </div>
          </v-card>
        </v-col>

        <!-- Top Fornecedores -->
        <v-col cols="12" md="6">
          <v-card elevation="3" class="h-100" style="border-radius:12px; overflow:hidden;">
            <div class="section-header">
              <div class="section-badge" style="background: linear-gradient(135deg,#009688,#00796b);">
                <v-icon size="16" color="white">mdi-store-outline</v-icon>
              </div>
              <p class="section-title">Top 10 Fornecedores</p>
            </div>
            <div class="pa-4">
              <div
                v-for="(forn, i) in dados.resumo.por_fornecedor"
                :key="forn.fornecedor"
                class="ranking-item"
                :class="{ 'mt-3': i > 0 }"
              >
                <div class="d-flex justify-space-between align-center mb-1">
                  <div class="d-flex align-center gap-2">
                    <span class="ranking-num">{{ i + 1 }}</span>
                    <span class="text-body-2" style="max-width:260px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">
                      {{ forn.fornecedor || 'Sem fornecedor' }}
                    </span>
                  </div>
                  <span class="text-body-2 font-weight-bold">{{ brl(forn.total) }}</span>
                </div>
                <v-progress-linear
                  :model-value="pct(forn.total, dados.resumo.total_geral)"
                  color="teal"
                  height="6"
                  rounded
                  bg-color="rgba(0,150,136,0.15)"
                />
              </div>
            </div>
          </v-card>
        </v-col>
      </v-row>

      <!-- Tabela de despesas -->
      <v-card elevation="3" class="pa-4">
        <div class="d-flex align-center justify-space-between mb-3 flex-wrap gap-2">
          <p class="text-subtitle-1 font-weight-bold">
            <v-icon size="18" class="mr-1">mdi-table</v-icon>
            Despesas ({{ despesasFiltradas.length }})
          </p>
          <v-text-field
            v-model="busca"
            density="compact"
            variant="outlined"
            hide-details
            placeholder="Buscar..."
            prepend-inner-icon="mdi-magnify"
            style="max-width: 280px"
          />
        </div>

        <v-data-table
          :headers="headers"
          :items="despesasFiltradas"
          :items-per-page="20"
          density="compact"
          class="text-body-2"
        >
          <template #item.valor="{ item }">
            {{ brl(item.valor) }}
          </template>
          <template #item.valor_pago="{ item }">
            {{ item.valor_pago > 0 ? brl(item.valor_pago) : '-' }}
          </template>
          <template #item.status="{ item }">
            <v-chip
              :color="item.status === 'liquidada' ? 'green' : 'red'"
              size="x-small"
              variant="tonal"
            >{{ item.status }}</v-chip>
          </template>
        </v-data-table>
      </v-card>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const condominios = ref([])
const condominioSelecionado = ref([])
const loadingCondominios = ref(false)
const loading = ref(false)
const erro = ref('')
const dados = ref(null)
const busca = ref('')

// Filtros — padrão: mês atual
const hoje = new Date()
const primeiroDia = `01/${String(hoje.getMonth() + 1).padStart(2, '0')}/${hoje.getFullYear()}`
const ultimoDia = `${String(new Date(hoje.getFullYear(), hoje.getMonth() + 1, 0).getDate()).padStart(2, '0')}/${String(hoje.getMonth() + 1).padStart(2, '0')}/${hoje.getFullYear()}`

const dtInicio = ref(primeiroDia)
const dtFim = ref(ultimoDia)
const comStatus = ref('todas')

const headers = [
  { title: 'Descrição', key: 'descricao', sortable: true },
  { title: 'Fornecedor', key: 'fornecedor', sortable: true },
  { title: 'Categoria', key: 'categoria', sortable: true },
  { title: 'Vencimento', key: 'vencimento', sortable: true },
  { title: 'Liquidação', key: 'liquidacao', sortable: true },
  { title: 'Valor', key: 'valor', sortable: true },
  { title: 'Valor Pago', key: 'valor_pago', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
]

const headersDialog = [
  { title: 'Fornecedor', key: 'fornecedor', sortable: true },
  { title: 'Categoria', key: 'categoria', sortable: true },
  { title: 'Vencimento', key: 'vencimento', sortable: true },
  { title: 'Liquidação', key: 'liquidacao', sortable: true },
  { title: 'Valor', key: 'valor', sortable: true },
  { title: 'Status', key: 'status', sortable: true },
]

const headersPendentes = [
  { title: 'Fornecedor', key: 'fornecedor', sortable: true },
  { title: 'Categoria', key: 'categoria', sortable: true },
  { title: 'Vencimento', key: 'vencimento', sortable: true },
  { title: 'Valor', key: 'valor', sortable: true },
  { title: 'Dias em atraso', key: 'dias_atraso', sortable: true },
]

// Dialog KPI
const dialogKpi = ref(false)
const dialogFiltro = ref('todas')
const dialogConfig = ref({ titulo: '', cor: 'primary', icone: 'mdi-cash-multiple' })

const configPorFiltro = {
  todas:    { titulo: 'Todas as Despesas',   cor: 'blue',  icone: 'mdi-cash-multiple'       },
  liquidada:{ titulo: 'Despesas Liquidadas', cor: 'green', icone: 'mdi-check-circle-outline' },
  pendente: { titulo: 'Despesas Pendentes',  cor: 'red',   icone: 'mdi-alert-circle-outline' },
}

const diasAtraso = (vencimento) => {
  if (!vencimento) return 0
  const [d, m, a] = vencimento.split('/')
  const venc = new Date(+a, +m - 1, +d)
  const hoje = new Date()
  hoje.setHours(0, 0, 0, 0)
  const diff = Math.floor((hoje - venc) / 86400000)
  return diff > 0 ? diff : 0
}

const dialogItens = computed(() => {
  if (!dados.value?.despesas) return []
  let lista = dialogFiltro.value === 'todas'
    ? dados.value.despesas
    : dados.value.despesas.filter(d => d.status === dialogFiltro.value)
  if (dialogFiltro.value === 'pendente') {
    lista = lista.map(d => ({ ...d, dias_atraso: diasAtraso(d.vencimento) }))
    lista = [...lista].sort((a, b) => b.dias_atraso - a.dias_atraso)
  }
  return lista
})

const abrirDialog = (filtro) => {
  dialogFiltro.value = filtro
  dialogConfig.value = configPorFiltro[filtro]
  dialogKpi.value = true
}

const authHeader = () => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

const brl = (v) => new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0)
const pct = (parte, total) => total > 0 ? Math.round((parte / total) * 100) : 0

const despesasFiltradas = computed(() => {
  if (!dados.value?.despesas) return []
  const q = busca.value.toLowerCase().trim()
  if (!q) return dados.value.despesas
  return dados.value.despesas.filter(d =>
    d.descricao.toLowerCase().includes(q) ||
    d.fornecedor.toLowerCase().includes(q) ||
    d.categoria.toLowerCase().includes(q)
  )
})

const fetchCondominios = async () => {
  loadingCondominios.value = true
  try {
    const res = await fetch('/api/admin/condominios', { headers: authHeader() })
    if (res.ok) {
      const lista = await res.json()
      condominios.value = lista
    }
  } catch { /* silencioso */ }
  finally { loadingCondominios.value = false }
}

const buscar = async () => {
  if (!condominioSelecionado.value.length || !dtInicio.value || !dtFim.value) return
  loading.value = true
  erro.value = ''
  dados.value = null

  try {
    const params = new URLSearchParams({
      dt_inicio: dtInicio.value,
      dt_fim: dtFim.value,
      com_status: comStatus.value,
    })

    const respostas = await Promise.all(
      condominioSelecionado.value.map(id =>
        fetch(`/api/financeiro/despesas/${id}?${params}`, { headers: authHeader() })
          .then(r => r.json())
      )
    )

    if (condominioSelecionado.value.length === 1) {
      dados.value = respostas[0]
    } else {
      // Agrega múltiplos condomínios
      const todasDespesas = respostas.flatMap(r => r.despesas || [])
      const somaResumo = (campo) => respostas.reduce((acc, r) => acc + (r.resumo?.[campo] || 0), 0)

      // Agrega por_categoria
      const catMap = {}
      respostas.forEach(r => (r.resumo?.por_categoria || []).forEach(c => {
        if (!catMap[c.categoria]) catMap[c.categoria] = { categoria: c.categoria, total: 0, quantidade: 0 }
        catMap[c.categoria].total += c.total
        catMap[c.categoria].quantidade += c.quantidade
      }))

      // Agrega por_fornecedor
      const fornMap = {}
      respostas.forEach(r => (r.resumo?.por_fornecedor || []).forEach(f => {
        if (!fornMap[f.fornecedor]) fornMap[f.fornecedor] = { fornecedor: f.fornecedor, total: 0 }
        fornMap[f.fornecedor].total += f.total
      }))

      dados.value = {
        despesas: todasDespesas,
        atualizado_em: respostas[0]?.atualizado_em || '',
        resumo: {
          total_geral:    somaResumo('total_geral'),
          total_pago:     somaResumo('total_pago'),
          total_pendente: somaResumo('total_pendente'),
          total_liquidado:somaResumo('total_liquidado'),
          quantidade:     somaResumo('quantidade'),
          por_categoria:  Object.values(catMap).sort((a, b) => b.total - a.total),
          por_fornecedor: Object.values(fornMap).sort((a, b) => b.total - a.total),
          por_mes:        [],
        },
      }
    }
  } catch (e) {
    erro.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchCondominios)
</script>

<style scoped>
.page-icon {
  width: 40px;
  height: 40px;
  background: linear-gradient(135deg, #009688, #00796b);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
}
.page-title { font-size: 1.4rem; font-weight: 700; margin: 0; }
.page-subtitle { font-size: 0.85rem; color: #6b7280; margin: 0; }
.section-card { border-radius: 12px; overflow: hidden; }
.section-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 24px;
  background: linear-gradient(135deg, rgba(0,150,136,0.08), rgba(0,121,107,0.04));
  border-bottom: 1px solid rgba(0,0,0,0.06);
}
.section-badge {
  width: 32px; height: 32px;
  background: linear-gradient(135deg, #009688, #00796b);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.section-title { font-size: 0.95rem; font-weight: 600; margin: 0; }
.section-subtitle { font-size: 0.8rem; color: #6b7280; margin: 0; }
.kpi-card { padding: 20px; border-radius: 12px; }
.kpi-clickable { cursor: pointer; transition: transform 0.15s, box-shadow 0.15s; }
.kpi-clickable:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0,0,0,0.15) !important; }
.ranking-num {
  width: 22px; height: 22px; border-radius: 50%;
  background: rgba(0,0,0,0.06);
  font-size: 11px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
</style>
