<template>
  <v-container>
    <!-- Cabeçalho -->
    <v-row class="mb-4" align="center">
      <v-col cols="12" sm="8">
        <h1 class="text-h5 font-weight-bold">
          <v-icon class="mr-2" color="green">mdi-google-spreadsheet</v-icon>
          Dashboards Google Sheets
        </h1>
        <p class="text-body-2 text-medium-emphasis mt-1">
          Visualize dados financeiros diretamente das suas planilhas em tempo real.
        </p>
      </v-col>
      <v-col cols="12" sm="4" class="text-sm-right">
        <v-btn
          color="primary"
          prepend-icon="mdi-plus"
          @click="dialogNovaPlanilha = true"
          :disabled="!statusConexao.conectado"
        >
          Adicionar planilha
        </v-btn>
      </v-col>
    </v-row>

    <!-- Status da conexão -->
    <v-alert
      v-if="!statusConexao.conectado && !loadingStatus"
      type="warning"
      variant="tonal"
      class="mb-4"
      prominent
    >
      <div class="d-flex align-center justify-space-between flex-wrap gap-2">
        <div>
          <strong>Google Sheets não configurado</strong>
          <p class="text-body-2 mb-0 mt-1">
            {{ statusConexao.erro || 'Configure as credenciais para conectar.' }}
          </p>
        </div>
        <v-btn variant="outlined" size="small" @click="dialogConfig = true">
          Ver instruções
        </v-btn>
      </div>
    </v-alert>

    <v-alert v-if="erro" type="error" class="mb-4" closable @click:close="erro = ''">
      {{ erro }}
    </v-alert>

    <!-- Loading status -->
    <div v-if="loadingStatus" class="d-flex justify-center my-8">
      <v-progress-circular indeterminate color="primary" />
    </div>

    <!-- Seletor de planilha -->
    <v-card v-if="statusConexao.conectado && !loadingStatus" elevation="2" class="mb-4">
      <v-card-text>
        <v-row align="center">
          <v-col cols="12" md="4">
            <v-text-field
              v-model="spreadsheetId"
              label="ID da Planilha Google Sheets"
              placeholder="Cole o ID da planilha aqui"
              variant="outlined"
              density="compact"
              hide-details
              prepend-inner-icon="mdi-link"
              :loading="loadingAbas"
            >
              <template #append>
                <v-tooltip text="O ID está na URL da planilha: docs.google.com/spreadsheets/d/[ID]/edit">
                  <template #activator="{ props }">
                    <v-icon v-bind="props" size="small">mdi-help-circle-outline</v-icon>
                  </template>
                </v-tooltip>
              </template>
            </v-text-field>
          </v-col>
          <v-col cols="12" md="2">
            <v-select
              v-model="abaSelecionada"
              :items="abas"
              item-title="title"
              item-value="title"
              label="Aba"
              variant="outlined"
              density="compact"
              hide-details
              :disabled="!abas.length"
              :loading="loadingAbas"
            />
          </v-col>
          <v-col cols="12" md="3">
            <v-select
              v-model="tipoDashboard"
              :items="[
                { title: 'Financeiro (automático)', value: 'financeiro' },
                { title: 'Cobranças / Vencimentos', value: 'cobrancas' },
              ]"
              item-title="title"
              item-value="value"
              label="Tipo de dashboard"
              variant="outlined"
              density="compact"
              hide-details
            />
          </v-col>
          <v-col cols="12" md="2">
            <v-btn
              color="primary"
              block
              :loading="loadingDashboard"
              :disabled="!spreadsheetId || !abaSelecionada"
              @click="carregarDashboard()"
            >
              <v-icon class="mr-1">mdi-chart-box</v-icon>
              Carregar
            </v-btn>
          </v-col>
          <v-col cols="12" md="1">
            <v-btn
              color="secondary"
              variant="outlined"
              block
              :loading="loadingDashboard"
              :disabled="!spreadsheetId || !abaSelecionada"
              @click="carregarDashboard(true)"
              title="Ignorar cache"
            >
              <v-icon>mdi-refresh</v-icon>
            </v-btn>
          </v-col>
        </v-row>
      </v-card-text>
    </v-card>

    <!-- Dashboard -->
    <Transition name="fade" mode="out-in">
      <div v-if="loadingDashboard" key="loading" class="d-flex flex-column align-center my-12">
        <v-progress-circular indeterminate color="primary" size="56" />
        <p class="text-body-2 text-medium-emphasis mt-4">Carregando dados da planilha...</p>
      </div>

      <!-- ── Dashboard Cobranças ────────────────────────────────────────────── -->
      <div v-else-if="dashboard && dashboard.tipo === 'cobrancas'" key="dashboard-cobrancas">
        <div class="d-flex align-center justify-space-between mb-4">
          <div>
            <span class="text-h6 font-weight-bold">{{ dashboard.titulo }}</span>
            <span class="text-caption text-medium-emphasis ml-3">
              <v-icon size="small" class="mr-1">mdi-clock-outline</v-icon>
              Atualizado em {{ dashboard.atualizado_em }}
            </span>
          </div>
          <v-chip size="small" color="green" variant="tonal">
            <v-icon size="small" class="mr-1">mdi-check-circle</v-icon>
            Conectado ao Google Sheets
          </v-chip>
        </div>

        <!-- KPIs -->
        <v-row class="mb-4">
          <v-col cols="12" sm="6" md="3">
            <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #2196F3;">
              <div class="d-flex align-center justify-space-between mb-2">
                <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Total Previsto</span>
                <v-icon color="blue" size="28">mdi-cash-multiple</v-icon>
              </div>
              <div class="text-h5 font-weight-bold" style="color: #2196F3;">
                {{ brl(dashboard.resumo.total_previsto) }}
              </div>
              <div class="text-caption text-medium-emphasis mt-1">
                {{ dashboard.resumo.total_condominios }} condomínios
              </div>
            </v-card>
          </v-col>

          <v-col cols="12" sm="6" md="3">
            <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #4CAF50;">
              <div class="d-flex align-center justify-space-between mb-2">
                <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Total Recebido</span>
                <v-icon color="green" size="28">mdi-check-circle</v-icon>
              </div>
              <div class="text-h5 font-weight-bold" style="color: #4CAF50;">
                {{ brl(dashboard.resumo.total_recebido) }}
              </div>
              <div class="text-caption text-medium-emphasis mt-1">
                {{ dashboard.resumo.pagos }} pagos
              </div>
            </v-card>
          </v-col>

          <v-col cols="12" sm="6" md="3">
            <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #F44336;">
              <div class="d-flex align-center justify-space-between mb-2">
                <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Pendente</span>
                <v-icon color="red" size="28">mdi-alert-circle</v-icon>
              </div>
              <div class="text-h5 font-weight-bold" style="color: #F44336;">
                {{ brl(dashboard.resumo.pendente) }}
              </div>
              <div class="text-caption text-medium-emphasis mt-1">
                {{ dashboard.resumo.pendentes }} pendentes
              </div>
            </v-card>
          </v-col>

          <v-col cols="12" sm="6" md="3">
            <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #9C27B0;">
              <div class="d-flex align-center justify-space-between mb-2">
                <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">% Recebido</span>
                <v-icon color="purple" size="28">mdi-percent</v-icon>
              </div>
              <div class="text-h5 font-weight-bold" style="color: #9C27B0;">
                {{ dashboard.resumo.percentual_recebido }}%
              </div>
              <div class="text-caption text-medium-emphasis mt-1">
                Antecipado: {{ brl(dashboard.resumo.total_antecipado) }}
              </div>
            </v-card>
          </v-col>
        </v-row>

        <!-- Gráfico por vencimento -->
        <v-row class="mb-4">
          <v-col cols="12" md="8">
            <v-card elevation="4">
              <v-card-title class="pa-4 pb-2 d-flex align-center">
                <v-icon class="mr-2" color="primary">mdi-chart-bar</v-icon>
                Previsto vs Recebido por Vencimento
              </v-card-title>
              <v-card-text>
                <div class="chart-container">
                  <canvas ref="chartCobrancas"></canvas>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="4">
            <v-card elevation="4" height="100%">
              <v-card-title class="pa-4 pb-2 d-flex align-center">
                <v-icon class="mr-2" color="primary">mdi-view-list</v-icon>
                Por Vencimento
              </v-card-title>
              <v-card-text class="pa-0">
                <v-list density="compact">
                  <v-list-item
                    v-for="pv in dashboard.por_vencimento"
                    :key="pv.vencimento"
                    class="px-4"
                  >
                    <template #title>
                      <span class="text-body-2 font-weight-medium">{{ pv.vencimento }}</span>
                    </template>
                    <template #subtitle>
                      <span class="text-caption">
                        Previsto: {{ brl(pv.previsto) }} · Recebido: {{ brl(pv.recebido) }}
                      </span>
                    </template>
                    <template #append>
                      <div class="d-flex gap-1">
                        <v-chip v-if="pv.pagos" size="x-small" color="green" variant="tonal">{{ pv.pagos }} ✓</v-chip>
                        <v-chip v-if="pv.pendentes" size="x-small" color="red" variant="tonal">{{ pv.pendentes }} ✗</v-chip>
                      </div>
                    </template>
                  </v-list-item>
                </v-list>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Tabela de condomínios -->
        <v-card elevation="4">
          <v-card-title class="pa-4 pb-2 d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-icon class="mr-2" color="primary">mdi-office-building</v-icon>
              Condomínios
            </div>
            <v-text-field
              v-model="buscaCobranca"
              density="compact"
              variant="outlined"
              placeholder="Buscar condomínio..."
              prepend-inner-icon="mdi-magnify"
              hide-details
              style="max-width: 260px;"
              clearable
            />
          </v-card-title>
          <v-card-text class="pa-0">
            <v-data-table
              :headers="headersCobrancas"
              :items="cobrancasFiltradas"
              :items-per-page="20"
              density="comfortable"
              class="elevation-0"
              no-data-text="Nenhum registro encontrado"
              :sort-by="[{ key: 'vencimento', order: 'asc' }]"
            >
              <template #item.valor_previsto="{ item }">
                {{ item.valor_previsto != null ? brl(item.valor_previsto) : '—' }}
              </template>
              <template #item.valor_pago="{ item }">
                <span :class="item.status === 'pendente' ? 'text-red' : 'text-green'">
                  {{ item.valor_pago > 0 ? brl(item.valor_pago) : '—' }}
                </span>
              </template>
              <template #item.diferenca="{ item }">
                <span v-if="item.diferenca != null" :class="item.diferenca >= 0 ? 'text-orange' : 'text-blue'">
                  {{ item.diferenca >= 0 ? '+' : '' }}{{ brl(item.diferenca) }}
                </span>
                <span v-else class="text-medium-emphasis">—</span>
              </template>
              <template #item.status="{ item }">
                <v-chip
                  :color="item.status === 'pago' ? 'green' : item.status === 'antecipado' ? 'blue' : 'red'"
                  size="small"
                  variant="tonal"
                >
                  {{ item.status === 'pago' ? 'Pago' : item.status === 'antecipado' ? 'Antecipado' : 'Pendente' }}
                </v-chip>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </div>

      <!-- ── Dashboard Financeiro (padrão) ─────────────────────────────────── -->
      <div v-else-if="dashboard" key="dashboard">
        <!-- Info de atualização -->
        <div class="d-flex align-center justify-space-between mb-4">
          <span class="text-caption text-medium-emphasis">
            <v-icon size="small" class="mr-1">mdi-clock-outline</v-icon>
            Atualizado em {{ dashboard.atualizado_em }}
          </span>
          <v-chip size="small" color="green" variant="tonal">
            <v-icon size="small" class="mr-1">mdi-check-circle</v-icon>
            Conectado ao Google Sheets
          </v-chip>
        </div>

        <!-- KPIs -->
        <v-row class="mb-4">
          <v-col cols="12" sm="6" md="3">
            <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #4CAF50;">
              <div class="d-flex align-center justify-space-between mb-2">
                <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Receitas</span>
                <v-icon color="green" size="28">mdi-trending-up</v-icon>
              </div>
              <div class="text-h5 font-weight-bold" style="color: #4CAF50;">
                {{ brl(dashboard.resumo.total_receitas) }}
              </div>
            </v-card>
          </v-col>

          <v-col cols="12" sm="6" md="3">
            <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #F44336;">
              <div class="d-flex align-center justify-space-between mb-2">
                <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Despesas</span>
                <v-icon color="red" size="28">mdi-trending-down</v-icon>
              </div>
              <div class="text-h5 font-weight-bold" style="color: #F44336;">
                {{ brl(dashboard.resumo.total_despesas) }}
              </div>
            </v-card>
          </v-col>

          <v-col cols="12" sm="6" md="3">
            <v-card elevation="4" class="kpi-card" :style="{ borderLeft: `4px solid ${dashboard.resumo.saldo >= 0 ? '#2196F3' : '#FF9800'}` }">
              <div class="d-flex align-center justify-space-between mb-2">
                <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Saldo</span>
                <v-icon :color="dashboard.resumo.saldo >= 0 ? 'blue' : 'orange'" size="28">
                  {{ dashboard.resumo.saldo >= 0 ? 'mdi-wallet-plus' : 'mdi-wallet-outline' }}
                </v-icon>
              </div>
              <div class="text-h5 font-weight-bold" :style="{ color: dashboard.resumo.saldo >= 0 ? '#2196F3' : '#FF9800' }">
                {{ brl(dashboard.resumo.saldo) }}
              </div>
            </v-card>
          </v-col>

          <v-col cols="12" sm="6" md="3">
            <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #9C27B0;">
              <div class="d-flex align-center justify-space-between mb-2">
                <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Transações</span>
                <v-icon color="purple" size="28">mdi-swap-horizontal</v-icon>
              </div>
              <div class="text-h5 font-weight-bold" style="color: #9C27B0;">
                {{ dashboard.resumo.total_transacoes }}
              </div>
            </v-card>
          </v-col>
        </v-row>

        <!-- Gráficos -->
        <v-row class="mb-4">
          <v-col cols="12" md="8">
            <v-card elevation="4">
              <v-card-title class="pa-4 pb-2 d-flex align-center">
                <v-icon class="mr-2" color="primary">mdi-chart-line</v-icon>
                Evolução Mensal
              </v-card-title>
              <v-card-text>
                <div v-if="dashboard.por_mes.length" class="chart-container">
                  <canvas ref="chartMensal"></canvas>
                </div>
                <div v-else class="text-center text-medium-emphasis pa-8">
                  <v-icon size="48" color="grey">mdi-chart-line-variant</v-icon>
                  <p class="mt-2">Sem dados mensais para exibir</p>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <v-col cols="12" md="4">
            <v-card elevation="4">
              <v-card-title class="pa-4 pb-2 d-flex align-center">
                <v-icon class="mr-2" color="primary">mdi-chart-pie</v-icon>
                Por Categoria
              </v-card-title>
              <v-card-text>
                <div v-if="Object.keys(dashboard.por_categoria).length" class="chart-container-pie">
                  <canvas ref="chartCategoria"></canvas>
                </div>
                <div v-else class="text-center text-medium-emphasis pa-8">
                  <v-icon size="48" color="grey">mdi-chart-donut</v-icon>
                  <p class="mt-2">Sem categorias para exibir</p>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Tabela de transações -->
        <v-card elevation="4">
          <v-card-title class="pa-4 pb-2 d-flex align-center justify-space-between">
            <div class="d-flex align-center">
              <v-icon class="mr-2" color="primary">mdi-format-list-bulleted</v-icon>
              Últimas Transações
            </div>
            <v-text-field
              v-model="buscaTransacao"
              density="compact"
              variant="outlined"
              placeholder="Buscar..."
              prepend-inner-icon="mdi-magnify"
              hide-details
              style="max-width: 250px;"
              clearable
            />
          </v-card-title>
          <v-card-text class="pa-0">
            <v-data-table
              :headers="headersTransacoes"
              :items="transacoesFiltradas"
              :items-per-page="10"
              density="comfortable"
              class="elevation-0"
              no-data-text="Nenhuma transação encontrada"
            >
              <template #item.valor="{ item }">
                <span :class="item.tipo === 'receita' ? 'text-green' : 'text-red'">
                  {{ item.tipo === 'receita' ? '+' : '-' }} {{ brl(Math.abs(item.valor)) }}
                </span>
              </template>
              <template #item.tipo="{ item }">
                <v-chip
                  :color="item.tipo === 'receita' ? 'green' : 'red'"
                  size="small"
                  variant="tonal"
                >
                  {{ item.tipo === 'receita' ? 'Receita' : 'Despesa' }}
                </v-chip>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </div>

      <!-- Estado vazio -->
      <v-card v-else-if="statusConexao.conectado" key="empty" elevation="2" class="pa-10 text-center">
        <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-table-large</v-icon>
        <p class="text-h6 text-medium-emphasis">Nenhum dashboard carregado</p>
        <p class="text-body-2 text-medium-emphasis mb-6">
          Cole o ID de uma planilha Google Sheets acima e clique em "Carregar".
        </p>
      </v-card>
    </Transition>

    <!-- Dialog de configuração -->
    <v-dialog v-model="dialogConfig" max-width="700">
      <v-card>
        <v-card-title class="pa-4 bg-primary">
          <v-icon class="mr-2">mdi-cog</v-icon>
          Configuração do Google Sheets
        </v-card-title>
        <v-card-text class="pa-4">
          <h3 class="text-subtitle-1 font-weight-bold mb-3">1. Criar conta de serviço no Google Cloud</h3>
          <ol class="text-body-2 mb-4">
            <li>Acesse o <a href="https://console.cloud.google.com" target="_blank">Google Cloud Console</a></li>
            <li>Crie um novo projeto ou selecione um existente</li>
            <li>Ative a <strong>Google Sheets API</strong></li>
            <li>Vá em "Credenciais" → "Criar credenciais" → "Conta de serviço"</li>
            <li>Baixe o arquivo JSON da chave</li>
          </ol>

          <h3 class="text-subtitle-1 font-weight-bold mb-3">2. Configurar variáveis de ambiente</h3>
          <v-code class="mb-4 pa-3 d-block" style="white-space: pre-wrap;">
# Opção 1: JSON direto (recomendado para Docker)
GOOGLE_SHEETS_CREDENTIALS='{"type":"service_account",...}'

# Opção 2: Caminho do arquivo
GOOGLE_SHEETS_CREDENTIALS_FILE=/path/to/credentials.json

# Cache (segundos)
SHEETS_CACHE_TTL=30
          </v-code>

          <h3 class="text-subtitle-1 font-weight-bold mb-3">3. Compartilhar planilhas</h3>
          <p class="text-body-2">
            Compartilhe cada planilha com o e-mail da conta de serviço
            (ex: <code>nome@projeto.iam.gserviceaccount.com</code>) com permissão de <strong>Leitor</strong>.
          </p>

          <v-alert type="info" variant="tonal" class="mt-4" density="compact">
            <strong>Dica:</strong> O ID da planilha está na URL:
            <code>docs.google.com/spreadsheets/d/<strong>[ID]</strong>/edit</code>
          </v-alert>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="dialogConfig = false">Fechar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog nova planilha -->
    <v-dialog v-model="dialogNovaPlanilha" max-width="500">
      <v-card>
        <v-card-title class="pa-4">
          <v-icon class="mr-2">mdi-plus</v-icon>
          Adicionar Planilha
        </v-card-title>
        <v-card-text class="pa-4">
          <v-text-field
            v-model="novaPlanilha.id"
            label="ID da Planilha"
            variant="outlined"
            class="mb-3"
            hint="Cole o ID da URL do Google Sheets"
            persistent-hint
          />
          <v-text-field
            v-model="novaPlanilha.nome"
            label="Nome de exibição"
            variant="outlined"
            class="mb-3"
          />
          <v-select
            v-model="novaPlanilha.tipo"
            :items="['financeiro', 'cobrancas', 'fluxo_caixa']"
            label="Tipo de dashboard"
            variant="outlined"
          />
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="dialogNovaPlanilha = false">Cancelar</v-btn>
          <v-btn color="primary" @click="salvarPlanilha">Salvar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import Chart from 'chart.js/auto'

// ── State ───────────────────────────────────────────────────────────────────

const statusConexao = ref({ conectado: false, erro: null })
const loadingStatus = ref(true)
const loadingAbas = ref(false)
const loadingDashboard = ref(false)
const erro = ref('')

const spreadsheetId = ref('')
const abas = ref([])
const abaSelecionada = ref('')
const tipoDashboard = ref('financeiro')
const dashboard = ref(null)

const buscaTransacao = ref('')
const buscaCobranca = ref('')
const dialogConfig = ref(false)
const dialogNovaPlanilha = ref(false)

const novaPlanilha = ref({ id: '', nome: '', tipo: 'financeiro' })

const chartMensal = ref(null)
const chartCategoria = ref(null)
const chartCobrancas = ref(null)
let chartMensalInstance = null
let chartCategoriaInstance = null
let chartCobrancasInstance = null

let pollingInterval = null

// ── Computed ────────────────────────────────────────────────────────────────

const transacoesFiltradas = computed(() => {
  if (!dashboard.value?.ultimas_transacoes) return []
  const q = buscaTransacao.value?.toLowerCase().trim()
  if (!q) return dashboard.value.ultimas_transacoes
  return dashboard.value.ultimas_transacoes.filter(t =>
    t.descricao.toLowerCase().includes(q) ||
    t.categoria.toLowerCase().includes(q) ||
    t.data.includes(q)
  )
})

const cobrancasFiltradas = computed(() => {
  if (!dashboard.value?.registros) return []
  const q = buscaCobranca.value?.toLowerCase().trim()
  if (!q) return dashboard.value.registros
  return dashboard.value.registros.filter(r =>
    r.condominio.toLowerCase().includes(q) ||
    r.vencimento.toLowerCase().includes(q) ||
    r.status.toLowerCase().includes(q)
  )
})

const headersTransacoes = [
  { title: 'Data', key: 'data', width: 110 },
  { title: 'Descrição', key: 'descricao' },
  { title: 'Categoria', key: 'categoria', width: 140 },
  { title: 'Valor', key: 'valor', width: 140 },
  { title: 'Tipo', key: 'tipo', width: 110 },
]

const headersCobrancas = [
  { title: 'Condomínio', key: 'condominio' },
  { title: 'Vencimento', key: 'vencimento', width: 130 },
  { title: 'Valor Previsto', key: 'valor_previsto', width: 140 },
  { title: 'Valor Pago', key: 'valor_pago', width: 130 },
  { title: 'Data Pagamento', key: 'data_pagamento', width: 140 },
  { title: 'Diferença', key: 'diferenca', width: 120 },
  { title: 'Status', key: 'status', width: 110 },
]

// ── Utils ───────────────────────────────────────────────────────────────────

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

// ── API Calls ───────────────────────────────────────────────────────────────

const verificarStatus = async () => {
  loadingStatus.value = true
  try {
    const res = await fetch('/api/sheets/status', { headers: authHeader() })
    if (res.ok) {
      statusConexao.value = await res.json()
    } else {
      statusConexao.value = { conectado: false, erro: 'Erro ao verificar conexão' }
    }
  } catch (e) {
    statusConexao.value = { conectado: false, erro: e.message }
  } finally {
    loadingStatus.value = false
  }
}

const sheetId = () => spreadsheetId.value.trim().replace(/\/+$/, '')

const carregarAbas = async () => {
  if (!spreadsheetId.value) {
    abas.value = []
    return
  }

  loadingAbas.value = true
  try {
    const res = await fetch(`/api/sheets/planilha/${sheetId()}/abas`, { headers: authHeader() })
    if (res.ok) {
      abas.value = await res.json()
      if (abas.value.length && !abaSelecionada.value) {
        abaSelecionada.value = abas.value[0].title
      }
    } else {
      const data = await res.json()
      erro.value = data.detail || 'Erro ao carregar abas'
      abas.value = []
    }
  } catch (e) {
    erro.value = e.message
    abas.value = []
  } finally {
    loadingAbas.value = false
  }
}

const carregarDashboard = async (force = false) => {
  if (!spreadsheetId.value || !abaSelecionada.value) return

  loadingDashboard.value = true
  erro.value = ''

  try {
    let url
    if (tipoDashboard.value === 'cobrancas') {
      url = `/api/sheets/dashboard/cobrancas/${sheetId()}?aba=${encodeURIComponent(abaSelecionada.value)}${force ? '&force=true' : ''}`
    } else {
      url = `/api/sheets/dashboard/rapido/${sheetId()}?aba=${encodeURIComponent(abaSelecionada.value)}${force ? '&force=true' : ''}`
    }

    const res = await fetch(url, { headers: authHeader() })

    if (res.ok) {
      dashboard.value = await res.json()
      // Os gráficos são renderizados via watch nos refs dos canvas
      // (o <Transition mode="out-in"> insere o canvas só após a animação de saída)
    } else {
      const data = await res.json()
      erro.value = data.detail || 'Erro ao carregar dashboard'
    }
  } catch (e) {
    erro.value = e.message
  } finally {
    loadingDashboard.value = false
  }
}

const salvarPlanilha = () => {
  dialogNovaPlanilha.value = false
  novaPlanilha.value = { id: '', nome: '', tipo: 'financeiro' }
}

// ── Gráficos ────────────────────────────────────────────────────────────────

const destroyCharts = () => {
  if (chartMensalInstance) { chartMensalInstance.destroy(); chartMensalInstance = null }
  if (chartCategoriaInstance) { chartCategoriaInstance.destroy(); chartCategoriaInstance = null }
  if (chartCobrancasInstance) { chartCobrancasInstance.destroy(); chartCobrancasInstance = null }
}

const renderizarGraficos = () => {
  if (!dashboard.value) return
  destroyCharts()

  if (chartMensal.value && dashboard.value.por_mes?.length) {
    const ctx = chartMensal.value.getContext('2d')
    const labels = dashboard.value.por_mes.map(m => {
      const [ano, mes] = m.mes.split('-')
      return `${mes}/${ano.slice(2)}`
    })

    chartMensalInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          {
            label: 'Receitas',
            data: dashboard.value.por_mes.map(m => m.receitas),
            borderColor: '#4CAF50',
            backgroundColor: 'rgba(76, 175, 80, 0.1)',
            fill: true,
            tension: 0.3,
          },
          {
            label: 'Despesas',
            data: dashboard.value.por_mes.map(m => m.despesas),
            borderColor: '#F44336',
            backgroundColor: 'rgba(244, 67, 54, 0.1)',
            fill: true,
            tension: 0.3,
          },
          {
            label: 'Saldo',
            data: dashboard.value.por_mes.map(m => m.saldo),
            borderColor: '#2196F3',
            backgroundColor: 'transparent',
            borderDash: [5, 5],
            tension: 0.3,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'top' } },
        scales: {
          y: {
            beginAtZero: true,
            ticks: { callback: (v) => `R$ ${(v / 1000).toFixed(0)}k` },
          },
        },
      },
    })
  }

  if (chartCategoria.value && Object.keys(dashboard.value.por_categoria || {}).length) {
    const ctx = chartCategoria.value.getContext('2d')
    const categorias = Object.entries(dashboard.value.por_categoria)
    const labels = categorias.map(([k]) => k)
    const totais = categorias.map(([, v]) => v.despesas + v.receitas)
    const cores = [
      '#4CAF50', '#2196F3', '#FF9800', '#9C27B0', '#F44336',
      '#00BCD4', '#795548', '#607D8B', '#E91E63', '#3F51B5',
    ]

    chartCategoriaInstance = new Chart(ctx, {
      type: 'doughnut',
      data: {
        labels,
        datasets: [{ data: totais, backgroundColor: cores.slice(0, labels.length) }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'right' } },
      },
    })
  }
}

const renderizarGraficoCobrancas = () => {
  if (!dashboard.value?.por_vencimento?.length) return
  destroyCharts()

  if (!chartCobrancas.value) return
  const ctx = chartCobrancas.value.getContext('2d')
  const pv = dashboard.value.por_vencimento

  chartCobrancasInstance = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: pv.map(p => p.vencimento),
      datasets: [
        {
          label: 'Previsto',
          data: pv.map(p => p.previsto),
          backgroundColor: 'rgba(33, 150, 243, 0.6)',
          borderColor: '#2196F3',
          borderWidth: 1,
        },
        {
          label: 'Recebido',
          data: pv.map(p => p.recebido),
          backgroundColor: 'rgba(76, 175, 80, 0.7)',
          borderColor: '#4CAF50',
          borderWidth: 1,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: {
        y: {
          beginAtZero: true,
          ticks: { callback: (v) => `R$ ${(v / 1000).toFixed(1)}k` },
        },
      },
    },
  })
}

// ── Watchers ────────────────────────────────────────────────────────────────

watch(spreadsheetId, (newVal) => {
  if (newVal && newVal.length > 20) {
    carregarAbas()
  } else {
    abas.value = []
    abaSelecionada.value = ''
  }
})

// Renderiza gráfico de cobranças quando o canvas entra no DOM (após transição)
watch(chartCobrancas, (canvas) => {
  if (canvas && dashboard.value?.tipo === 'cobrancas') {
    renderizarGraficoCobrancas()
  }
})

// Renderiza gráficos financeiros quando os canvas entram no DOM
watch([chartMensal, chartCategoria], ([mensal]) => {
  if (mensal && dashboard.value && dashboard.value.tipo !== 'cobrancas') {
    renderizarGraficos()
  }
})

// ── Lifecycle ───────────────────────────────────────────────────────────────

onMounted(async () => {
  await verificarStatus()
})

onUnmounted(() => {
  destroyCharts()
})
</script>

<style scoped>
.kpi-card {
  padding: 20px !important;
  height: 130px;
  display: flex;
  flex-direction: column;
}

.chart-container {
  height: 300px;
  position: relative;
}

.chart-container-pie {
  height: 280px;
  position: relative;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
