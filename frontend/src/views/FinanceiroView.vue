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
      <v-btn color="primary" prepend-icon="mdi-plus" @click="abrirCriarSuperlogica">
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
        <!-- Filtros salvos -->
        <div v-if="filtrosSalvos.length" class="mb-4">
          <p class="text-caption text-medium-emphasis text-uppercase font-weight-bold mb-2" style="letter-spacing:.05em;">Filtros salvos</p>
          <div class="d-flex flex-wrap gap-2">
            <v-chip
              v-for="f in filtrosSalvos"
              :key="f.nome"
              :color="filtroAtivoNome === f.nome ? 'primary' : undefined"
              :variant="filtroAtivoNome === f.nome ? 'flat' : 'tonal'"
              size="small"
              closable
              @click="aplicarFiltroSalvo(f)"
              @click:close="excluirFiltroSalvo(f.nome)"
            >
              <v-icon start size="14">mdi-bookmark-outline</v-icon>
              {{ f.nome }}
              <span class="ml-1 opacity-60">({{ f.ids.length }})</span>
            </v-chip>
          </div>
        </div>

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
              :hide-details="!loadingCondominios"
              multiple
              chips
              closable-chips
              :disabled="loadingCondominios || loading"
              :no-data-text="loadingCondominios ? 'Carregando condomínios...' : 'Nenhum condomínio encontrado'"
              :placeholder="loadingCondominios ? 'Carregando, só um momento...' : 'Selecione um ou mais condomínios...'"
              :loading="loadingCondominios"
              :hint="loadingCondominios ? 'Buscando condomínios disponíveis...' : ''"
              :persistent-hint="loadingCondominios"
              @update:model-value="filtroAtivoNome = null"
            >
              <template #item="{ props, item }">
                <v-list-item v-bind="props" :title="item.raw.nome">
                  <template #prepend>
                    <span class="text-caption text-medium-emphasis mr-3" style="min-width:28px; text-align:right; font-variant-numeric: tabular-nums;">#{{ item.raw.id }}</span>
                  </template>
                </v-list-item>
              </template>
              <template #chip="{ props, item, index }">
                <template v-if="filtroAtivoNome">
                  <v-chip v-if="index === 0" color="primary" variant="flat" prepend-icon="mdi-bookmark">
                    {{ filtroAtivoNome }}
                    <span class="text-caption ml-1 opacity-70">({{ condominioSelecionado.length }})</span>
                  </v-chip>
                </template>
                <template v-else>
                  <v-chip v-bind="props">
                    <span class="text-caption opacity-60 mr-1">#{{ item.raw.id }}</span>
                    {{ item.raw.nome }}
                  </v-chip>
                </template>
              </template>
              <template #prepend-item>
                <v-list-item
                  :title="condominioSelecionado.length === condominios.length ? 'Desmarcar todas' : 'Selecionar todas'"
                  :prepend-icon="condominioSelecionado.length === condominios.length ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline'"
                  @click="condominioSelecionado.length === condominios.length ? condominioSelecionado = [] : condominioSelecionado = condominios.map(c => c.id); filtroAtivoNome = null"
                />
                <v-divider class="mb-1" />
              </template>
            </v-autocomplete>
          </v-col>

          <v-col cols="12" sm="6" md="2">
            <v-menu v-model="menuDtInicio" :close-on-content-click="false" min-width="0">
              <template #activator="{ props }">
                <v-text-field
                  v-bind="props"
                  :model-value="dtInicio"
                  label="Data início"
                  variant="outlined"
                  density="comfortable"
                  placeholder="DD/MM/AAAA"
                  hide-details
                  readonly
                  :disabled="loading"
                  prepend-inner-icon="mdi-calendar-outline"
                />
              </template>
              <v-date-picker
                :model-value="dtInicioISO"
                color="primary"
                show-adjacent-months
                @update:model-value="val => { dtInicio = isoParaBR(val); menuDtInicio = false }"
              />
            </v-menu>
          </v-col>

          <v-col cols="12" sm="6" md="2">
            <v-menu v-model="menuDtFim" :close-on-content-click="false" min-width="0">
              <template #activator="{ props }">
                <v-text-field
                  v-bind="props"
                  :model-value="dtFim"
                  label="Data fim"
                  variant="outlined"
                  density="comfortable"
                  placeholder="DD/MM/AAAA"
                  hide-details
                  readonly
                  :disabled="loading"
                  prepend-inner-icon="mdi-calendar-outline"
                />
              </template>
              <v-date-picker
                :model-value="dtFimISO"
                color="primary"
                show-adjacent-months
                @update:model-value="val => { dtFim = isoParaBR(val); menuDtFim = false }"
              />
            </v-menu>
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

          <v-col cols="12" sm="6" md="2" class="d-flex flex-column gap-2 align-start">
            <v-btn
              color="primary"
              block
              size="large"
              prepend-icon="mdi-magnify"
              :loading="loading"
              :disabled="!condominioSelecionado.length || !dtInicio || !dtFim || loading"
              @click="buscar"
            >Buscar despesas</v-btn>
            <v-btn
              v-if="condominioSelecionado.length"
              block
              size="small"
              variant="tonal"
              color="primary"
              prepend-icon="mdi-bookmark-plus-outline"
              @click="dialogSalvarFiltro = true"
            >Salvar filtro</v-btn>
          </v-col>
        </v-row>
      </div>
    </v-card>

    <!-- ── Dialog: Salvar filtro ── -->
    <v-dialog v-model="dialogSalvarFiltro" max-width="400" persistent>
      <v-card rounded="xl">
        <div class="dialog-header d-flex align-center gap-3">
          <div class="page-icon" style="width:36px;height:36px;border-radius:9px;flex-shrink:0;">
            <v-icon size="18" color="white">mdi-bookmark-plus-outline</v-icon>
          </div>
          <div>
            <p style="font-weight:700;font-size:0.95rem;margin:0;">Salvar filtro</p>
            <p style="font-size:0.75rem;opacity:.5;margin:2px 0 0;">{{ condominioSelecionado.length }} condomínio(s) selecionado(s)</p>
          </div>
        </div>
        <v-divider />
        <div class="pa-5">
          <v-text-field
            v-model="novoFiltroNome"
            label="Nome do filtro"
            variant="outlined"
            density="comfortable"
            placeholder="Ex: Zona Sul, Clientes VIP..."
            autofocus
            hide-details="auto"
            :rules="[v => !!v || 'Informe um nome']"
            @keyup.enter="confirmarSalvarFiltro"
          />
          <v-alert v-if="erroSalvarFiltro" type="error" density="compact" class="mt-3">{{ erroSalvarFiltro }}</v-alert>
        </div>
        <v-divider />
        <div class="d-flex justify-end gap-2 pa-4">
          <v-btn variant="text" color="grey" @click="dialogSalvarFiltro = false; novoFiltroNome = ''; erroSalvarFiltro = ''">Cancelar</v-btn>
          <v-btn color="primary" :disabled="!novoFiltroNome.trim()" @click="confirmarSalvarFiltro">Salvar</v-btn>
        </div>
      </v-card>
    </v-dialog>

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
      <v-dialog v-model="dialogKpi" max-width="960">
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
              v-model="selecionadasParaPagar"
              :headers="dialogFiltro === 'pendente' ? headersPendentes : headersDialog"
              :items="dialogItens"
              :items-per-page="15"
              density="compact"
              class="text-body-2"
              :show-select="dialogFiltro === 'pendente' || dialogModoCategoria"
              item-value="id"
              return-object
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

            <div class="d-flex align-center justify-space-between mt-3 flex-wrap gap-2">
              <div v-if="dialogFiltro === 'pendente' || dialogModoCategoria" class="d-flex align-center gap-2 flex-wrap">
                <v-btn
                  size="small"
                  variant="tonal"
                  :color="selecionadasParaPagar.length === dialogItens.length ? 'grey' : 'indigo'"
                  :prepend-icon="selecionadasParaPagar.length === dialogItens.length ? 'mdi-checkbox-marked' : 'mdi-checkbox-blank-outline'"
                  @click="selecionadasParaPagar = selecionadasParaPagar.length === dialogItens.length ? [] : [...dialogItens]"
                >
                  {{ selecionadasParaPagar.length === dialogItens.length ? 'Desmarcar tudo' : 'Selecionar tudo' }}
                </v-btn>
                <v-btn
                  v-if="selecionadasParaPagar.length"
                  color="warning"
                  variant="tonal"
                  prepend-icon="mdi-clock-outline"
                  :loading="marcandoPagamento"
                  @click="marcarParaPagamento"
                >
                  Marcar {{ selecionadasParaPagar.length }} para pagamento
                </v-btn>
                <span v-else class="text-caption text-medium-emphasis">
                  Selecione despesas para encaminhar ao financeiro
                </span>
              </div>
              <strong class="ml-auto">
                <span v-if="selecionadasParaPagar.length" class="text-caption text-medium-emphasis mr-2">
                  {{ selecionadasParaPagar.length }} selecionada(s) /
                </span>
                Total: {{ brl((selecionadasParaPagar.length ? selecionadasParaPagar : dialogItens).reduce((s, d) => s + (Number(d.valor) || 0), 0)) }}
              </strong>
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
                v-for="(cat, i) in categoriasDinamicas"
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
                  <div class="d-flex align-center gap-3">
                    <span class="text-body-2 font-weight-bold">{{ brl(cat.total) }}</span>
                    <v-btn
                      size="x-small"
                      variant="tonal"
                      color="indigo"
                      icon
                      :title="`Enviar despesas de '${cat.categoria}' para fila`"
                      @click="abrirDialogCategoria(cat.categoria)"
                    >
                      <v-icon size="14">mdi-send-outline</v-icon>
                    </v-btn>
                  </div>
                </div>
                <v-progress-linear
                  :model-value="pct(cat.total, totalGeralDinamico)"
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
                  <div class="d-flex align-center gap-3">
                    <span class="text-body-2 font-weight-bold">{{ brl(forn.total) }}</span>
                    <v-btn size="x-small" variant="tonal" color="teal" icon :title="`Enviar despesas de '${forn.fornecedor}' para fila`" @click="abrirDialogFornecedor(forn.fornecedor)">
                      <v-icon size="14">mdi-send-outline</v-icon>
                    </v-btn>
                  </div>
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
    <!-- ── Fila de Pagamentos ── -->
    <v-card class="section-card mt-6" elevation="3">
      <div class="section-header d-flex align-center justify-space-between">
        <div class="section-badge" style="background: linear-gradient(135deg,#f59e0b,#d97706);">
          <v-icon size="16" color="white">mdi-clock-outline</v-icon>
        </div>
        <div class="flex-grow-1">
          <p class="section-title">Fila de Pagamentos</p>
          <p class="section-subtitle">Despesas encaminhadas para o financeiro pagar</p>
        </div>
        <div class="d-flex align-center gap-2">
          <v-chip v-if="filaPagamento.filter(i=>i.status==='aguardando').length" color="warning" size="small" variant="tonal">
            {{ filaPagamento.filter(i=>i.status==='aguardando').length }} aguardando
          </v-chip>
          <v-select
            v-model="filaFiltroStatus"
            :items="[{title:'Aguardando',value:'aguardando'},{title:'Pagas',value:'pago'},{title:'Canceladas',value:'cancelado'},{title:'Todas',value:'todas'}]"
            item-title="title"
            item-value="value"
            density="compact"
            variant="outlined"
            hide-details
            style="max-width:160px;"
            @update:model-value="fetchFilaPagamento"
          />
          <v-btn icon size="small" variant="text" :loading="loadingFila" @click="fetchFilaPagamento">
            <v-icon size="18">mdi-refresh</v-icon>
          </v-btn>
        </div>
      </div>
      <v-divider />

      <div class="pa-4">
        <div v-if="!loadingFila && !filaPagamento.length" class="text-center py-8 text-disabled">
          <v-icon size="40" class="mb-2 opacity-30">mdi-clock-check-outline</v-icon>
          <p style="font-size:0.85rem;">Nenhuma despesa na fila de pagamento.</p>
        </div>

        <v-table v-else density="compact">
          <thead>
            <tr>
              <th>Descrição</th>
              <th>Fornecedor</th>
              <th>Condomínio</th>
              <th>Vencimento</th>
              <th class="text-right">Valor</th>
              <th>Status</th>
              <th>Encaminhado por</th>
              <th class="text-center">Ações</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in filaPagamento" :key="item.id">
              <td>{{ item.descricao }}</td>
              <td class="text-medium-emphasis">{{ item.fornecedor || '—' }}</td>
              <td class="text-medium-emphasis" style="max-width:160px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{{ item.condominio_nome }}</td>
              <td>{{ item.vencimento || '—' }}</td>
              <td class="text-right font-weight-bold">{{ brl(item.valor) }}</td>
              <td>
                <v-chip
                  :color="item.status==='pago'?'success':item.status==='cancelado'?'error':'warning'"
                  size="x-small" variant="tonal"
                >{{ item.status }}</v-chip>
              </td>
              <td class="text-caption text-medium-emphasis">{{ item.marcado_por }}</td>
              <td class="text-center">
                <div class="d-flex gap-1 justify-center">
                  <v-tooltip v-if="item.status==='aguardando'" text="Marcar como Pago" location="top">
                    <template #activator="{ props }">
                      <v-btn v-bind="props" icon size="x-small" variant="text" color="success"
                        @click="atualizarStatusFila(item.id, 'pago')">
                        <v-icon size="16">mdi-check-circle-outline</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                  <v-tooltip v-if="item.status==='aguardando'" text="Cancelar" location="top">
                    <template #activator="{ props }">
                      <v-btn v-bind="props" icon size="x-small" variant="text" color="error"
                        @click="atualizarStatusFila(item.id, 'cancelado')">
                        <v-icon size="16">mdi-close-circle-outline</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                  <v-tooltip text="Remover" location="top">
                    <template #activator="{ props }">
                      <v-btn v-bind="props" icon size="x-small" variant="text" color="grey"
                        @click="removerDaFila(item.id)">
                        <v-icon size="15">mdi-delete-outline</v-icon>
                      </v-btn>
                    </template>
                  </v-tooltip>
                </div>
              </td>
            </tr>
          </tbody>
        </v-table>

        <div v-if="filaPagamento.length" class="d-flex justify-end align-center mt-3 px-2">
          <span class="text-caption text-medium-emphasis mr-3">
            {{ filaPagamento.length }} item(s)
          </span>
          <strong style="font-size:1rem;">
            Total: {{ brl(filaPagamento.reduce((s, i) => s + (Number(i.valor) || 0), 0)) }}
          </strong>
        </div>
      </div>
    </v-card>

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
    <v-dialog v-model="dialogCriarSL" max-width="680" persistent scrollable>
      <v-card rounded="xl">

        <!-- Header -->
        <div class="dialog-header d-flex align-center gap-3">
          <div class="page-icon" style="width:38px;height:38px;border-radius:10px;flex-shrink:0;">
            <v-icon size="19" color="white">mdi-cloud-upload-outline</v-icon>
          </div>
          <div>
            <p style="font-weight:700;font-size:1rem;margin:0;">Nova Despesa no Superlógica</p>
            <p style="font-size:0.75rem;opacity:.5;margin:2px 0 0;">Preencha os dados e clique em Criar</p>
          </div>
        </div>
        <v-divider />

        <v-card-text class="pa-0">
          <div class="sl-form-body">

            <!-- Seção 1: Condomínio e Descrição -->
            <div class="sl-section">
              <p class="sl-section-label">
                <v-icon size="13" class="mr-1">mdi-office-building-outline</v-icon>
                Identificação
              </p>
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
                  <v-text-field
                    v-model="formCriarSL.descricao"
                    label="Descrição / Complemento *"
                    variant="outlined"
                    density="comfortable"
                    hide-details="auto"
                    :rules="[v => !!v || 'Obrigatório']"
                    prepend-inner-icon="mdi-text-short"
                  />
                </v-col>
              </v-row>
            </div>

            <v-divider />

            <!-- Seção 2: Fornecedor -->
            <div class="sl-section">
              <p class="sl-section-label">
                <v-icon size="13" class="mr-1">mdi-account-outline</v-icon>
                Fornecedor / Favorecido
              </p>
              <v-row dense>
                <v-col cols="12" sm="7">
                  <v-text-field
                    v-model="formCriarSL.nome_contato"
                    label="Nome do Fornecedor *"
                    variant="outlined"
                    density="comfortable"
                    hide-details="auto"
                    :rules="[v => !!v || 'Obrigatório']"
                    prepend-inner-icon="mdi-account"
                  />
                </v-col>
                <v-col cols="12" sm="5">
                  <v-text-field
                    v-model="formCriarSL.id_contato"
                    label="ID Superlógica *"
                    variant="outlined"
                    density="comfortable"
                    hide-details="auto"
                    :rules="[v => !!v || 'Obrigatório']"
                    prepend-inner-icon="mdi-identifier"
                    hint="Ver em Despesas → Favorecidos"
                    persistent-hint
                  />
                </v-col>
              </v-row>
            </div>

            <v-divider />

            <!-- Seção 3: Valores e Parcelas -->
            <div class="sl-section">
              <p class="sl-section-label">
                <v-icon size="13" class="mr-1">mdi-cash-multiple</v-icon>
                Valores e Parcelas
              </p>
              <v-row dense>
                <v-col cols="6" sm="4">
                  <v-text-field
                    v-model.number="formCriarSL.vl_valor"
                    label="Valor Total (R$) *"
                    variant="outlined"
                    density="comfortable"
                    type="number"
                    step="0.01"
                    min="0"
                    hide-details="auto"
                    :rules="[v => v > 0 || 'Obrigatório']"
                    prepend-inner-icon="mdi-currency-brl"
                  />
                </v-col>
                <v-col cols="6" sm="4">
                  <v-text-field
                    v-model="formCriarSL.dt_vencimento"
                    label="1º Vencimento *"
                    variant="outlined"
                    density="comfortable"
                    placeholder="DD/MM/AAAA"
                    hide-details="auto"
                    :rules="[v => !!v || 'Obrigatório']"
                    prepend-inner-icon="mdi-calendar"
                  />
                </v-col>
                <v-col cols="6" sm="4">
                  <v-text-field
                    v-model.number="formCriarSL.qt_parcelas"
                    label="Parcelas"
                    variant="outlined"
                    density="comfortable"
                    type="number"
                    min="1"
                    max="60"
                    hide-details
                    prepend-inner-icon="mdi-numeric"
                  />
                </v-col>
              </v-row>
            </div>

            <v-divider />

            <!-- Seção 4: Dados Complementares -->
            <div class="sl-section">
              <p class="sl-section-label">
                <v-icon size="13" class="mr-1">mdi-tune-variant</v-icon>
                Dados Complementares
              </p>
              <v-row dense>
                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model="formCriarSL.dt_competencia"
                    label="Competência"
                    variant="outlined"
                    density="comfortable"
                    placeholder="DD/MM/AAAA"
                    hide-details
                    prepend-inner-icon="mdi-calendar-month"
                  />
                </v-col>
                <v-col cols="12" sm="4">
                  <v-select
                    v-model="formCriarSL.id_forma_pag"
                    :items="formasPagamento"
                    item-title="label"
                    item-value="value"
                    label="Forma de Pagamento"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                  />
                </v-col>
                <v-col cols="12" sm="4">
                  <v-text-field
                    v-model="formCriarSL.id_conta"
                    label="Conta Contábil"
                    placeholder="ex: 2.1.1"
                    variant="outlined"
                    density="comfortable"
                    hide-details
                    prepend-inner-icon="mdi-book-outline"
                  />
                </v-col>
                <v-col cols="12">
                  <v-textarea
                    v-model="formCriarSL.observacao"
                    label="Observação"
                    variant="outlined"
                    density="comfortable"
                    rows="2"
                    hide-details
                    prepend-inner-icon="mdi-note-text-outline"
                  />
                </v-col>
              </v-row>
            </div>

            <!-- Seção 5: Liquidação imediata -->
            <div class="sl-section sl-section--liquidar">
              <div class="d-flex align-center justify-space-between">
                <div>
                  <p class="sl-section-label mb-0">
                    <v-icon size="13" class="mr-1">mdi-check-circle-outline</v-icon>
                    Liquidar ao criar
                  </p>
                  <p style="font-size:0.72rem;opacity:.45;margin:2px 0 0;">Marca a 1ª parcela como paga imediatamente</p>
                </div>
                <v-switch v-model="formCriarSL.liquidar_agora" color="primary" hide-details density="compact" />
              </div>
              <v-row v-if="formCriarSL.liquidar_agora" dense class="mt-3">
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model="formCriarSL.dt_liquidacao"
                    label="Data de Liquidação"
                    variant="outlined"
                    density="comfortable"
                    placeholder="DD/MM/AAAA"
                    hide-details
                    prepend-inner-icon="mdi-calendar-check"
                  />
                </v-col>
                <v-col cols="12" sm="6">
                  <v-text-field
                    v-model.number="formCriarSL.vl_pago"
                    label="Valor Pago (R$)"
                    variant="outlined"
                    density="comfortable"
                    type="number"
                    step="0.01"
                    hide-details
                    prepend-inner-icon="mdi-currency-brl"
                  />
                </v-col>
              </v-row>
            </div>

          </div>
        </v-card-text>

        <v-divider />

        <!-- Erro + Ações -->
        <div class="pa-4">
          <v-alert v-if="erroCriarSL" type="error" density="compact" variant="tonal" class="mb-3" :text="erroCriarSL" />
          <div class="d-flex justify-end gap-2">
            <v-btn variant="text" color="grey" @click="dialogCriarSL = false">Cancelar</v-btn>
            <v-btn color="primary" :loading="salvandoCriarSL" @click="salvarNoSuperlogica" min-width="180">
              <v-icon start size="16">mdi-cloud-upload-outline</v-icon>
              Criar no Superlógica
            </v-btn>
          </div>
        </div>

      </v-card>
    </v-dialog>

    <!-- ── Snackbar sucesso Superlógica ── -->
    <v-snackbar
      v-model="snackSL"
      color="success"
      timeout="4000"
      location="top right"
      rounded="lg"
      elevation="8"
      min-width="320"
      transition="slide-x-reverse-transition"
      theme="dark"
    >
      <div class="d-flex align-center gap-3">
        <v-icon size="22">mdi-check-circle-outline</v-icon>
        <span style="font-size:0.9rem; font-weight:500;">Despesa criada com sucesso no Superlógica!</span>
      </div>
      <template #actions>
        <v-btn variant="text" size="small" @click="snackSL = false">Fechar</v-btn>
      </template>
    </v-snackbar>

    <!-- ── Snackbar ações fila ── -->
    <v-snackbar
      v-model="snackFila.show"
      :color="snackFila.color"
      timeout="4000"
      location="top right"
      rounded="lg"
      elevation="8"
      min-width="320"
      transition="slide-x-reverse-transition"
      theme="dark"
    >
      <div class="d-flex align-center gap-3">
        <v-icon size="22">{{ snackFila.icon }}</v-icon>
        <span style="font-size:0.9rem; font-weight:500;">{{ snackFila.msg }}</span>
      </div>
      <template #actions>
        <v-btn variant="text" size="small" @click="snackFila.show = false">Fechar</v-btn>
      </template>
    </v-snackbar>

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
const menuDtInicio = ref(false)
const menuDtFim    = ref(false)

const brParaDate = (br) => {
  if (!br) return null
  const [d, m, y] = br.split('/')
  return new Date(Number(y), Number(m) - 1, Number(d))
}
const isoParaBR = (val) => {
  if (!val) return ''
  const d = val instanceof Date ? val : new Date(val + 'T00:00:00')
  return `${String(d.getDate()).padStart(2,'0')}/${String(d.getMonth()+1).padStart(2,'0')}/${d.getFullYear()}`
}
const dtInicioISO = computed(() => brParaDate(dtInicio.value))
const dtFimISO    = computed(() => brParaDate(dtFim.value))

// ── Filtros salvos ────────────────────────────────────────────────────────────
const FILTROS_KEY = 'financeiro_filtros_salvos'
const filtrosSalvos    = ref(JSON.parse(localStorage.getItem(FILTROS_KEY) || '[]'))
const filtroAtivoNome  = ref(null)
const dialogSalvarFiltro = ref(false)
const novoFiltroNome   = ref('')
const erroSalvarFiltro = ref('')

const persistirFiltros = () => {
  localStorage.setItem(FILTROS_KEY, JSON.stringify(filtrosSalvos.value))
}

const aplicarFiltroSalvo = (f) => {
  condominioSelecionado.value = [...f.ids]
  filtroAtivoNome.value = f.nome
}

const confirmarSalvarFiltro = () => {
  const nome = novoFiltroNome.value.trim()
  if (!nome) return
  if (filtrosSalvos.value.some(f => f.nome === nome)) {
    erroSalvarFiltro.value = 'Já existe um filtro com esse nome.'
    return
  }
  filtrosSalvos.value.push({ nome, ids: [...condominioSelecionado.value] })
  persistirFiltros()
  filtroAtivoNome.value = nome
  dialogSalvarFiltro.value = false
  novoFiltroNome.value = ''
  erroSalvarFiltro.value = ''
}

const excluirFiltroSalvo = (nome) => {
  filtrosSalvos.value = filtrosSalvos.value.filter(f => f.nome !== nome)
  persistirFiltros()
  if (filtroAtivoNome.value === nome) filtroAtivoNome.value = null
}

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
const dialogModoCategoria = ref(false)
const dialogCategoria = ref('')
const dialogFornecedor = ref('')
const dialogConfig = ref({ titulo: '', cor: 'primary', icone: 'mdi-cash-multiple' })
const selecionadasParaPagar = ref([])
const marcandoPagamento = ref(false)

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
  let lista = dialogModoCategoria.value
    ? dialogFornecedor.value
      ? dados.value.despesas.filter(d => d.fornecedor === dialogFornecedor.value)
      : dados.value.despesas.filter(d => d.categoria === dialogCategoria.value)
    : dialogFiltro.value === 'todas'
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
  dialogModoCategoria.value = false
  dialogCategoria.value = ''
  dialogFornecedor.value = ''
  dialogConfig.value = configPorFiltro[filtro]
  selecionadasParaPagar.value = []
  dialogKpi.value = true
}

const abrirDialogCategoria = (categoria) => {
  dialogFiltro.value = 'todas'
  dialogModoCategoria.value = true
  dialogCategoria.value = categoria
  dialogFornecedor.value = ''
  dialogConfig.value = { titulo: `Categoria: ${categoria}`, cor: 'indigo', icone: 'mdi-tag-multiple-outline' }
  const despesasCategoria = (dados.value?.despesas || []).filter(d => d.categoria === categoria)
  selecionadasParaPagar.value = [...despesasCategoria]
  dialogKpi.value = true
}

const abrirDialogFornecedor = (fornecedor) => {
  dialogFiltro.value = 'todas'
  dialogModoCategoria.value = true
  dialogCategoria.value = ''
  dialogFornecedor.value = fornecedor
  dialogConfig.value = { titulo: `Fornecedor: ${fornecedor || 'Sem fornecedor'}`, cor: 'teal', icone: 'mdi-store-outline' }
  const despesasForn = (dados.value?.despesas || []).filter(d => d.fornecedor === fornecedor)
  selecionadasParaPagar.value = [...despesasForn]
  dialogKpi.value = true
}

const condominioNome = computed(() => {
  const id = condominioSelecionado.value[0]
  return condominios.value.find(c => c.id === id)?.nome || ''
})

const marcarParaPagamento = async () => {
  if (!selecionadasParaPagar.value.length) return
  marcandoPagamento.value = true
  try {
    const condId   = Number(condominioSelecionado.value[0]) || 0
    const condNome = condominioNome.value
    const despesas = selecionadasParaPagar.value.map(d => ({
      id_despesa:      String(d.id        || ''),
      id_parcela:      String(d.id_parcela || ''),
      id_contato:      String(d.id_contato || ''),
      descricao:       String(d.descricao  || ''),
      fornecedor:      String(d.fornecedor || ''),
      condominio_id:   condId,
      condominio_nome: condNome,
      valor:           Number(d.valor) || 0,
      vencimento:      String(d.vencimento || ''),
    }))
    const res = await fetch('/api/financeiro/fila-pagamento', {
      method: 'POST',
      headers: authHeader(),
      body: JSON.stringify({ despesas }),
    })
    const text = await res.text()
    let data
    try { data = JSON.parse(text) } catch { throw new Error(text.substring(0, 300)) }
    if (!res.ok) throw new Error(data.detail || JSON.stringify(data))
    selecionadasParaPagar.value = []
    dialogKpi.value = false
    await fetchFilaPagamento()
  } catch (e) {
    alert('Erro: ' + e.message)
  } finally {
    marcandoPagamento.value = false
  }
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

const categoriasDinamicas = computed(() => {
  if (!dados.value?.despesas) return []
  let lista = dados.value.despesas
  if (comStatus.value === 'pendentes') lista = lista.filter(d => d.status === 'pendente')
  else if (comStatus.value === 'liquidadas') lista = lista.filter(d => d.status === 'liquidada')
  const mapa = {}
  for (const d of lista) {
    const cat = d.categoria || 'Sem categoria'
    if (!mapa[cat]) mapa[cat] = { categoria: cat, total: 0, quantidade: 0 }
    mapa[cat].total += Number(d.valor) || 0
    mapa[cat].quantidade++
  }
  return Object.values(mapa).sort((a, b) => b.total - a.total)
})

const totalGeralDinamico = computed(() =>
  categoriasDinamicas.value.reduce((s, c) => s + c.total, 0)
)

const IDS_LOJAS = new Set([84, 67, 78, 60, 58, 79, 82, 75, 73, 70, 74, 71, 72, 76, 77, 66, 69, 68, 83, 80])

const fetchCondominios = async () => {
  loadingCondominios.value = true
  try {
    const res = await fetch('/api/admin/condominios', { headers: authHeader() })
    if (res.ok) {
      const lista = await res.json()
      condominios.value = lista.filter(c => IDS_LOJAS.has(Number(c.id)))
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
const snackSL          = ref(false)

const formCriarSLVazio = () => ({
  id_condominio:  null,
  descricao:      '',
  nome_contato:   '',
  id_contato:     '',
  id_conta:       '',
  vl_valor:       0,
  qt_parcelas:    1,
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
  if (!formCriarSL.value.id_condominio || !formCriarSL.value.descricao || !formCriarSL.value.nome_contato || !formCriarSL.value.id_contato || formCriarSL.value.vl_valor <= 0) {
    erroCriarSL.value = 'Preencha todos os campos obrigatórios (incluindo ID do Fornecedor).'
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
    snackSL.value = true
    await buscar()
  } catch (e) {
    erroCriarSL.value = e.message
  } finally {
    salvandoCriarSL.value = false
  }
}

// ── Fila de Pagamentos ────────────────────────────────────────────────────────
const filaPagamento    = ref([])
const loadingFila      = ref(false)
const filaFiltroStatus = ref('aguardando')
const snackFila        = ref({ show: false, msg: '', color: 'success', icon: 'mdi-check-circle-outline' })

const mostrarSnackFila = (msg, color = 'success', icon = 'mdi-check-circle-outline') => {
  snackFila.value = { show: true, msg, color, icon }
}

const fetchFilaPagamento = async () => {
  loadingFila.value = true
  try {
    const res = await fetch(
      `/api/financeiro/fila-pagamento?status=${filaFiltroStatus.value}`,
      { headers: authHeader() }
    )
    if (res.ok) filaPagamento.value = await res.json()
  } catch (_) {}
  loadingFila.value = false
}

const atualizarStatusFila = async (id, status) => {
  const item = filaPagamento.value.find(i => i.id === id)
  const fornecedor = item?.fornecedor || item?.descricao || 'Despesa'
  try {
    await fetch(`/api/financeiro/fila-pagamento/${id}`, {
      method: 'PUT',
      headers: authHeader(),
      body: JSON.stringify({ status }),
    })
    await fetchFilaPagamento()
    if (status === 'pago') {
      mostrarSnackFila(`"${fornecedor}" marcada como paga.`, 'success', 'mdi-check-circle-outline')
    } else if (status === 'cancelado') {
      mostrarSnackFila(`"${fornecedor}" foi cancelada.`, 'error', 'mdi-close-circle-outline')
    }
  } catch (_) {
    mostrarSnackFila('Erro ao atualizar status.', 'error', 'mdi-alert-circle-outline')
  }
}

const removerDaFila = async (id) => {
  const item = filaPagamento.value.find(i => i.id === id)
  const fornecedor = item?.fornecedor || item?.descricao || 'Despesa'
  if (!confirm(`Remover "${fornecedor}" da fila de pagamento?`)) return
  try {
    await fetch(`/api/financeiro/fila-pagamento/${id}`, {
      method: 'DELETE',
      headers: authHeader(),
    })
    await fetchFilaPagamento()
    mostrarSnackFila(`"${fornecedor}" removida da fila.`, 'info', 'mdi-delete-outline')
  } catch (_) {
    mostrarSnackFila('Erro ao remover da fila.', 'error', 'mdi-alert-circle-outline')
  }
}

onMounted(() => {
  fetchCondominios()
  fetchFilaPagamento()
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

/* dialog-header usado nos dialogs desta view */
.dialog-header {
  padding: 16px 20px;
  border-left: 3px solid #34d399;
}

/* ── Form Nova Despesa Superlógica ── */
.sl-form-body {
  max-height: 70vh;
  overflow-y: auto;
}
.sl-section {
  padding: 18px 24px;
}
.sl-section--liquidar {
  background: rgba(var(--v-theme-primary), 0.03);
}
.sl-section-label {
  font-size: 0.7rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  opacity: 0.45;
  margin: 0 0 12px;
  display: flex;
  align-items: center;
}
</style>
