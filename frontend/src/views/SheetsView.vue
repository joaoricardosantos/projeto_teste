<template>
  <v-container>
    <!-- Cabeçalho -->
    <div class="d-flex align-center justify-space-between flex-wrap gap-3 mb-6">
      <div class="d-flex align-center gap-4">
        <div class="page-icon">
          <v-icon size="20" color="white">mdi-google-spreadsheet</v-icon>
        </div>
        <div>
          <h1 class="page-title">Google Sheets</h1>
          <p class="page-subtitle">Visualize dados das planilhas configuradas em tempo real</p>
        </div>
      </div>
      <div class="d-flex gap-2">
        <v-btn variant="outlined" prepend-icon="mdi-cog" @click="dialogSetores = true">
          Gerenciar Setores
        </v-btn>
        <v-btn
          v-if="setorAtivo"
          color="primary"
          variant="tonal"
          :loading="loadingDashboard"
          icon
          @click="carregarDashboard(true)"
        >
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
      </div>
    </div>

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
          <p class="text-body-2 mb-0 mt-1">{{ statusConexao.erro || 'Configure as credenciais.' }}</p>
        </div>
        <v-btn variant="outlined" size="small" @click="dialogConfig = true">Ver instruções</v-btn>
      </div>
    </v-alert>

    <v-alert v-if="erro" type="error" class="mb-4" closable @click:close="erro = ''">
      {{ erro }}
    </v-alert>

    <div v-if="loadingStatus" class="d-flex justify-center my-8">
      <v-progress-circular indeterminate color="primary" />
    </div>

    <!-- Menu de Setores -->
    <div v-if="statusConexao.conectado && !loadingStatus">
      <div v-if="setores.length === 0" class="text-center my-8">
        <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-google-spreadsheet</v-icon>
        <p class="text-h6 text-medium-emphasis">Nenhum setor configurado</p>
        <p class="text-body-2 text-medium-emphasis mb-6">
          Clique em "Gerenciar Setores" para adicionar uma planilha.
        </p>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="dialogSetores = true">
          Adicionar Setor
        </v-btn>
      </div>

      <div v-else>
        <!-- Seletor de Grupo -->
        <div v-if="grupos.length > 1" class="mb-3">
          <v-menu>
            <template #activator="{ props }">
              <v-btn v-bind="props" variant="outlined" append-icon="mdi-chevron-down">
                <v-icon start>mdi-folder-outline</v-icon>
                {{ grupoAtivo || 'Sem grupo' }}
              </v-btn>
            </template>
            <v-list>
              <v-list-item
                v-for="g in grupos"
                :key="g"
                :title="g || 'Sem grupo'"
                :active="grupoAtivo === g"
                active-color="primary"
                @click="selecionarGrupo(g)"
              />
            </v-list>
          </v-menu>
        </div>

        <!-- Tabs de Setores -->
        <v-tabs v-model="setorAtivoId" color="primary" class="mb-4" show-arrows>
          <v-tab
            v-for="setor in setoresFiltrados"
            :key="setor.id"
            :value="setor.id"
          >
            <v-icon size="small" class="mr-2">
              {{ { cobrancas: 'mdi-cash-clock', advocacia: 'mdi-gavel', despesas: 'mdi-store-minus' }[setor.tipo_dashboard] || 'mdi-chart-line' }}
            </v-icon>
            {{ setor.nome }}
          </v-tab>
        </v-tabs>

        <!-- Dashboard -->
        <Transition name="fade" mode="out-in">
          <div v-if="loadingDashboard" key="loading" class="d-flex flex-column align-center my-12">
            <v-progress-circular indeterminate color="primary" size="56" />
            <p class="text-body-2 text-medium-emphasis mt-4">Carregando dados da planilha...</p>
          </div>

          <!-- Dashboard Cobranças -->
          <div v-else-if="dashboard && dashboard.tipo === 'cobrancas'" key="cobrancas">
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
                Conectado
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
                  <div class="text-h5 font-weight-bold" style="color: #2196F3;">{{ brl(dashboard.resumo.total_previsto) }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">{{ dashboard.resumo.total_condominios }} condomínios</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #4CAF50;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Total Recebido</span>
                    <v-icon color="green" size="28">mdi-check-circle</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #4CAF50;">{{ brl(dashboard.resumo.total_recebido) }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">{{ dashboard.resumo.pagos }} pagos</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #F44336;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Pendente</span>
                    <v-icon color="red" size="28">mdi-alert-circle</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #F44336;">{{ brl(dashboard.resumo.pendente) }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">{{ dashboard.resumo.pendentes }} pendentes</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #9C27B0;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">% Recebido</span>
                    <v-icon color="purple" size="28">mdi-percent</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #9C27B0;">{{ dashboard.resumo.percentual_recebido }}%</div>
                  <div class="text-caption text-medium-emphasis mt-1">Antecipado: {{ brl(dashboard.resumo.total_antecipado) }}</div>
                </v-card>
              </v-col>
            </v-row>

            <!-- Gráfico + Lista -->
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
                      <v-list-item v-for="pv in dashboard.por_vencimento" :key="pv.vencimento" class="px-4">
                        <template #title>
                          <span class="text-body-2 font-weight-medium">{{ pv.vencimento }}</span>
                        </template>
                        <template #subtitle>
                          <span class="text-caption">Previsto: {{ brl(pv.previsto) }} · Recebido: {{ brl(pv.recebido) }}</span>
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

            <!-- Tabela -->
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

          <!-- Dashboard Advocacia -->
          <div v-else-if="dashboard && dashboard.tipo === 'advocacia'" key="advocacia">
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
                Conectado
              </v-chip>
            </div>

            <!-- KPIs -->
            <v-row class="mb-4">
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #2196F3;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Taxa de Cobrança</span>
                    <v-icon color="blue" size="28">mdi-gavel</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #2196F3;">{{ brl(dashboard.resumo.total_taxa_cobranca) }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">{{ dashboard.resumo.total_unidades }} unidades</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #4CAF50;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Total Creditado</span>
                    <v-icon color="green" size="28">mdi-check-circle</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #4CAF50;">{{ brl(dashboard.resumo.total_creditado) }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">{{ dashboard.resumo.liquidados }} liquidados</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #FF9800;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Honorários</span>
                    <v-icon color="orange" size="28">mdi-currency-usd</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #FF9800;">{{ brl(dashboard.resumo.total_honorarios) }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">{{ dashboard.resumo.pendentes }} pendentes</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #9C27B0;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">% Liquidado</span>
                    <v-icon color="purple" size="28">mdi-percent</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #9C27B0;">{{ dashboard.resumo.percentual_liquidado }}%</div>
                  <div class="text-caption text-medium-emphasis mt-1">{{ dashboard.resumo.liquidados }} de {{ dashboard.resumo.total_unidades }}</div>
                </v-card>
              </v-col>
            </v-row>

            <!-- Gráfico + Lista por Advogado -->
            <v-row class="mb-4">
              <v-col cols="12" md="8">
                <v-card elevation="4">
                  <v-card-title class="pa-4 pb-2 d-flex align-center">
                    <v-icon class="mr-2" color="primary">mdi-chart-bar</v-icon>
                    Taxa de Cobrança por Advogado
                  </v-card-title>
                  <v-card-text>
                    <div class="chart-container">
                      <canvas ref="chartAdvocacia"></canvas>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card elevation="4" height="100%">
                  <v-card-title class="pa-4 pb-2 d-flex align-center">
                    <v-icon class="mr-2" color="primary">mdi-account-group</v-icon>
                    Por Advogado
                  </v-card-title>
                  <v-card-text class="pa-0">
                    <v-list density="compact">
                      <v-list-item v-for="pa in dashboard.por_advogado" :key="pa.advogado" class="px-4">
                        <template #title>
                          <span class="text-body-2 font-weight-medium">{{ pa.advogado }}</span>
                        </template>
                        <template #subtitle>
                          <span class="text-caption">Taxa: {{ brl(pa.taxa_total) }} · Creditado: {{ brl(pa.creditado_total) }}</span>
                        </template>
                        <template #append>
                          <div class="d-flex gap-1">
                            <v-chip v-if="pa.liquidados" size="x-small" color="green" variant="tonal">{{ pa.liquidados }} ✓</v-chip>
                            <v-chip v-if="pa.pendentes" size="x-small" color="orange" variant="tonal">{{ pa.pendentes }} ⏳</v-chip>
                          </div>
                        </template>
                      </v-list-item>
                    </v-list>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- Tabela -->
            <v-card elevation="4">
              <v-card-title class="pa-4 pb-2 d-flex align-center justify-space-between">
                <div class="d-flex align-center">
                  <v-icon class="mr-2" color="primary">mdi-office-building</v-icon>
                  Unidades
                </div>
                <v-text-field
                  v-model="buscaAdvocacia"
                  density="compact"
                  variant="outlined"
                  placeholder="Buscar unidade ou advogado..."
                  prepend-inner-icon="mdi-magnify"
                  hide-details
                  style="max-width: 300px;"
                  clearable
                />
              </v-card-title>
              <v-card-text class="pa-0">
                <v-data-table
                  :headers="headersAdvocacia"
                  :items="advocaciaFiltrada"
                  :items-per-page="20"
                  density="comfortable"
                  class="elevation-0"
                  no-data-text="Nenhum registro encontrado"
                >
                  <template #item.taxa_cobranca="{ item }">{{ brl(item.taxa_cobranca) }}</template>
                  <template #item.honorarios="{ item }">
                    <span v-if="item.honorarios > 0">{{ brl(item.honorarios) }}</span>
                    <span v-else class="text-medium-emphasis">—</span>
                  </template>
                  <template #item.creditado="{ item }">
                    <span :class="item.creditado > 0 ? 'text-green' : 'text-medium-emphasis'">
                      {{ item.creditado > 0 ? brl(item.creditado) : '—' }}
                    </span>
                  </template>
                  <template #item.status="{ item }">
                    <v-chip :color="item.status === 'liquidado' ? 'green' : 'orange'" size="small" variant="tonal">
                      {{ item.status === 'liquidado' ? 'Liquidado' : 'Pendente' }}
                    </v-chip>
                  </template>
                </v-data-table>
              </v-card-text>
            </v-card>
          </div>

          <!-- Dashboard Despesas por Unidade -->
          <div v-else-if="dashboard && dashboard.tipo === 'despesas'" key="despesas">
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
                Conectado
              </v-chip>
            </div>

            <!-- KPIs -->
            <v-row class="mb-4">
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #F44336;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Total Despesas</span>
                    <v-icon color="red" size="28">mdi-cash-minus</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #F44336;">{{ brl(dashboard.resumo.total_geral) }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">{{ dashboard.resumo.total_registros }} lançamentos</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #2196F3;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Unidades</span>
                    <v-icon color="blue" size="28">mdi-store</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #2196F3;">{{ dashboard.resumo.total_unidades }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">unidades / lojas</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #FF9800;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Fornecedores</span>
                    <v-icon color="orange" size="28">mdi-truck</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #FF9800;">{{ dashboard.resumo.fornecedores_unicos }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">fornecedores únicos</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #9C27B0;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Maior Unidade</span>
                    <v-icon color="purple" size="28">mdi-trophy</v-icon>
                  </div>
                  <div class="text-subtitle-1 font-weight-bold text-truncate" style="color: #9C27B0;">{{ dashboard.resumo.maior_unidade }}</div>
                  <div class="text-caption text-medium-emphasis mt-1">{{ brl(dashboard.resumo.maior_unidade_valor) }}</div>
                </v-card>
              </v-col>
            </v-row>

            <!-- Gráficos -->
            <v-row class="mb-4">
              <v-col cols="12" md="7">
                <v-card elevation="4">
                  <v-card-title class="pa-4 pb-2 d-flex align-center">
                    <v-icon class="mr-2" color="primary">mdi-chart-bar</v-icon>
                    Total por Unidade
                  </v-card-title>
                  <v-card-text>
                    <div style="height: 340px; position: relative;">
                      <canvas ref="chartDespesasUnidade"></canvas>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="5">
                <v-card elevation="4">
                  <v-card-title class="pa-4 pb-2 d-flex align-center">
                    <v-icon class="mr-2" color="primary">mdi-chart-donut</v-icon>
                    Top 10 Fornecedores
                  </v-card-title>
                  <v-card-text>
                    <div style="height: 340px; position: relative;">
                      <canvas ref="chartDespesasFornecedor"></canvas>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>

            <!-- Tabela -->
            <v-card elevation="4">
              <v-card-title class="pa-4 pb-2 d-flex align-center justify-space-between flex-wrap gap-2">
                <div class="d-flex align-center">
                  <v-icon class="mr-2" color="primary">mdi-format-list-bulleted</v-icon>
                  Lançamentos
                </div>
                <div class="d-flex gap-2">
                  <v-select
                    v-model="filtroUnidade"
                    :items="['Todas', ...dashboard.por_unidade.map(u => u.unidade)]"
                    density="compact"
                    variant="outlined"
                    hide-details
                    style="min-width: 200px; max-width: 260px;"
                    label="Filtrar unidade"
                  />
                  <v-text-field
                    v-model="buscaDespesa"
                    density="compact"
                    variant="outlined"
                    placeholder="Buscar fornecedor..."
                    prepend-inner-icon="mdi-magnify"
                    hide-details
                    style="max-width: 240px;"
                    clearable
                  />
                </div>
              </v-card-title>
              <v-card-text class="pa-0">
                <v-data-table
                  :headers="headersDespesas"
                  :items="despesasFiltradas"
                  :items-per-page="20"
                  density="comfortable"
                  class="elevation-0"
                  no-data-text="Nenhum lançamento encontrado"
                  :sort-by="[{ key: 'vencimento', order: 'asc' }]"
                >
                  <template #item.valor="{ item }">
                    <span class="text-red font-weight-medium">{{ brl(item.valor) }}</span>
                  </template>
                </v-data-table>
              </v-card-text>
            </v-card>
          </div>

          <!-- Dashboard Financeiro -->
          <div v-else-if="dashboard" key="financeiro">
            <div class="d-flex align-center justify-space-between mb-4">
              <span class="text-caption text-medium-emphasis">
                <v-icon size="small" class="mr-1">mdi-clock-outline</v-icon>
                Atualizado em {{ dashboard.atualizado_em }}
              </span>
              <v-chip size="small" color="green" variant="tonal">
                <v-icon size="small" class="mr-1">mdi-check-circle</v-icon>
                Conectado
              </v-chip>
            </div>
            <v-row class="mb-4">
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #4CAF50;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Receitas</span>
                    <v-icon color="green" size="28">mdi-trending-up</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #4CAF50;">{{ brl(dashboard.resumo.total_receitas) }}</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #F44336;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Despesas</span>
                    <v-icon color="red" size="28">mdi-trending-down</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #F44336;">{{ brl(dashboard.resumo.total_despesas) }}</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" :style="{ borderLeft: `4px solid ${dashboard.resumo.saldo >= 0 ? '#2196F3' : '#FF9800'}` }">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Saldo</span>
                    <v-icon :color="dashboard.resumo.saldo >= 0 ? 'blue' : 'orange'" size="28">mdi-wallet-plus</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" :style="{ color: dashboard.resumo.saldo >= 0 ? '#2196F3' : '#FF9800' }">{{ brl(dashboard.resumo.saldo) }}</div>
                </v-card>
              </v-col>
              <v-col cols="12" sm="6" md="3">
                <v-card elevation="4" class="kpi-card" style="border-left: 4px solid #9C27B0;">
                  <div class="d-flex align-center justify-space-between mb-2">
                    <span class="text-caption text-uppercase font-weight-bold text-medium-emphasis">Transações</span>
                    <v-icon color="purple" size="28">mdi-swap-horizontal</v-icon>
                  </div>
                  <div class="text-h5 font-weight-bold" style="color: #9C27B0;">{{ dashboard.resumo.total_transacoes }}</div>
                </v-card>
              </v-col>
            </v-row>
            <v-row class="mb-4">
              <v-col cols="12" md="8">
                <v-card elevation="4">
                  <v-card-title class="pa-4 pb-2"><v-icon class="mr-2" color="primary">mdi-chart-line</v-icon>Evolução Mensal</v-card-title>
                  <v-card-text>
                    <div v-if="dashboard.por_mes.length" class="chart-container"><canvas ref="chartMensal"></canvas></div>
                    <div v-else class="text-center text-medium-emphasis pa-8">Sem dados mensais</div>
                  </v-card-text>
                </v-card>
              </v-col>
              <v-col cols="12" md="4">
                <v-card elevation="4">
                  <v-card-title class="pa-4 pb-2"><v-icon class="mr-2" color="primary">mdi-chart-pie</v-icon>Por Categoria</v-card-title>
                  <v-card-text>
                    <div v-if="Object.keys(dashboard.por_categoria).length" class="chart-container-pie"><canvas ref="chartCategoria"></canvas></div>
                    <div v-else class="text-center text-medium-emphasis pa-8">Sem categorias</div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
            <v-card elevation="4">
              <v-card-title class="pa-4 pb-2 d-flex align-center justify-space-between">
                <div><v-icon class="mr-2" color="primary">mdi-format-list-bulleted</v-icon>Últimas Transações</div>
                <v-text-field v-model="buscaTransacao" density="compact" variant="outlined" placeholder="Buscar..." prepend-inner-icon="mdi-magnify" hide-details style="max-width: 250px;" clearable />
              </v-card-title>
              <v-card-text class="pa-0">
                <v-data-table :headers="headersTransacoes" :items="transacoesFiltradas" :items-per-page="10" density="comfortable" class="elevation-0">
                  <template #item.valor="{ item }">
                    <span :class="item.tipo === 'receita' ? 'text-green' : 'text-red'">
                      {{ item.tipo === 'receita' ? '+' : '-' }} {{ brl(Math.abs(item.valor)) }}
                    </span>
                  </template>
                  <template #item.tipo="{ item }">
                    <v-chip :color="item.tipo === 'receita' ? 'green' : 'red'" size="small" variant="tonal">
                      {{ item.tipo === 'receita' ? 'Receita' : 'Despesa' }}
                    </v-chip>
                  </template>
                </v-data-table>
              </v-card-text>
            </v-card>
          </div>

          <!-- Estado vazio (setor selecionado mas sem dados ainda) -->
          <v-card v-else key="empty" elevation="2" class="pa-10 text-center">
            <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-table-large</v-icon>
            <p class="text-h6 text-medium-emphasis">Selecione um setor acima</p>
          </v-card>
        </Transition>
      </div>
    </div>

    <!-- ── Dialog Gerenciar Setores ─────────────────────────────────────────── -->
    <v-dialog v-model="dialogSetores" max-width="680">
      <v-card>
        <v-card-title class="pa-4 d-flex align-center justify-space-between">
          <div><v-icon class="mr-2">mdi-cog</v-icon>Gerenciar Setores</div>
          <v-btn icon variant="text" @click="dialogSetores = false"><v-icon>mdi-close</v-icon></v-btn>
        </v-card-title>
        <v-divider />

        <v-card-text class="pa-4">
          <!-- Lista de setores existentes -->
          <v-list v-if="setores.length" class="mb-4">
            <v-list-item
              v-for="s in setores"
              :key="s.id"
              :title="s.nome"
              :subtitle="`${tipoDashboardLabel(s.tipo_dashboard)} · Aba: ${s.aba}`"
              rounded="lg"
              class="mb-1"
            >
              <template #append>
                <v-btn icon size="small" variant="text" @click="editarSetor(s)">
                  <v-icon size="18">mdi-pencil</v-icon>
                </v-btn>
                <v-btn icon size="small" variant="text" color="red" @click="confirmarDeletar(s)">
                  <v-icon size="18">mdi-delete</v-icon>
                </v-btn>
              </template>
            </v-list-item>
          </v-list>

          <v-divider v-if="setores.length" class="mb-4" />

          <!-- Formulário -->
          <p class="text-subtitle-2 font-weight-bold mb-3">
            {{ formSetor.id ? 'Editar Setor' : 'Adicionar Novo Setor' }}
          </p>
          <v-text-field v-model="formSetor.nome" label="Nome do Setor" variant="outlined" density="compact" class="mb-3" placeholder="Ex: Cobranças Janeiro" />
          <v-text-field v-model="formSetor.spreadsheet_id" label="ID da Planilha Google Sheets" variant="outlined" density="compact" class="mb-3" placeholder="Cole o ID da URL" hint="docs.google.com/spreadsheets/d/[ID]/edit" persistent-hint />
          <div class="d-flex gap-2 align-start mb-3">
            <v-select
              v-if="abasDisponiveis.length"
              v-model="formSetor.aba"
              :items="abasDisponiveis"
              item-title="title"
              item-value="title"
              label="Aba"
              variant="outlined"
              density="compact"
              hide-details
              style="flex: 1"
            />
            <v-text-field
              v-else
              v-model="formSetor.aba"
              label="Nome da Aba"
              variant="outlined"
              density="compact"
              hide-details
              placeholder="Ex: COMP JAN 2026"
              style="flex: 1"
            />
            <v-btn
              :loading="carregandoAbas"
              variant="outlined"
              density="compact"
              style="height: 40px"
              @click="carregarAbasForm"
              title="Buscar abas disponíveis"
            >
              <v-icon>mdi-magnify</v-icon>
            </v-btn>
          </div>
          <v-select
            v-model="formSetor.tipo_dashboard"
            :items="[
              { title: 'Cobranças / Vencimentos', value: 'cobrancas' },
              { title: 'Honorários Advocatícios', value: 'advocacia' },
              { title: 'Despesas por Unidade', value: 'despesas' },
              { title: 'Financeiro', value: 'financeiro' },
            ]"
            item-title="title"
            item-value="value"
            label="Tipo de Dashboard"
            variant="outlined"
            density="compact"
            class="mb-3"
          />
          <v-combobox
            v-model="formSetor.grupo"
            :items="grupos.filter(g => g)"
            label="Grupo (opcional)"
            variant="outlined"
            density="compact"
            placeholder="Ex: Financeiro, Jurídico, Pratika"
            hint="Agrupa setores relacionados em uma categoria"
            persistent-hint
            clearable
          />
        </v-card-text>

        <v-card-actions class="pa-4 pt-0">
          <v-btn v-if="formSetor.id" variant="text" color="grey" @click="resetarForm">Cancelar edição</v-btn>
          <v-spacer />
          <v-btn color="primary" :loading="salvandoSetor" @click="salvarSetor">
            {{ formSetor.id ? 'Salvar Alterações' : 'Adicionar Setor' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog confirmar deleção -->
    <v-dialog v-model="dialogDeletar" max-width="400">
      <v-card>
        <v-card-title class="pa-4">Remover Setor</v-card-title>
        <v-card-text>Deseja remover o setor <strong>{{ setorParaDeletar?.nome }}</strong>?</v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="dialogDeletar = false">Cancelar</v-btn>
          <v-btn color="red" variant="tonal" @click="deletarSetor">Remover</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog de configuração de credenciais -->
    <v-dialog v-model="dialogConfig" max-width="700">
      <v-card>
        <v-card-title class="pa-4 bg-primary"><v-icon class="mr-2">mdi-cog</v-icon>Configuração do Google Sheets</v-card-title>
        <v-card-text class="pa-4">
          <p class="text-body-2 mb-3">Ative a <strong>Google Sheets API</strong> no Google Cloud Console e configure a variável <code>GOOGLE_SHEETS_CREDENTIALS_FILE</code> no docker-compose.</p>
          <v-alert type="info" variant="tonal" density="compact">
            Compartilhe cada planilha com <code>sheets-reader@projetoteste-491111.iam.gserviceaccount.com</code> como Leitor.
          </v-alert>
        </v-card-text>
        <v-card-actions class="pa-4"><v-spacer /><v-btn variant="text" @click="dialogConfig = false">Fechar</v-btn></v-card-actions>
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
const loadingDashboard = ref(false)
const erro = ref('')

const setores = ref([])
const setorAtivoId = ref(null)
const grupoAtivo = ref(null)
const dashboard = ref(null)

const buscaTransacao = ref('')
const buscaCobranca = ref('')
const buscaAdvocacia = ref('')
const buscaDespesa = ref('')
const filtroUnidade = ref('Todas')

const dialogSetores = ref(false)
const dialogConfig = ref(false)
const dialogDeletar = ref(false)
const salvandoSetor = ref(false)
const setorParaDeletar = ref(null)

const formSetor = ref({ id: null, nome: '', spreadsheet_id: '', aba: '', tipo_dashboard: 'cobrancas', grupo: '' })
const abasDisponiveis = ref([])
const carregandoAbas = ref(false)

const chartMensal = ref(null)
const chartCategoria = ref(null)
const chartCobrancas = ref(null)
const chartAdvocacia = ref(null)
const chartDespesasUnidade = ref(null)
const chartDespesasFornecedor = ref(null)
let chartMensalInstance = null
let chartCategoriaInstance = null
let chartCobrancasInstance = null
let chartAdvocaciaInstance = null
let chartDespesasUnidadeInstance = null
let chartDespesasFornecedorInstance = null

// ── Computed ────────────────────────────────────────────────────────────────

const setorAtivo = computed(() => setores.value.find(s => s.id === setorAtivoId.value))

const grupos = computed(() => {
  const set = new Set(setores.value.map(s => s.grupo || ''))
  return [...set].sort()
})

const setoresFiltrados = computed(() => {
  if (grupoAtivo.value === null || grupos.value.length <= 1) return setores.value
  return setores.value.filter(s => (s.grupo || '') === grupoAtivo.value)
})

const transacoesFiltradas = computed(() => {
  if (!dashboard.value?.ultimas_transacoes) return []
  const q = buscaTransacao.value?.toLowerCase().trim()
  if (!q) return dashboard.value.ultimas_transacoes
  return dashboard.value.ultimas_transacoes.filter(t =>
    t.descricao.toLowerCase().includes(q) || t.categoria.toLowerCase().includes(q)
  )
})

const despesasFiltradas = computed(() => {
  if (!dashboard.value?.registros) return []
  return dashboard.value.registros.filter(r => {
    const unidadeOk = filtroUnidade.value === 'Todas' || r.unidade === filtroUnidade.value
    const q = buscaDespesa.value?.toLowerCase().trim()
    const buscaOk = !q || r.fornecedor.toLowerCase().includes(q)
    return unidadeOk && buscaOk
  })
})

const advocaciaFiltrada = computed(() => {
  if (!dashboard.value?.registros) return []
  const q = buscaAdvocacia.value?.toLowerCase().trim()
  if (!q) return dashboard.value.registros
  return dashboard.value.registros.filter(r =>
    r.unidade.toLowerCase().includes(q) ||
    r.advogado.toLowerCase().includes(q) ||
    r.status.toLowerCase().includes(q)
  )
})

const cobrancasFiltradas = computed(() => {
  if (!dashboard.value?.registros) return []
  const q = buscaCobranca.value?.toLowerCase().trim()
  if (!q) return dashboard.value.registros
  return dashboard.value.registros.filter(r =>
    r.condominio.toLowerCase().includes(q) || r.vencimento.toLowerCase().includes(q) || r.status.toLowerCase().includes(q)
  )
})

const headersTransacoes = [
  { title: 'Data', key: 'data', width: 110 },
  { title: 'Descrição', key: 'descricao' },
  { title: 'Categoria', key: 'categoria', width: 140 },
  { title: 'Valor', key: 'valor', width: 140 },
  { title: 'Tipo', key: 'tipo', width: 110 },
]

const headersDespesas = [
  { title: 'Unidade', key: 'unidade', width: 200 },
  { title: 'Vencimento', key: 'vencimento', width: 120 },
  { title: 'Fornecedor', key: 'fornecedor' },
  { title: 'Valor', key: 'valor', width: 130 },
]

const headersAdvocacia = [
  { title: 'Unidade', key: 'unidade' },
  { title: 'Compet.', key: 'competencia', width: 90 },
  { title: 'Vencimento', key: 'vencimento', width: 120 },
  { title: 'Advogado', key: 'advogado', width: 120 },
  { title: 'Taxa Cobrança', key: 'taxa_cobranca', width: 130 },
  { title: 'Honorários', key: 'honorarios', width: 120 },
  { title: 'Creditado', key: 'creditado', width: 120 },
  { title: 'Liquidação', key: 'liquidacao', width: 110 },
  { title: 'Status', key: 'status', width: 110 },
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

const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` })

const brl = (valor) => {
  try { return `R$ ${Number(valor).toLocaleString('pt-BR', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` }
  catch { return `R$ ${valor}` }
}

const tipoDashboardLabel = (tipo) => ({
  cobrancas: 'Cobranças / Vencimentos',
  advocacia: 'Honorários Advocatícios',
  despesas: 'Despesas por Unidade',
  financeiro: 'Financeiro',
  fluxo_caixa: 'Fluxo de Caixa',
}[tipo] || tipo)

// ── API ──────────────────────────────────────────────────────────────────────

const verificarStatus = async () => {
  loadingStatus.value = true
  try {
    const res = await fetch('/api/sheets/status', { headers: authHeader() })
    statusConexao.value = res.ok ? await res.json() : { conectado: false, erro: 'Erro ao verificar conexão' }
  } catch (e) {
    statusConexao.value = { conectado: false, erro: e.message }
  } finally {
    loadingStatus.value = false
  }
}

const selecionarGrupo = (g) => {
  grupoAtivo.value = g
  const primeiro = setores.value.find(s => (s.grupo || '') === g)
  if (primeiro) setorAtivoId.value = primeiro.id
}

const carregarSetores = async () => {
  try {
    const res = await fetch('/api/sheets/setores', { headers: authHeader() })
    if (res.ok) {
      setores.value = await res.json()
      if (setores.value.length && !setorAtivoId.value) {
        grupoAtivo.value = setores.value[0].grupo || ''
        setorAtivoId.value = setores.value[0].id
      }
    }
  } catch { /* silencioso */ }
}

const carregarDashboard = async (force = false) => {
  const setor = setorAtivo.value
  if (!setor) return

  loadingDashboard.value = true
  erro.value = ''
  dashboard.value = null
  filtroUnidade.value = 'Todas'

  try {
    const q = `?aba=${encodeURIComponent(setor.aba)}${force ? '&force=true' : ''}`
    const endpointMap = {
    cobrancas: 'cobrancas',
    advocacia: 'advocacia',
    despesas: 'despesas',
  }
  const path = endpointMap[setor.tipo_dashboard] || 'rapido'
  const endpoint = `/api/sheets/dashboard/${path}/${setor.spreadsheet_id}${q}`

    const res = await fetch(endpoint, { headers: authHeader() })
    if (res.ok) {
      dashboard.value = await res.json()
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

// ── CRUD Setores ─────────────────────────────────────────────────────────────

const salvarSetor = async () => {
  if (!formSetor.value.nome || !formSetor.value.spreadsheet_id) return
  salvandoSetor.value = true
  try {
    const { id, ...payload } = formSetor.value
    const url = id ? `/api/sheets/setores/${id}` : '/api/sheets/setores'
    const method = id ? 'PUT' : 'POST'
    const res = await fetch(url, {
      method,
      headers: { ...authHeader(), 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })
    if (res.ok) {
      await carregarSetores()
      resetarForm()
    }
  } finally {
    salvandoSetor.value = false
  }
}

const editarSetor = (s) => {
  formSetor.value = { id: s.id, nome: s.nome, spreadsheet_id: s.spreadsheet_id, aba: s.aba, tipo_dashboard: s.tipo_dashboard, grupo: s.grupo || '' }
  abasDisponiveis.value = []
}

const resetarForm = () => {
  formSetor.value = { id: null, nome: '', spreadsheet_id: '', aba: '', tipo_dashboard: 'cobrancas', grupo: '' }
  abasDisponiveis.value = []
}

const carregarAbasForm = async () => {
  const id = formSetor.value.spreadsheet_id.trim()
  if (!id) return
  carregandoAbas.value = true
  try {
    const res = await fetch(`/api/sheets/planilha/${id}/abas`, { headers: authHeader() })
    if (res.ok) {
      abasDisponiveis.value = await res.json()
      if (abasDisponiveis.value.length && !formSetor.value.aba) {
        formSetor.value.aba = abasDisponiveis.value[0].title
      }
    }
  } finally {
    carregandoAbas.value = false
  }
}

const confirmarDeletar = (s) => {
  setorParaDeletar.value = s
  dialogDeletar.value = true
}

const deletarSetor = async () => {
  if (!setorParaDeletar.value) return
  await fetch(`/api/sheets/setores/${setorParaDeletar.value.id}`, { method: 'DELETE', headers: authHeader() })
  dialogDeletar.value = false
  setorParaDeletar.value = null
  if (setorAtivoId.value === setorParaDeletar.value?.id) {
    setorAtivoId.value = null
    dashboard.value = null
  }
  await carregarSetores()
}

// ── Gráficos ──────────────────────────────────────────────────────────────────

const destroyCharts = () => {
  if (chartMensalInstance) { chartMensalInstance.destroy(); chartMensalInstance = null }
  if (chartCategoriaInstance) { chartCategoriaInstance.destroy(); chartCategoriaInstance = null }
  if (chartCobrancasInstance) { chartCobrancasInstance.destroy(); chartCobrancasInstance = null }
  if (chartAdvocaciaInstance) { chartAdvocaciaInstance.destroy(); chartAdvocaciaInstance = null }
  if (chartDespesasUnidadeInstance) { chartDespesasUnidadeInstance.destroy(); chartDespesasUnidadeInstance = null }
  if (chartDespesasFornecedorInstance) { chartDespesasFornecedorInstance.destroy(); chartDespesasFornecedorInstance = null }
}

const renderizarGraficos = () => {
  if (!dashboard.value || !chartMensal.value) return
  destroyCharts()

  if (dashboard.value.por_mes?.length) {
    const ctx = chartMensal.value.getContext('2d')
    const labels = dashboard.value.por_mes.map(m => { const [a, ms] = m.mes.split('-'); return `${ms}/${a.slice(2)}` })
    chartMensalInstance = new Chart(ctx, {
      type: 'line',
      data: {
        labels,
        datasets: [
          { label: 'Receitas', data: dashboard.value.por_mes.map(m => m.receitas), borderColor: '#4CAF50', backgroundColor: 'rgba(76,175,80,0.1)', fill: true, tension: 0.3 },
          { label: 'Despesas', data: dashboard.value.por_mes.map(m => m.despesas), borderColor: '#F44336', backgroundColor: 'rgba(244,67,54,0.1)', fill: true, tension: 0.3 },
          { label: 'Saldo', data: dashboard.value.por_mes.map(m => m.saldo), borderColor: '#2196F3', backgroundColor: 'transparent', borderDash: [5, 5], tension: 0.3 },
        ],
      },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } }, scales: { y: { beginAtZero: true, ticks: { callback: v => `R$ ${(v/1000).toFixed(0)}k` } } } },
    })
  }

  if (chartCategoria.value && Object.keys(dashboard.value.por_categoria || {}).length) {
    const ctx = chartCategoria.value.getContext('2d')
    const cats = Object.entries(dashboard.value.por_categoria)
    const cores = ['#4CAF50','#2196F3','#FF9800','#9C27B0','#F44336','#00BCD4','#795548','#607D8B','#E91E63','#3F51B5']
    chartCategoriaInstance = new Chart(ctx, {
      type: 'doughnut',
      data: { labels: cats.map(([k]) => k), datasets: [{ data: cats.map(([,v]) => v.despesas + v.receitas), backgroundColor: cores }] },
      options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'right' } } },
    })
  }
}

const renderizarGraficoCobrancas = () => {
  if (!dashboard.value?.por_vencimento?.length || !chartCobrancas.value) return
  destroyCharts()

  const pv = dashboard.value.por_vencimento
  chartCobrancasInstance = new Chart(chartCobrancas.value.getContext('2d'), {
    type: 'bar',
    data: {
      labels: pv.map(p => p.vencimento),
      datasets: [
        { label: 'Previsto', data: pv.map(p => p.previsto), backgroundColor: 'rgba(33,150,243,0.6)', borderColor: '#2196F3', borderWidth: 1 },
        { label: 'Recebido', data: pv.map(p => p.recebido), backgroundColor: 'rgba(76,175,80,0.7)', borderColor: '#4CAF50', borderWidth: 1 },
      ],
    },
    options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'top' } }, scales: { y: { beginAtZero: true, ticks: { callback: v => `R$ ${(v/1000).toFixed(1)}k` } } } },
  })
}

const renderizarGraficosDespesas = () => {
  if (!dashboard.value?.por_unidade?.length) return
  destroyCharts()

  const cores = ['#F44336','#E91E63','#9C27B0','#673AB7','#3F51B5','#2196F3','#00BCD4','#009688','#4CAF50','#FF9800','#FF5722','#795548','#607D8B','#263238']

  // Gráfico horizontal de barras por unidade
  if (chartDespesasUnidade.value) {
    const pu = [...dashboard.value.por_unidade].reverse() // menor → maior (eixo Y de baixo p/ cima)
    chartDespesasUnidadeInstance = new Chart(chartDespesasUnidade.value.getContext('2d'), {
      type: 'bar',
      data: {
        labels: pu.map(u => u.unidade),
        datasets: [{
          label: 'Total (R$)',
          data: pu.map(u => u.total),
          backgroundColor: cores.slice(0, pu.length).reverse(),
          borderWidth: 0,
          borderRadius: 4,
        }],
      },
      options: {
        indexAxis: 'y',
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: {
          x: { beginAtZero: true, ticks: { callback: v => `R$ ${(v/1000).toFixed(0)}k` } },
          y: { ticks: { font: { size: 11 } } },
        },
      },
    })
  }

  // Donut top 10 fornecedores
  if (chartDespesasFornecedor.value && dashboard.value.por_fornecedor?.length) {
    const pf = dashboard.value.por_fornecedor
    chartDespesasFornecedorInstance = new Chart(chartDespesasFornecedor.value.getContext('2d'), {
      type: 'doughnut',
      data: {
        labels: pf.map(f => f.fornecedor.length > 25 ? f.fornecedor.slice(0, 25) + '…' : f.fornecedor),
        datasets: [{ data: pf.map(f => f.total), backgroundColor: cores.slice(0, pf.length), borderWidth: 1 }],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom', labels: { font: { size: 10 }, boxWidth: 12 } } },
      },
    })
  }
}

const renderizarGraficoAdvocacia = () => {
  if (!dashboard.value?.por_advogado?.length || !chartAdvocacia.value) return
  destroyCharts()

  const pa = dashboard.value.por_advogado
  chartAdvocaciaInstance = new Chart(chartAdvocacia.value.getContext('2d'), {
    type: 'bar',
    data: {
      labels: pa.map(p => p.advogado),
      datasets: [
        { label: 'Taxa de Cobrança', data: pa.map(p => p.taxa_total), backgroundColor: 'rgba(33,150,243,0.6)', borderColor: '#2196F3', borderWidth: 1 },
        { label: 'Creditado', data: pa.map(p => p.creditado_total), backgroundColor: 'rgba(76,175,80,0.7)', borderColor: '#4CAF50', borderWidth: 1 },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { position: 'top' } },
      scales: { y: { beginAtZero: true, ticks: { callback: v => `R$ ${(v/1000).toFixed(1)}k` } } },
    },
  })
}

// ── Watchers ──────────────────────────────────────────────────────────────────

watch(setorAtivoId, (id) => {
  if (id) carregarDashboard()
})

watch(chartCobrancas, (canvas) => {
  if (canvas && dashboard.value?.tipo === 'cobrancas') renderizarGraficoCobrancas()
})

watch(chartAdvocacia, (canvas) => {
  if (canvas && dashboard.value?.tipo === 'advocacia') renderizarGraficoAdvocacia()
})

watch(chartDespesasUnidade, (canvas) => {
  if (canvas && dashboard.value?.tipo === 'despesas') renderizarGraficosDespesas()
})

watch([chartMensal, chartCategoria], ([mensal]) => {
  if (mensal && dashboard.value && dashboard.value.tipo !== 'cobrancas') renderizarGraficos()
})

// ── Lifecycle ─────────────────────────────────────────────────────────────────

onMounted(async () => {
  await verificarStatus()
  if (statusConexao.value.conectado) await carregarSetores()
})

onUnmounted(() => { destroyCharts() })
</script>

<style scoped>
.kpi-card {
  padding: 20px !important;
  height: 130px;
  display: flex;
  flex-direction: column;
}
.chart-container { height: 300px; position: relative; }
.chart-container-pie { height: 280px; position: relative; }
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
