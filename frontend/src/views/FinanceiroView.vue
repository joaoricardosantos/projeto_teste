<template>
  <div>
    <!-- Cabeçalho -->
    <div class="d-flex align-center justify-space-between flex-wrap gap-3 mb-6">
      <div class="d-flex align-center gap-4">
        <div class="page-icon">
          <v-icon size="20" color="white">mdi-currency-usd</v-icon>
        </div>
        <div>
          <h1 class="page-title">Financeiro</h1>
          <p class="page-subtitle">Despesas por condomínio via Superlógica</p>
        </div>
      </div>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="abrirFormDespesa(null)">
        Nova Despesa
      </v-btn>
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
          <div class="d-flex align-center gap-2">
            <v-btn
              color="primary"
              size="small"
              variant="tonal"
              prepend-icon="mdi-plus"
              @click="abrirCriarSuperlogica"
            >Nova no Superlógica</v-btn>
            <v-text-field
              v-model="busca"
              density="compact"
              variant="outlined"
              hide-details
              placeholder="Buscar..."
              prepend-inner-icon="mdi-magnify"
              style="max-width: 240px"
            />
          </div>
        </div>

        <v-data-table
          :headers="headers"
          :items="despesasFiltradas"
          :items-per-page="20"
          density="compact"
          class="text-body-2"
        >
          <template #item.valor="{ item }">{{ brl(item.valor) }}</template>
          <template #item.valor_pago="{ item }">{{ item.valor_pago > 0 ? brl(item.valor_pago) : '-' }}</template>
          <template #item.status="{ item }">
            <v-chip :color="item.status === 'liquidada' ? 'green' : 'red'" size="x-small" variant="tonal">
              {{ item.status }}
            </v-chip>
          </template>
          <template #item.acoes_sl="{ item }">
            <v-tooltip v-if="item.status === 'pendente'" text="Liquidar no Superlógica" location="top">
              <template #activator="{ props }">
                <v-btn v-bind="props" icon size="x-small" variant="text" color="green" @click="abrirLiquidar(item)">
                  <v-icon size="16">mdi-check-circle-outline</v-icon>
                </v-btn>
              </template>
            </v-tooltip>
          </template>
        </v-data-table>
      </v-card>
    </div>
    <!-- ── Despesas Cadastradas no Sistema ── -->
    <v-card class="section-card mt-6" elevation="3">
      <div class="section-header d-flex align-center justify-space-between">
        <div class="section-badge" style="background: linear-gradient(135deg,#059669,#34d399); flex-shrink:0;">
          <v-icon size="16" color="white">mdi-clipboard-list-outline</v-icon>
        </div>
        <div class="flex-grow-1">
          <p class="section-title">Despesas Cadastradas no Sistema</p>
          <p class="section-subtitle">Custos e despesas registrados manualmente</p>
        </div>
        <div class="d-flex align-center gap-3 pr-1">
          <v-chip v-if="despesasLocais.length" size="small" color="primary" variant="tonal">
            {{ despesasLocais.length }} registro{{ despesasLocais.length !== 1 ? 's' : '' }}
          </v-chip>
          <v-select
            v-model="filtroStatusLocal"
            :items="[{title:'Todas',value:'todas'},{title:'Pendentes',value:'pendente'},{title:'Pagas',value:'pago'}]"
            item-title="title"
            item-value="value"
            density="compact"
            variant="outlined"
            hide-details
            style="min-width:130px;"
            @update:model-value="fetchDespesasLocais"
          />
        </div>
      </div>

      <div class="pa-4">
        <div v-if="loadingLocais" class="d-flex align-center justify-center py-8">
          <v-progress-circular indeterminate color="primary" size="28" class="mr-3" />
          <span class="text-body-2 text-medium-emphasis">Carregando...</span>
        </div>

        <div v-else-if="!despesasLocais.length" class="text-center py-10">
          <v-icon size="48" color="grey-lighten-1">mdi-clipboard-text-off-outline</v-icon>
          <p class="text-body-2 text-medium-emphasis mt-3">Nenhuma despesa cadastrada ainda.</p>
          <v-btn color="primary" variant="tonal" size="small" class="mt-3" prepend-icon="mdi-plus" @click="abrirFormDespesa(null)">
            Adicionar despesa
          </v-btn>
        </div>

        <div v-else>
          <!-- KPIs locais -->
          <v-row class="mb-4">
            <v-col cols="6" sm="3">
              <div class="local-kpi">
                <span class="local-kpi__label">Total</span>
                <span class="local-kpi__value">{{ brl(totalLocais) }}</span>
              </div>
            </v-col>
            <v-col cols="6" sm="3">
              <div class="local-kpi local-kpi--red">
                <span class="local-kpi__label">Pendente</span>
                <span class="local-kpi__value">{{ brl(totalLocaisPendente) }}</span>
              </div>
            </v-col>
            <v-col cols="6" sm="3">
              <div class="local-kpi local-kpi--green">
                <span class="local-kpi__label">Pago</span>
                <span class="local-kpi__value">{{ brl(totalLocaisPago) }}</span>
              </div>
            </v-col>
            <v-col cols="6" sm="3">
              <div class="local-kpi">
                <span class="local-kpi__label">Registros</span>
                <span class="local-kpi__value">{{ despesasLocais.length }}</span>
              </div>
            </v-col>
          </v-row>

          <v-data-table
            :headers="headersLocais"
            :items="despesasLocais"
            :items-per-page="10"
            density="compact"
            class="text-body-2"
          >
            <template #item.valor="{ item }">{{ brl(item.valor) }}</template>
            <template #item.status="{ item }">
              <v-chip :color="item.status === 'pago' ? 'green' : 'orange'" size="x-small" variant="tonal">
                {{ item.status === 'pago' ? 'Pago' : 'Pendente' }}
              </v-chip>
            </template>
            <template #item.acoes="{ item }">
              <div class="d-flex gap-1">
                <v-tooltip v-if="item.status === 'pendente'" text="Marcar como pago" location="top">
                  <template #activator="{ props }">
                    <v-btn v-bind="props" icon size="x-small" variant="text" color="green" @click="marcarComoPago(item)">
                      <v-icon size="16">mdi-check-circle-outline</v-icon>
                    </v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip text="Editar" location="top">
                  <template #activator="{ props }">
                    <v-btn v-bind="props" icon size="x-small" variant="text" color="primary" @click="abrirFormDespesa(item)">
                      <v-icon size="16">mdi-pencil-outline</v-icon>
                    </v-btn>
                  </template>
                </v-tooltip>
                <v-tooltip text="Excluir" location="top">
                  <template #activator="{ props }">
                    <v-btn v-bind="props" icon size="x-small" variant="text" color="error" @click="confirmarExclusao(item)">
                      <v-icon size="16">mdi-delete-outline</v-icon>
                    </v-btn>
                  </template>
                </v-tooltip>
              </div>
            </template>
          </v-data-table>
        </div>
      </div>
    </v-card>

    <!-- ── Dialog: Formulário de Despesa ── -->
    <v-dialog v-model="dialogForm" max-width="560" persistent eager>
      <v-card rounded="xl">
        <div class="dialog-header d-flex align-center gap-3">
          <div class="page-icon" style="width:36px;height:36px;border-radius:9px;flex-shrink:0;">
            <v-icon size="18" color="white">{{ formEdicao ? 'mdi-pencil' : 'mdi-plus' }}</v-icon>
          </div>
          <div>
            <p style="font-weight:700;font-size:0.95rem;margin:0;">{{ formEdicao ? 'Editar Despesa' : 'Nova Despesa' }}</p>
            <p style="font-size:0.75rem;opacity:.5;margin:2px 0 0;">Preencha os dados da despesa</p>
          </div>
        </div>
        <v-divider />

        <div class="pa-5">
          <v-form ref="formRef">
            <v-row dense>
              <v-col cols="12">
                <v-select
                  v-model="form.condominio_id"
                  :items="condominios"
                  item-title="nome"
                  item-value="id"
                  label="Condomínio *"
                  variant="outlined"
                  density="comfortable"
                  clearable
                  hide-details="auto"
                  :loading="loadingCondominios"
                  :disabled="loadingCondominios"
                  no-data-text="Nenhum condomínio encontrado"
                  :rules="[v => !!v || 'Obrigatório']"
                  @update:model-value="onFormCondominioChange"
                />
              </v-col>
              <v-col cols="12">
                <v-text-field
                  v-model="form.descricao"
                  label="Descrição *"
                  variant="outlined"
                  density="comfortable"
                  hide-details="auto"
                  :rules="[v => !!v || 'Obrigatório']"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="form.fornecedor"
                  label="Fornecedor"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-combobox
                  v-model="form.categoria"
                  :items="categoriasDisponiveis"
                  label="Categoria"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="form.valor"
                  label="Valor (R$) *"
                  variant="outlined"
                  density="comfortable"
                  type="number"
                  step="0.01"
                  min="0"
                  hide-details="auto"
                  :rules="[v => !!v && v > 0 || 'Informe um valor']"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field
                  v-model="form.vencimento"
                  label="Vencimento *"
                  variant="outlined"
                  density="comfortable"
                  placeholder="DD/MM/AAAA"
                  hide-details="auto"
                  :rules="[v => !!v || 'Obrigatório']"
                />
              </v-col>
              <v-col cols="12" sm="6">
                <v-select
                  v-model="form.status"
                  :items="[{title:'Pendente',value:'pendente'},{title:'Pago',value:'pago'}]"
                  item-title="title"
                  item-value="value"
                  label="Status"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                />
              </v-col>
              <v-col v-if="form.status === 'pago'" cols="12" sm="6">
                <v-text-field
                  v-model="form.data_pagamento"
                  label="Data de Pagamento"
                  variant="outlined"
                  density="comfortable"
                  placeholder="DD/MM/AAAA"
                  hide-details
                />
              </v-col>
              <v-col cols="12">
                <v-textarea
                  v-model="form.observacao"
                  label="Observação"
                  variant="outlined"
                  density="comfortable"
                  rows="2"
                  hide-details
                />
              </v-col>
            </v-row>
          </v-form>

          <v-alert v-if="erroForm" type="error" density="compact" class="mt-3">{{ erroForm }}</v-alert>
        </div>

        <v-divider />
        <div class="d-flex justify-end gap-2 pa-4">
          <v-btn variant="text" color="grey" @click="dialogForm = false">Cancelar</v-btn>
          <v-btn color="primary" :loading="salvando" @click="salvarDespesa">
            <v-icon start size="16">mdi-content-save-outline</v-icon>
            {{ formEdicao ? 'Salvar alterações' : 'Cadastrar despesa' }}
          </v-btn>
        </div>
      </v-card>
    </v-dialog>

    <!-- ── Dialog: Liquidar despesa Superlógica ── -->
    <v-dialog v-model="dialogLiquidar" max-width="560" persistent eager>
      <v-card rounded="xl">
        <div class="dialog-header d-flex align-center gap-3">
          <div class="page-icon" style="width:36px;height:36px;border-radius:9px;flex-shrink:0;">
            <v-icon size="18" color="white">mdi-check-circle-outline</v-icon>
          </div>
          <div>
            <p style="font-weight:700;font-size:0.95rem;margin:0;">Liquidar Despesa</p>
            <p style="font-size:0.75rem;opacity:.5;margin:2px 0 0;">Registra o pagamento diretamente no Superlógica</p>
          </div>
        </div>
        <v-divider />

        <div class="pa-5">
          <v-row dense>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formLiquidar.dt_liquidacao" label="Data de Liquidação *" variant="outlined" density="comfortable" placeholder="DD/MM/AAAA" hide-details="auto" :rules="[v => !!v || 'Obrigatório']" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model.number="formLiquidar.vl_pago" label="Valor Pago (R$) *" variant="outlined" density="comfortable" type="number" step="0.01" hide-details="auto" :rules="[v => v > 0 || 'Obrigatório']" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model.number="formLiquidar.vl_desconto" label="Desconto (R$)" variant="outlined" density="comfortable" type="number" step="0.01" hide-details />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model.number="formLiquidar.vl_multa" label="Multa (R$)" variant="outlined" density="comfortable" type="number" step="0.01" hide-details />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model.number="formLiquidar.vl_juros" label="Juros (R$)" variant="outlined" density="comfortable" type="number" step="0.01" hide-details />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model.number="formLiquidar.id_conta_banco" label="ID Conta Banco" variant="outlined" density="comfortable" type="number" hide-details hint="ID da conta no Superlógica" persistent-hint />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select v-model="formLiquidar.id_forma_pag" :items="formasPagamento" item-title="label" item-value="value" label="Forma de Pagamento" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formLiquidar.nm_numero_ch" label="Nº Cheque / Doc" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12">
              <v-switch v-model="formLiquidar.liquidar_todos" :true-value="1" :false-value="0" label="Liquidar todas as parcelas desta despesa" color="primary" hide-details density="compact" />
            </v-col>
            <v-col cols="12">
              <v-switch v-model="formLiquidar.emitir_recibo" :true-value="1" :false-value="0" label="Emitir recibo" color="primary" hide-details density="compact" />
            </v-col>
          </v-row>

          <!-- Resumo -->
          <v-sheet rounded="lg" class="pa-3 mt-3" color="rgba(5,150,105,0.06)" style="border:1px solid rgba(5,150,105,0.15)">
            <p class="text-caption font-weight-bold mb-1">Resumo</p>
            <div class="d-flex justify-space-between text-caption">
              <span>Despesa: <strong>{{ despesaLiquidando?.descricao }}</strong></span>
              <span>Valor original: <strong>{{ brl(despesaLiquidando?.valor) }}</strong></span>
            </div>
          </v-sheet>

          <v-alert v-if="erroLiquidar" type="error" density="compact" class="mt-3">{{ erroLiquidar }}</v-alert>
        </div>

        <v-divider />
        <div class="d-flex justify-end gap-2 pa-4">
          <v-btn variant="text" color="grey" @click="dialogLiquidar = false">Cancelar</v-btn>
          <v-btn color="green" :loading="salvandoLiquidar" @click="confirmarLiquidacao">
            <v-icon start size="16">mdi-check</v-icon>
            Confirmar liquidação
          </v-btn>
        </div>
      </v-card>
    </v-dialog>

    <!-- ── Dialog: Criar despesa no Superlógica ── -->
    <v-dialog v-model="dialogCriarSL" max-width="600" persistent eager>
      <v-card rounded="xl">
        <div class="dialog-header d-flex align-center gap-3">
          <div class="page-icon" style="width:36px;height:36px;border-radius:9px;flex-shrink:0;">
            <v-icon size="18" color="white">mdi-cloud-upload-outline</v-icon>
          </div>
          <div>
            <p style="font-weight:700;font-size:0.95rem;margin:0;">Nova Despesa no Superlógica</p>
            <p style="font-size:0.75rem;opacity:.5;margin:2px 0 0;">Cria e salva diretamente no Superlógica</p>
          </div>
        </div>
        <v-divider />

        <div class="pa-5">
          <v-row dense>
            <v-col cols="12">
              <v-select
                v-model="formCriarSL.id_condominio"
                :items="condominios"
                item-title="nome"
                item-value="id"
                label="Condomínio *"
                variant="outlined"
                density="comfortable"
                :loading="loadingCondominios"
                hide-details="auto"
                :rules="[v => !!v || 'Obrigatório']"
              />
            </v-col>
            <v-col cols="12">
              <v-text-field v-model="formCriarSL.descricao" label="Descrição / Complemento *" variant="outlined" density="comfortable" hide-details="auto" :rules="[v => !!v || 'Obrigatório']" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formCriarSL.nome_contato" label="Nome do Fornecedor" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formCriarSL.id_conta" label="Conta Contábil (ex: 2.1.1)" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model.number="formCriarSL.vl_valor" label="Valor (R$) *" variant="outlined" density="comfortable" type="number" step="0.01" hide-details="auto" :rules="[v => v > 0 || 'Obrigatório']" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formCriarSL.dt_vencimento" label="Vencimento *" variant="outlined" density="comfortable" placeholder="DD/MM/AAAA" hide-details="auto" :rules="[v => !!v || 'Obrigatório']" />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model="formCriarSL.dt_competencia" label="Competência" variant="outlined" density="comfortable" placeholder="DD/MM/AAAA" hide-details />
            </v-col>
            <v-col cols="12" sm="6">
              <v-select v-model="formCriarSL.id_forma_pag" :items="formasPagamento" item-title="label" item-value="value" label="Forma de Pagamento" variant="outlined" density="comfortable" hide-details />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field v-model.number="formCriarSL.id_conta_banco" label="ID Conta Banco" variant="outlined" density="comfortable" type="number" hide-details />
            </v-col>
            <v-col cols="12">
              <v-textarea v-model="formCriarSL.observacao" label="Observação" variant="outlined" density="comfortable" rows="2" hide-details />
            </v-col>
            <v-col cols="12">
              <v-switch v-model="formCriarSL.liquidar_agora" label="Já liquidar ao criar" color="primary" hide-details density="compact" />
            </v-col>
            <template v-if="formCriarSL.liquidar_agora">
              <v-col cols="12" sm="6">
                <v-text-field v-model="formCriarSL.dt_liquidacao" label="Data Liquidação" variant="outlined" density="comfortable" placeholder="DD/MM/AAAA" hide-details />
              </v-col>
              <v-col cols="12" sm="6">
                <v-text-field v-model.number="formCriarSL.vl_pago" label="Valor Pago (R$)" variant="outlined" density="comfortable" type="number" step="0.01" hide-details />
              </v-col>
            </template>
          </v-row>

          <v-alert v-if="erroCriarSL" type="error" density="compact" class="mt-3">{{ erroCriarSL }}</v-alert>
        </div>

        <v-divider />
        <div class="d-flex justify-end gap-2 pa-4">
          <v-btn variant="text" color="grey" @click="dialogCriarSL = false">Cancelar</v-btn>
          <v-btn color="primary" :loading="salvandoCriarSL" @click="salvarNoSuperlogica">
            <v-icon start size="16">mdi-cloud-upload-outline</v-icon>
            Criar no Superlógica
          </v-btn>
        </div>
      </v-card>
    </v-dialog>

    <!-- ── Dialog: Confirmar exclusão ── -->
    <v-dialog v-model="dialogExcluir" max-width="380">
      <v-card rounded="xl">
        <div class="pa-5 text-center">
          <v-icon size="48" color="error" class="mb-3">mdi-delete-alert-outline</v-icon>
          <p class="font-weight-bold mb-1">Excluir despesa?</p>
          <p class="text-body-2 text-medium-emphasis">
            "<strong>{{ despesaParaExcluir?.descricao }}</strong>" será removida permanentemente.
          </p>
        </div>
        <v-divider />
        <div class="d-flex justify-end gap-2 pa-4">
          <v-btn variant="text" color="grey" @click="dialogExcluir = false">Cancelar</v-btn>
          <v-btn color="error" :loading="excluindo" @click="excluirDespesa">Excluir</v-btn>
        </div>
      </v-card>
    </v-dialog>

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
  { title: 'Descrição',   key: 'descricao',  sortable: true },
  { title: 'Fornecedor',  key: 'fornecedor', sortable: true },
  { title: 'Categoria',   key: 'categoria',  sortable: true },
  { title: 'Vencimento',  key: 'vencimento', sortable: true },
  { title: 'Liquidação',  key: 'liquidacao', sortable: true },
  { title: 'Valor',       key: 'valor',      sortable: true },
  { title: 'Valor Pago',  key: 'valor_pago', sortable: true },
  { title: 'Status',      key: 'status',     sortable: true },
  { title: '',            key: 'acoes_sl',   sortable: false, width: '48px' },
]

const formasPagamento = [
  { value: 0,  label: 'Não especificado' },
  { value: 1,  label: 'Dinheiro' },
  { value: 2,  label: 'Cheque' },
  { value: 3,  label: 'Cartão de Débito' },
  { value: 4,  label: 'Cartão de Crédito' },
  { value: 5,  label: 'TED / DOC' },
  { value: 6,  label: 'Boleto' },
  { value: 7,  label: 'PIX' },
  { value: 8,  label: 'Débito em Conta' },
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

// ── Liquidar no Superlógica ────────────────────────────────────────────────────
const dialogLiquidar     = ref(false)
const salvandoLiquidar   = ref(false)
const erroLiquidar       = ref('')
const despesaLiquidando  = ref(null)

const formLiquidarVazio = () => ({
  dt_liquidacao:  new Date().toLocaleDateString('pt-BR'),
  vl_pago:        0,
  vl_desconto:    0,
  vl_multa:       0,
  vl_juros:       0,
  id_conta_banco: 0,
  id_forma_pag:   0,
  nm_numero_ch:   '',
  liquidar_todos: 0,
  emitir_recibo:  0,
})
const formLiquidar = ref(formLiquidarVazio())

const abrirLiquidar = (despesa) => {
  despesaLiquidando.value = despesa
  erroLiquidar.value = ''
  formLiquidar.value = {
    ...formLiquidarVazio(),
    vl_pago: despesa.valor,
  }
  dialogLiquidar.value = true
}

const confirmarLiquidacao = async () => {
  if (!formLiquidar.value.dt_liquidacao || formLiquidar.value.vl_pago <= 0) {
    erroLiquidar.value = 'Informe a data e o valor pago.'
    return
  }
  salvandoLiquidar.value = true
  erroLiquidar.value = ''
  try {
    const d = despesaLiquidando.value
    const cond = condominioSelecionado.value[0] || 0
    const res = await fetch('/api/financeiro/liquidar', {
      method: 'POST',
      headers: authHeader(),
      body: JSON.stringify({
        id_condominio:  cond,
        id_despesa:     d.id,
        id_parcela:     d.id_parcela || '',
        id_contato:     d.id_contato || '',
        nome_contato:   d.fornecedor || '',
        ...formLiquidar.value,
      }),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Erro ao liquidar')
    dialogLiquidar.value = false
    // Recarrega as despesas
    await buscar()
  } catch (e) {
    erroLiquidar.value = e.message
  } finally {
    salvandoLiquidar.value = false
  }
}

// ── Criar no Superlógica ───────────────────────────────────────────────────────
const dialogCriarSL    = ref(false)
const salvandoCriarSL  = ref(false)
const erroCriarSL      = ref('')

const formCriarSLVazio = () => ({
  id_condominio:  null,
  descricao:      '',
  nome_contato:   '',
  id_conta:       '',
  vl_valor:       0,
  dt_vencimento:  new Date().toLocaleDateString('pt-BR'),
  dt_competencia: '',
  id_forma_pag:   0,
  id_conta_banco: 0,
  observacao:     '',
  liquidar_agora: false,
  dt_liquidacao:  '',
  vl_pago:        0,
})
const formCriarSL = ref(formCriarSLVazio())

const abrirCriarSuperlogica = () => {
  erroCriarSL.value = ''
  formCriarSL.value = {
    ...formCriarSLVazio(),
    id_condominio: condominioSelecionado.value[0] || null,
  }
  if (!condominios.value.length && !loadingCondominios.value) fetchCondominios()
  dialogCriarSL.value = true
}

const salvarNoSuperlogica = async () => {
  if (!formCriarSL.value.id_condominio || !formCriarSL.value.descricao || formCriarSL.value.vl_valor <= 0) {
    erroCriarSL.value = 'Preencha os campos obrigatórios.'
    return
  }
  salvandoCriarSL.value = true
  erroCriarSL.value = ''
  try {
    const res = await fetch('/api/financeiro/criar-superlogica', {
      method: 'POST',
      headers: authHeader(),
      body: JSON.stringify(formCriarSL.value),
    })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Erro ao criar despesa')
    dialogCriarSL.value = false
    await buscar()
  } catch (e) {
    erroCriarSL.value = e.message
  } finally {
    salvandoCriarSL.value = false
  }
}

// ── Despesas Locais ────────────────────────────────────────────────────────────
const despesasLocais    = ref([])
const loadingLocais     = ref(false)
const filtroStatusLocal = ref('todas')
const dialogForm        = ref(false)
const dialogExcluir     = ref(false)
const formEdicao        = ref(null)   // null = novo, objeto = editar
const salvando          = ref(false)
const excluindo         = ref(false)
const erroForm          = ref('')
const despesaParaExcluir = ref(null)
const formRef           = ref(null)

const categoriasDisponiveis = [
  'Manutenção', 'Limpeza', 'Segurança', 'Água', 'Energia', 'Internet',
  'Seguro', 'Administração', 'Jurídico', 'Outros',
]

const formVazio = () => ({
  condominio_id:   null,
  condominio_nome: '',
  descricao:       '',
  fornecedor:      '',
  categoria:       '',
  valor:           '',
  vencimento:      '',
  data_pagamento:  '',
  status:          'pendente',
  observacao:      '',
})

const form = ref(formVazio())

const headersLocais = [
  { title: 'Condomínio',  key: 'condominio_nome', sortable: true },
  { title: 'Descrição',   key: 'descricao',        sortable: true },
  { title: 'Fornecedor',  key: 'fornecedor',        sortable: true },
  { title: 'Categoria',   key: 'categoria',         sortable: true },
  { title: 'Vencimento',  key: 'vencimento',        sortable: true },
  { title: 'Valor',       key: 'valor',             sortable: true },
  { title: 'Status',      key: 'status',            sortable: true },
  { title: 'Ações',       key: 'acoes',             sortable: false, align: 'center' },
]

const totalLocais        = computed(() => despesasLocais.value.reduce((s, d) => s + d.valor, 0))
const totalLocaisPendente = computed(() => despesasLocais.value.filter(d => d.status === 'pendente').reduce((s, d) => s + d.valor, 0))
const totalLocaisPago    = computed(() => despesasLocais.value.filter(d => d.status === 'pago').reduce((s, d) => s + d.valor, 0))

const fetchDespesasLocais = async () => {
  loadingLocais.value = true
  try {
    const params = new URLSearchParams()
    if (filtroStatusLocal.value !== 'todas') params.set('status', filtroStatusLocal.value)
    const res = await fetch(`/api/financeiro/locais?${params}`, { headers: authHeader() })
    if (res.ok) despesasLocais.value = await res.json()
  } catch { /* silencioso */ }
  finally { loadingLocais.value = false }
}

const onFormCondominioChange = (id) => {
  const condo = condominios.value.find(c => c.id === id)
  form.value.condominio_nome = condo?.nome || ''
}

const abrirFormDespesa = (despesa) => {
  erroForm.value = ''
  // Garante que os condomínios estejam carregados
  if (!condominios.value.length && !loadingCondominios.value) {
    fetchCondominios()
  }
  if (despesa) {
    formEdicao.value = despesa
    form.value = {
      condominio_id:   despesa.condominio_id,
      condominio_nome: despesa.condominio_nome,
      descricao:       despesa.descricao,
      fornecedor:      despesa.fornecedor,
      categoria:       despesa.categoria,
      valor:           despesa.valor,
      vencimento:      despesa.vencimento,
      data_pagamento:  despesa.data_pagamento || '',
      status:          despesa.status,
      observacao:      despesa.observacao,
    }
  } else {
    formEdicao.value = null
    form.value = formVazio()
  }
  dialogForm.value = true
}

const parseDate = (str) => {
  if (!str) return null
  const [d, m, y] = str.split('/')
  return `${y}-${m}-${d}`
}

const salvarDespesa = async () => {
  const { valid } = await formRef.value.validate()
  if (!valid) return
  salvando.value = true
  erroForm.value = ''
  try {
    const payload = {
      ...form.value,
      valor:          parseFloat(form.value.valor),
      vencimento:     parseDate(form.value.vencimento),
      data_pagamento: form.value.data_pagamento ? parseDate(form.value.data_pagamento) : null,
    }
    const url    = formEdicao.value ? `/api/financeiro/locais/${formEdicao.value.id}` : '/api/financeiro/locais'
    const method = formEdicao.value ? 'PUT' : 'POST'
    const res = await fetch(url, { method, headers: authHeader(), body: JSON.stringify(payload) })
    if (!res.ok) {
      const err = await res.json()
      throw new Error(err.detail || 'Erro ao salvar')
    }
    dialogForm.value = false
    await fetchDespesasLocais()
  } catch (e) {
    erroForm.value = e.message
  } finally {
    salvando.value = false
  }
}

const marcarComoPago = async (despesa) => {
  try {
    const payload = {
      condominio_id:   despesa.condominio_id,
      condominio_nome: despesa.condominio_nome,
      descricao:       despesa.descricao,
      fornecedor:      despesa.fornecedor,
      categoria:       despesa.categoria,
      valor:           despesa.valor,
      vencimento:      parseDate(despesa.vencimento),
      data_pagamento:  parseDate(new Date().toLocaleDateString('pt-BR')),
      status:          'pago',
      observacao:      despesa.observacao,
    }
    await fetch(`/api/financeiro/locais/${despesa.id}`, {
      method: 'PUT', headers: authHeader(), body: JSON.stringify(payload),
    })
    await fetchDespesasLocais()
  } catch { /* silencioso */ }
}

const confirmarExclusao = (despesa) => {
  despesaParaExcluir.value = despesa
  dialogExcluir.value = true
}

const excluirDespesa = async () => {
  excluindo.value = true
  try {
    await fetch(`/api/financeiro/locais/${despesaParaExcluir.value.id}`, {
      method: 'DELETE', headers: authHeader(),
    })
    dialogExcluir.value = false
    await fetchDespesasLocais()
  } catch { /* silencioso */ }
  finally { excluindo.value = false }
}

onMounted(() => {
  fetchCondominios()
  fetchDespesasLocais()
})
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

/* ── Despesas Locais ── */
.local-kpi {
  padding: 12px 16px;
  border-radius: 10px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-border-color), 0.08);
}
.local-kpi--red   { border-left: 3px solid #ef4444; }
.local-kpi--green { border-left: 3px solid #22c55e; }
.local-kpi__label {
  display: block;
  font-size: 0.72rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  opacity: .55;
  margin-bottom: 4px;
}
.local-kpi__value {
  display: block;
  font-size: 1.1rem;
  font-weight: 700;
  color: rgb(var(--v-theme-on-surface));
}

/* dialog-header usado nos dialogs desta view */
.dialog-header {
  padding: 16px 20px;
  border-left: 3px solid #34d399;
}
</style>
