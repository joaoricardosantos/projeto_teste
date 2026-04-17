<template>
  <v-container fluid class="pa-6">

    <!-- ── Cabeçalho ── -->
    <div class="d-flex align-center justify-space-between flex-wrap gap-3 mb-5">
      <div>
        <h2 class="text-h5 font-weight-bold">Planilhas dos Funcionários</h2>
        <p class="text-body-2 text-medium-emphasis mt-1">
          Acompanhe o progresso das tarefas com indicadores visuais de prazo.
        </p>
      </div>
      <v-btn v-if="isAdmin" color="primary" variant="tonal" prepend-icon="mdi-cog-outline"
        @click="dialogGerenciar = true">
        Gerenciar Planilhas
      </v-btn>
    </div>

    <!-- ── Seletor de funcionário (admin) ── -->
    <v-row v-if="isAdmin" class="mb-1">
      <v-col cols="12" md="4">
        <v-select
          v-model="configSelecionadaId"
          :items="configs"
          item-title="funcionario_nome"
          item-value="id"
          label="Funcionário"
          variant="outlined"
          density="comfortable"
          prepend-inner-icon="mdi-account-outline"
          clearable
          @update:model-value="onConfigChange"
        />
      </v-col>
    </v-row>

    <v-alert v-if="!carregando && !configAtual && !isAdmin" type="info" variant="tonal" class="mb-4">
      Você ainda não possui uma planilha configurada. Contate o administrador.
    </v-alert>
    <v-alert v-if="!carregando && isAdmin && configs.length === 0" type="info" variant="tonal" class="mb-4">
      Nenhuma planilha configurada. Clique em "Gerenciar Planilhas" para criar.
    </v-alert>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- Dashboard                                                            -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <template v-if="configAtual">

      <!-- Seletor de aba -->
      <div class="d-flex align-center flex-wrap gap-3 mb-6">
        <v-select
          v-model="abaSelecionada"
          :items="abas"
          item-title="title"
          item-value="title"
          label="Aba / Período"
          variant="outlined"
          density="comfortable"
          hide-details
          style="max-width:280px"
          prepend-inner-icon="mdi-table-large"
          :loading="carregandoAbas"
          @update:model-value="carregarDashboard"
        />
        <v-btn icon variant="tonal" size="small" :loading="carregandoDados"
          @click="carregarDashboard" title="Atualizar">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
        <span v-if="dashboard?.atualizado_em" class="text-caption text-medium-emphasis">
          Atualizado: {{ dashboard.atualizado_em }}
        </span>
      </div>

      <div v-if="carregandoDados" class="d-flex justify-center py-16">
        <v-progress-circular indeterminate color="primary" size="48" />
      </div>

      <template v-if="dash && !carregandoDados">

        <!-- ── Row 1: Stats rápidos ── -->
        <v-row class="mb-2" dense>
          <v-col cols="6" sm="3">
            <div class="stat-chip">
              <v-icon size="18" color="primary" class="mb-1">mdi-office-building-outline</v-icon>
              <div class="stat-valor">{{ dash.resumo.total_condominios }}</div>
              <div class="stat-label">Condomínios</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-chip" :class="dash.resumo.prestacao_pct < 100 ? 'stat-warn' : 'stat-ok'">
              <v-icon size="18" :color="dash.resumo.prestacao_pct < 100 ? 'warning' : 'success'" class="mb-1">
                mdi-file-check-outline
              </v-icon>
              <div class="stat-valor">{{ dash.resumo.prestacao_pct }}%</div>
              <div class="stat-label">Prestações OK</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-chip" :class="dash.resumo.recebimentos_pct < 100 ? 'stat-warn' : 'stat-ok'">
              <v-icon size="18" :color="dash.resumo.recebimentos_pct < 100 ? 'warning' : 'success'" class="mb-1">
                mdi-inbox-arrow-down-outline
              </v-icon>
              <div class="stat-valor">{{ dash.resumo.recebimentos_pct }}%</div>
              <div class="stat-label">Recebimentos OK</div>
            </div>
          </v-col>
          <v-col cols="6" sm="3">
            <div class="stat-chip" :class="dash.resumo.boletos_pct < 100 ? 'stat-warn' : 'stat-ok'">
              <v-icon size="18" :color="dash.resumo.boletos_pct < 100 ? 'warning' : 'success'" class="mb-1">
                mdi-barcode
              </v-icon>
              <div class="stat-valor">{{ dash.resumo.boletos_pct }}%</div>
              <div class="stat-label">Boletos no Prazo</div>
            </div>
          </v-col>
        </v-row>

        <!-- ── Row 2: KPI cards clicáveis ── -->
        <v-row class="mb-2" dense>

          <!-- Prestação de Contas -->
          <v-col cols="12" md="4">
            <v-card class="kpi-card h-100"
              :class="dash.kpis.prestacao.pendentes > 0 ? 'kpi-error' : 'kpi-ok'"
              rounded="lg" @click="abrirModalKpi('prestacao')" style="cursor:pointer">
              <v-card-text class="pa-5">
                <div class="d-flex align-center justify-space-between mb-4">
                  <div class="kpi-icon-wrap"
                    :class="dash.kpis.prestacao.pendentes > 0 ? 'icon-error' : 'icon-ok'">
                    <v-icon size="24">mdi-file-check-outline</v-icon>
                  </div>
                  <v-chip size="small" variant="tonal"
                    :color="dash.kpis.prestacao.pendentes > 0 ? 'error' : 'success'">
                    {{ dash.kpis.prestacao.pendentes > 0
                        ? dash.kpis.prestacao.pendentes + ' atrasada' + (dash.kpis.prestacao.pendentes !== 1 ? 's' : '')
                        : 'Em dia' }}
                  </v-chip>
                </div>
                <div class="text-subtitle-1 font-weight-semibold mb-1">Prestação de Contas</div>
                <div class="text-caption text-medium-emphasis mb-3">
                  {{ dash.kpis.prestacao.total - dash.kpis.prestacao.pendentes }}
                  de {{ dash.kpis.prestacao.total }} concluídas
                </div>
                <v-progress-linear
                  :model-value="prestacaoPct"
                  :color="dash.kpis.prestacao.pendentes > 0 ? 'error' : 'success'"
                  bg-color="rgba(128,128,128,0.15)"
                  rounded height="6"
                />
                <div class="text-caption text-medium-emphasis mt-2">
                  {{ prestacaoPct }}% · Clique para ver detalhes
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Recebimentos -->
          <v-col cols="12" md="4">
            <v-card class="kpi-card h-100"
              :class="dash.kpis.recebimentos.total_pendentes > 0 ? 'kpi-error' : 'kpi-ok'"
              rounded="lg" @click="abrirModalKpi('recebimentos')" style="cursor:pointer">
              <v-card-text class="pa-5">
                <div class="d-flex align-center justify-space-between mb-4">
                  <div class="kpi-icon-wrap"
                    :class="dash.kpis.recebimentos.total_pendentes > 0 ? 'icon-error' : 'icon-ok'">
                    <v-icon size="24">mdi-inbox-arrow-down-outline</v-icon>
                  </div>
                  <v-chip size="small" variant="tonal"
                    :color="dash.kpis.recebimentos.total_pendentes > 0 ? 'error' : 'success'">
                    {{ dash.kpis.recebimentos.total_pendentes > 0
                        ? dash.kpis.recebimentos.total_pendentes + ' pendente' + (dash.kpis.recebimentos.total_pendentes !== 1 ? 's' : '')
                        : 'Em dia' }}
                  </v-chip>
                </div>
                <div class="text-subtitle-1 font-weight-semibold mb-3">Recebimentos de Relatórios</div>
                <div class="d-flex flex-column gap-2">
                  <div v-for="(g, k) in recebGrupos" :key="k" class="receb-row">
                    <span class="text-caption text-medium-emphasis" style="width:68px;flex-shrink:0">{{ g }}</span>
                    <v-progress-linear
                      :model-value="recebPct(k)"
                      :color="dash.kpis.recebimentos[k].pendentes > 0 ? 'error' : 'success'"
                      bg-color="rgba(128,128,128,0.15)"
                      rounded height="5"
                      class="flex-grow-1"
                    />
                    <span class="text-caption font-weight-medium" style="width:36px;text-align:right;flex-shrink:0">
                      {{ recebPct(k) }}%
                    </span>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Boletos -->
          <v-col cols="12" md="4">
            <v-card class="kpi-card h-100"
              :class="dash.kpis.boletos.atrasados > 0 ? 'kpi-error' : 'kpi-ok'"
              rounded="lg" @click="abrirModalKpi('boletos')" style="cursor:pointer">
              <v-card-text class="pa-5">
                <div class="d-flex align-center justify-space-between mb-4">
                  <div class="kpi-icon-wrap"
                    :class="dash.kpis.boletos.atrasados > 0 ? 'icon-error' : 'icon-ok'">
                    <v-icon size="24">mdi-barcode</v-icon>
                  </div>
                  <v-chip size="small" variant="tonal"
                    :color="dash.kpis.boletos.atrasados > 0 ? 'error' : 'success'">
                    {{ dash.kpis.boletos.atrasados > 0
                        ? dash.kpis.boletos.atrasados + ' atrasado' + (dash.kpis.boletos.atrasados !== 1 ? 's' : '')
                        : 'Em dia' }}
                  </v-chip>
                </div>
                <div class="text-subtitle-1 font-weight-semibold mb-1">Geração de Boletos</div>
                <div class="text-caption text-medium-emphasis mb-3">
                  {{ dash.kpis.boletos.no_prazo }} no prazo ·
                  {{ dash.kpis.boletos.atrasados }} atrasados
                </div>
                <v-progress-linear
                  :model-value="boletosPct"
                  :color="dash.kpis.boletos.atrasados > 0 ? 'error' : 'success'"
                  bg-color="rgba(128,128,128,0.15)"
                  rounded height="6"
                />
                <div class="text-caption text-medium-emphasis mt-2">
                  {{ boletosPct }}% · Clique para ver detalhes
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- ── Row 3: Pipeline de boletos ── -->
        <v-row class="mb-4" dense>
          <v-col cols="12">
            <v-card rounded="lg">
              <v-card-text class="pa-5">
                <div class="text-subtitle-2 font-weight-semibold mb-4">
                  <v-icon size="16" class="mr-1">mdi-timeline-check-outline</v-icon>
                  Pipeline de Boletos
                </div>
                <div class="pipeline-wrapper">
                  <div
                    v-for="(passo, idx) in dash.pipeline"
                    :key="passo.label"
                    class="pipeline-passo"
                  >
                    <div class="pipeline-seta" v-if="idx > 0">
                      <v-icon size="20" color="rgba(128,128,128,0.4)">mdi-chevron-right</v-icon>
                    </div>
                    <div class="pipeline-item"
                      :class="passo.pct === 100 ? 'pipe-ok' : passo.pct >= 50 ? 'pipe-warn' : 'pipe-error'">
                      <div class="pipe-pct">{{ passo.pct }}%</div>
                      <v-progress-circular
                        :model-value="passo.pct"
                        :color="passo.pct === 100 ? 'success' : passo.pct >= 50 ? 'warning' : 'error'"
                        bg-color="rgba(128,128,128,0.12)"
                        size="52"
                        width="5"
                      >
                        <span class="text-caption font-weight-bold">{{ passo.concluidos }}</span>
                      </v-progress-circular>
                      <div class="pipe-label">{{ passo.label }}</div>
                      <div class="pipe-sub">{{ passo.concluidos }}/{{ passo.total }}</div>
                    </div>
                  </div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- ── Legenda ── -->
        <div class="legenda-row mb-4">
          <div v-for="l in legenda" :key="l.label" class="legenda-item">
            <div class="legenda-dot" :style="`background:${l.cor}`"></div>
            <span class="text-caption text-medium-emphasis">{{ l.label }}</span>
          </div>
        </div>

        <!-- ── Tabela ── -->
        <div class="planilha-wrapper">
          <div class="planilha-scroll">
            <table class="planilha-table">
              <thead>
                <tr>
                  <th class="sticky-col th-label">Condomínio</th>
                  <th class="th-date">Prazo<br>Prestação</th>
                  <th class="th-status">OK<br>Prestação</th>
                  <th class="th-status">Água</th>
                  <th class="th-status">Gás</th>
                  <th class="th-status">Reservas</th>
                  <th class="th-date">Prazo<br>Boleto</th>
                  <th class="th-status">Geração</th>
                  <th class="th-status">E-mail</th>
                  <th class="th-status">Impresso</th>
                  <th class="th-status">Gráfica</th>
                  <th class="th-status">Retorno</th>
                </tr>
              </thead>
              <tbody>
                <tr v-if="dash.linhas.length === 0">
                  <td colspan="12" class="text-center text-medium-emphasis py-8">
                    Nenhuma linha encontrada nesta aba.
                  </td>
                </tr>
                <tr v-for="(l, i) in dash.linhas" :key="i" class="planilha-row">
                  <td class="sticky-col td-label">{{ l.condominio }}</td>
                  <td class="td-date">{{ l.prazo_prestacao || '—' }}</td>
                  <td :class="['td-status', `st-${l.ok_prestacao.status}`]">
                    <div class="celula-inner">{{ celulaDisplay(l.ok_prestacao) }}</div>
                  </td>
                  <td :class="['td-status', `st-${l.recebimento_agua.status}`]">
                    <div class="celula-inner">{{ celulaDisplay(l.recebimento_agua) }}</div>
                  </td>
                  <td :class="['td-status', `st-${l.recebimento_gas.status}`]">
                    <div class="celula-inner">{{ celulaDisplay(l.recebimento_gas) }}</div>
                  </td>
                  <td :class="['td-status', `st-${l.recebimento_reservas.status}`]">
                    <div class="celula-inner">{{ celulaDisplay(l.recebimento_reservas) }}</div>
                  </td>
                  <td class="td-date">{{ l.prazo_boleto || '—' }}</td>
                  <td :class="['td-status', `st-${l.geracao_boleto.status}`]">
                    <div class="celula-inner">{{ celulaDisplay(l.geracao_boleto) }}</div>
                  </td>
                  <td :class="['td-status', `st-${l.enviado_email.status}`]">
                    <div class="celula-inner">{{ celulaDisplay(l.enviado_email) }}</div>
                  </td>
                  <td :class="['td-status', `st-${l.impresso_pratika.status}`]">
                    <div class="celula-inner">{{ celulaDisplay(l.impresso_pratika) }}</div>
                  </td>
                  <td :class="['td-status', `st-${l.enviado_grafica.status}`]">
                    <div class="celula-inner">{{ celulaDisplay(l.enviado_grafica) }}</div>
                  </td>
                  <td :class="['td-status', `st-${l.retorno_grafica.status}`]">
                    <div class="celula-inner">{{ celulaDisplay(l.retorno_grafica) }}</div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

      </template>
    </template>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- Modal KPI detalhe                                                    -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <v-dialog v-model="modalKpi.show" max-width="480">
      <v-card rounded="lg">
        <v-card-title class="pa-4 pb-2 d-flex align-center justify-space-between">
          <span class="text-subtitle-1 font-weight-medium">{{ modalKpi.titulo }}</span>
          <v-btn icon variant="text" size="small" @click="modalKpi.show = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4" style="max-height:60vh;overflow-y:auto">

          <template v-if="modalKpi.tipo === 'prestacao'">
            <v-alert v-if="dash?.kpis.prestacao.pendentes === 0" type="success" variant="tonal" density="compact">
              Todas as prestações estão em dia!
            </v-alert>
            <v-list v-else lines="one" density="compact">
              <v-list-item v-for="nome in dash?.kpis.prestacao.lista" :key="nome"
                prepend-icon="mdi-alert-circle-outline" color="error">
                <template #title><span class="text-body-2">{{ nome }}</span></template>
              </v-list-item>
            </v-list>
          </template>

          <template v-else-if="modalKpi.tipo === 'recebimentos'">
            <v-alert v-if="dash?.kpis.recebimentos.total_pendentes === 0"
              type="success" variant="tonal" density="compact">
              Todos os relatórios foram recebidos!
            </v-alert>
            <template v-else>
              <template v-for="(gLabel, gKey) in recebGrupos" :key="gKey">
                <div v-if="dash?.kpis.recebimentos[gKey].pendentes > 0" class="mb-4">
                  <div class="text-subtitle-2 mb-2 d-flex align-center gap-2">
                    <v-icon size="14" color="error">mdi-circle</v-icon>
                    {{ gLabel }} —
                    <span class="text-error text-caption">
                      {{ dash?.kpis.recebimentos[gKey].pendentes }} pendente{{ dash?.kpis.recebimentos[gKey].pendentes !== 1 ? 's' : '' }}
                    </span>
                  </div>
                  <v-list lines="one" density="compact" class="rounded border">
                    <template v-for="(nome, ni) in dash?.kpis.recebimentos[gKey].lista" :key="ni">
                      <v-divider v-if="ni > 0" />
                      <v-list-item prepend-icon="mdi-home-outline">
                        <template #title><span class="text-body-2">{{ nome }}</span></template>
                      </v-list-item>
                    </template>
                  </v-list>
                </div>
              </template>
            </template>
          </template>

          <template v-else-if="modalKpi.tipo === 'boletos'">
            <div class="d-flex gap-3 mb-4">
              <v-chip color="success" variant="tonal">
                <v-icon start size="14">mdi-check</v-icon>
                {{ dash?.kpis.boletos.no_prazo }} no prazo
              </v-chip>
              <v-chip color="error" variant="tonal">
                <v-icon start size="14">mdi-close</v-icon>
                {{ dash?.kpis.boletos.atrasados }} atrasados
              </v-chip>
            </div>
            <v-alert v-if="dash?.kpis.boletos.atrasados === 0"
              type="success" variant="tonal" density="compact">
              Todos os boletos foram gerados no prazo!
            </v-alert>
            <v-list v-else lines="one" density="compact" class="rounded border">
              <template v-for="(nome, ni) in dash?.kpis.boletos.lista_atrasados" :key="ni">
                <v-divider v-if="ni > 0" />
                <v-list-item prepend-icon="mdi-alert-circle-outline" color="error">
                  <template #title><span class="text-body-2">{{ nome }}</span></template>
                </v-list-item>
              </template>
            </v-list>
          </template>

        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- Dialog Gerenciar (admin)                                             -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <v-dialog v-model="dialogGerenciar" max-width="600" scrollable>
      <v-card rounded="lg">
        <v-card-title class="pa-4 pb-2 d-flex align-center justify-space-between">
          <span class="text-subtitle-1 font-weight-medium">Gerenciar Planilhas</span>
          <v-btn icon variant="text" size="small" @click="dialogGerenciar = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4" style="max-height:75vh">

          <div class="d-flex align-center justify-space-between mb-3">
            <span class="text-subtitle-2">Planilhas vinculadas</span>
            <v-btn size="small" color="primary" variant="tonal" prepend-icon="mdi-plus"
              @click="abrirFormConfig()">
              Nova
            </v-btn>
          </div>

          <v-list v-if="configs.length" lines="two" class="rounded border mb-4">
            <template v-for="(cfg, idx) in configs" :key="cfg.id">
              <v-divider v-if="idx > 0" />
              <v-list-item>
                <template #title>{{ cfg.funcionario_nome }} — {{ cfg.nome }}</template>
                <template #subtitle>
                  <span v-if="cfg.spreadsheet_id" class="text-caption">
                    {{ cfg.spreadsheet_id.substring(0, 32) }}…
                  </span>
                  <span v-else class="text-caption text-error">Sem planilha vinculada</span>
                </template>
                <template #append>
                  <v-btn icon size="x-small" variant="text" @click="abrirFormConfig(cfg)">
                    <v-icon size="16">mdi-pencil-outline</v-icon>
                  </v-btn>
                  <v-btn icon size="x-small" variant="text" color="error"
                    @click="confirmarExclusao('Excluir planilha de ' + cfg.funcionario_nome + '?', () => deletarConfig(cfg))">
                    <v-icon size="16">mdi-delete-outline</v-icon>
                  </v-btn>
                </template>
              </v-list-item>
            </template>
          </v-list>
          <v-alert v-else type="info" variant="tonal" density="compact" class="mb-4">
            Nenhuma planilha configurada.
          </v-alert>

          <v-expand-transition>
            <div v-if="formConfig.aberto">
              <v-divider class="mb-4" />
              <div class="text-subtitle-2 mb-3">{{ formConfig.id ? 'Editar' : 'Nova planilha' }}</div>
              <v-row dense>
                <v-col cols="12" md="6">
                  <v-select v-model="formConfig.funcionario_id" :items="usuarios"
                    item-title="nome" item-value="id" label="Funcionário"
                    variant="outlined" density="comfortable" :disabled="!!formConfig.id" />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field v-model="formConfig.nome" label="Nome"
                    variant="outlined" density="comfortable" />
                </v-col>
                <v-col cols="12">
                  <v-text-field v-model="formConfig.spreadsheet_id"
                    label="ID do Google Sheets" variant="outlined" density="comfortable"
                    hint="Cole o ID da URL da planilha (trecho entre /d/ e /edit)"
                    persistent-hint />
                </v-col>
              </v-row>
              <div class="d-flex gap-2 justify-end mt-3">
                <v-btn variant="text" @click="formConfig.aberto = false">Cancelar</v-btn>
                <v-btn color="primary" variant="tonal" @click="salvarConfig" :loading="salvando"
                  :disabled="!formConfig.funcionario_id || !formConfig.nome">
                  {{ formConfig.id ? 'Atualizar' : 'Criar' }}
                </v-btn>
              </div>
            </div>
          </v-expand-transition>

        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- Confirm -->
    <v-dialog v-model="confirmDlg.show" max-width="340">
      <v-card rounded="lg">
        <v-card-text class="pa-5">{{ confirmDlg.msg }}</v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="confirmDlg.show = false">Cancelar</v-btn>
          <v-btn color="error" variant="tonal" @click="confirmDlg.action" :loading="salvando">
            Excluir
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snack.show" :color="snack.color" :timeout="3000" location="bottom right">
      {{ snack.msg }}
    </v-snackbar>

  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const API = '/api'
const token = () => localStorage.getItem('access_token')
const isAdmin = computed(() => localStorage.getItem('is_admin') === 'true')

const carregando      = ref(false)
const carregandoAbas  = ref(false)
const carregandoDados = ref(false)
const salvando        = ref(false)

const configs             = ref([])
const usuarios            = ref([])
const configSelecionadaId = ref(null)
const configAtual         = ref(null)
const abas                = ref([])
const abaSelecionada      = ref(null)
const dashboard           = ref(null)

const _kpiItemVazio = () => ({ total: 0, pendentes: 0, lista: [] })
const _kpisVazios = () => ({
  prestacao: _kpiItemVazio(),
  recebimentos: { agua: _kpiItemVazio(), gas: _kpiItemVazio(), reservas: _kpiItemVazio(), total_pendentes: 0 },
  boletos: { no_prazo: 0, atrasados: 0, lista_atrasados: [] },
})

function _pct(ok, total) { return total ? Math.round(ok / total * 100) : 0 }
function _preenchido(v) {
  return !!(v && v.trim() && !['0', 'none', '-', '—'].includes(v.trim().toLowerCase()))
}

const dash = computed(() => {
  const d = dashboard.value
  if (!d) return null

  const kpis = d.kpis ?? _kpisVazios()
  const linhas = d.linhas ?? []

  const resumo = d.resumo ?? {
    total_condominios: linhas.length,
    prestacao_pct: _pct(
      kpis.prestacao.total - kpis.prestacao.pendentes,
      kpis.prestacao.total
    ),
    recebimentos_pct: _pct(
      (kpis.recebimentos.agua.total - kpis.recebimentos.agua.pendentes) +
      (kpis.recebimentos.gas.total - kpis.recebimentos.gas.pendentes) +
      (kpis.recebimentos.reservas.total - kpis.recebimentos.reservas.pendentes),
      kpis.recebimentos.agua.total + kpis.recebimentos.gas.total + kpis.recebimentos.reservas.total
    ),
    boletos_pct: _pct(kpis.boletos.no_prazo, kpis.boletos.no_prazo + kpis.boletos.atrasados),
  }

  const _passoLabels = [
    { label: 'Geração',  campo: 'geracao_boleto' },
    { label: 'E-mail',   campo: 'enviado_email' },
    { label: 'Impresso', campo: 'impresso_pratika' },
    { label: 'Gráfica',  campo: 'enviado_grafica' },
    { label: 'Retorno',  campo: 'retorno_grafica' },
  ]
  const pipeline = (d.pipeline && d.pipeline.length)
    ? d.pipeline
    : _passoLabels.map(({ label, campo }) => {
        const concluidos = linhas.filter(l => _preenchido(l[campo]?.valor || '')).length
        const total = linhas.length
        return { label, concluidos, total, pct: total ? Math.round(concluidos / total * 1000) / 10 : 0 }
      })

  return { ...d, resumo, pipeline, kpis, linhas }
})

const dialogGerenciar = ref(false)
const formConfig = ref({ aberto: false, id: null, funcionario_id: null, nome: '', spreadsheet_id: '' })
const modalKpi   = ref({ show: false, tipo: '', titulo: '' })
const snack      = ref({ show: false, color: 'success', msg: '' })
const confirmDlg = ref({ show: false, msg: '', action: null })

const recebGrupos = { agua: 'Água', gas: 'Gás', reservas: 'Reservas' }

const legenda = [
  { label: 'Concluído no prazo', cor: '#4caf50' },
  { label: 'Atrasado',           cor: '#f44336' },
  { label: 'Vence em breve',     cor: '#ff9800' },
  { label: 'Pendente',           cor: 'rgba(128,128,128,0.18)' },
  { label: 'Sem prazo definido', cor: 'transparent', borda: true },
]

// ── Computeds ─────────────────────────────────────────────────────────────────
const prestacaoPct = computed(() => {
  if (!dash.value) return 0
  const { total, pendentes } = dash.value.kpis.prestacao
  if (!total) return 0
  return Math.round((total - pendentes) / total * 100)
})

const boletosPct = computed(() => {
  if (!dash.value) return 0
  const { no_prazo, atrasados } = dash.value.kpis.boletos
  const t = no_prazo + atrasados
  if (!t) return 0
  return Math.round(no_prazo / t * 100)
})

function recebPct(key) {
  if (!dash.value) return 0
  const { total, pendentes } = dash.value.kpis.recebimentos[key]
  if (!total) return 0
  return Math.round((total - pendentes) / total * 100)
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function mostrarSnack(msg, color = 'success') { snack.value = { show: true, color, msg } }

function confirmarExclusao(msg, action) {
  confirmDlg.value = {
    show: true, msg,
    action: async () => { await action(); confirmDlg.value.show = false },
  }
}

function celulaDisplay(c) { return c.valor || '—' }

async function apiFetch(url, opts = {}) {
  const res = await fetch(`${API}${url}`, {
    headers: { Authorization: `Bearer ${token()}`, 'Content-Type': 'application/json' },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Erro ${res.status}`)
  }
  return res.status === 204 ? null : res.json()
}

// ── Inicialização ─────────────────────────────────────────────────────────────
async function init() {
  carregando.value = true
  try {
    if (isAdmin.value) {
      const [cfgs, users] = await Promise.all([
        apiFetch('/planilhas/configs'),
        apiFetch('/planilhas/usuarios'),
      ])
      configs.value = cfgs
      usuarios.value = users
    } else {
      try {
        configAtual.value = await apiFetch('/planilhas/minha')
        await carregarAbas()
      } catch (e) {
        if (!e.message.includes('404') && !e.message.includes('Planilha_nao_configurada')) throw e
      }
    }
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    carregando.value = false
  }
}

async function onConfigChange(id) {
  configAtual.value = id ? configs.value.find(c => c.id === id) || null : null
  abas.value = []; abaSelecionada.value = null; dashboard.value = null
  if (configAtual.value) await carregarAbas()
}

async function carregarAbas() {
  if (!configAtual.value?.spreadsheet_id) return
  carregandoAbas.value = true
  try {
    abas.value = await apiFetch(`/planilhas/configs/${configAtual.value.id}/abas`)
    if (abas.value.length) {
      abaSelecionada.value = abas.value[0].title
      await carregarDashboard()
    }
  } catch (e) { mostrarSnack(e.message, 'error') }
  finally { carregandoAbas.value = false }
}

async function carregarDashboard() {
  if (!configAtual.value || !abaSelecionada.value) return
  carregandoDados.value = true; dashboard.value = null
  try {
    dashboard.value = await apiFetch(
      `/planilhas/configs/${configAtual.value.id}/dashboard?aba=${encodeURIComponent(abaSelecionada.value)}`
    )
  } catch (e) { mostrarSnack(e.message, 'error') }
  finally { carregandoDados.value = false }
}

// ── Modal KPI ─────────────────────────────────────────────────────────────────
function abrirModalKpi(tipo) {
  const t = { prestacao: 'Prestação de Contas', recebimentos: 'Recebimentos de Relatórios', boletos: 'Geração de Boletos' }
  modalKpi.value = { show: true, tipo, titulo: t[tipo] }
}

// ── Config CRUD ───────────────────────────────────────────────────────────────
function abrirFormConfig(cfg = null) {
  formConfig.value = cfg
    ? { aberto: true, id: cfg.id, funcionario_id: cfg.funcionario_id, nome: cfg.nome, spreadsheet_id: cfg.spreadsheet_id }
    : { aberto: true, id: null, funcionario_id: null, nome: '', spreadsheet_id: '' }
}

async function salvarConfig() {
  salvando.value = true
  try {
    const body = { funcionario_id: formConfig.value.funcionario_id, nome: formConfig.value.nome, spreadsheet_id: formConfig.value.spreadsheet_id }
    if (formConfig.value.id) {
      const u = await apiFetch(`/planilhas/configs/${formConfig.value.id}`, { method: 'PUT', body: JSON.stringify(body) })
      const i = configs.value.findIndex(c => c.id === u.id)
      if (i >= 0) configs.value[i] = u
    } else {
      configs.value.push(await apiFetch('/planilhas/configs', { method: 'POST', body: JSON.stringify(body) }))
    }
    formConfig.value.aberto = false
    mostrarSnack('Planilha salva')
  } catch (e) { mostrarSnack(e.message, 'error') }
  finally { salvando.value = false }
}

async function deletarConfig(cfg) {
  salvando.value = true
  try {
    await apiFetch(`/planilhas/configs/${cfg.id}`, { method: 'DELETE' })
    configs.value = configs.value.filter(c => c.id !== cfg.id)
    if (configSelecionadaId.value === cfg.id) {
      configSelecionadaId.value = null; configAtual.value = null; dashboard.value = null
    }
    mostrarSnack('Planilha excluída')
  } catch (e) { mostrarSnack(e.message, 'error') }
  finally { salvando.value = false }
}

onMounted(init)
</script>

<style scoped>
/* ── Stat chips (row 1) ── */
.stat-chip {
  display: flex; flex-direction: column; align-items: center;
  padding: 14px 8px; border-radius: 12px;
  background: rgba(128,128,128,0.06);
  border: 1px solid rgba(128,128,128,0.12);
  text-align: center; gap: 2px;
}
.stat-ok   { border-color: rgba(76,175,80,0.3);  background: rgba(76,175,80,0.06); }
.stat-warn { border-color: rgba(255,152,0,0.3); background: rgba(255,152,0,0.06); }
.stat-valor { font-size: 22px; font-weight: 700; line-height: 1.1; }
.stat-label { font-size: 11px; color: rgba(128,128,128,0.8); }

/* ── KPI cards (row 2) ── */
.kpi-card { transition: box-shadow 0.15s, transform 0.1s; }
.kpi-card:hover { box-shadow: 0 4px 24px rgba(0,0,0,0.1) !important; transform: translateY(-2px); }
.kpi-error { border-left: 4px solid rgb(var(--v-theme-error)) !important; }
.kpi-ok    { border-left: 4px solid rgb(var(--v-theme-success)) !important; }
.kpi-icon-wrap {
  width: 44px; height: 44px; border-radius: 12px;
  display: flex; align-items: center; justify-content: center;
}
.icon-error { background: rgba(var(--v-theme-error), 0.12); color: rgb(var(--v-theme-error)); }
.icon-ok    { background: rgba(var(--v-theme-success), 0.12); color: rgb(var(--v-theme-success)); }

/* Recebimentos rows */
.receb-row {
  display: flex; align-items: center; gap: 8px;
}

/* ── Pipeline (row 3) ── */
.pipeline-wrapper {
  display: flex; align-items: center; flex-wrap: wrap; gap: 4px;
}
.pipeline-passo  { display: flex; align-items: center; gap: 4px; }
.pipeline-seta   { display: flex; align-items: center; }
.pipeline-item {
  display: flex; flex-direction: column; align-items: center;
  padding: 12px 16px; border-radius: 10px; gap: 6px;
  background: rgba(128,128,128,0.05);
  border: 1px solid rgba(128,128,128,0.1);
  min-width: 90px;
}
.pipe-ok    { border-color: rgba(76,175,80,0.3);  background: rgba(76,175,80,0.06); }
.pipe-warn  { border-color: rgba(255,152,0,0.3);  background: rgba(255,152,0,0.05); }
.pipe-error { border-color: rgba(244,67,54,0.3);  background: rgba(244,67,54,0.05); }
.pipe-label { font-size: 11px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.04em; }
.pipe-sub   { font-size: 11px; color: rgba(128,128,128,0.7); }
.pipe-pct   { display: none; }

/* ── Legenda ── */
.legenda-row {
  display: flex; flex-wrap: wrap; gap: 20px; align-items: center;
}
.legenda-item {
  display: flex; align-items: center; gap: 8px;
}
.legenda-dot {
  width: 14px; height: 14px; border-radius: 4px; flex-shrink: 0;
  border: 1px solid rgba(128,128,128,0.2);
}

/* ── Tabela ── */
.planilha-wrapper { border: 1px solid rgba(128,128,128,0.2); border-radius: 8px; overflow: hidden; }
.planilha-scroll  { overflow-x: auto; }
.planilha-table   { width: 100%; border-collapse: collapse; min-width: 900px; }

.planilha-table thead tr { background: rgba(128,128,128,0.06); }
.planilha-table th {
  padding: 10px 12px; text-align: left;
  font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.04em;
  border-bottom: 1px solid rgba(128,128,128,0.15);
  white-space: nowrap; line-height: 1.3;
}
.th-label  { min-width: 160px; }
.th-date   { min-width: 90px; }
.th-status { min-width: 80px; text-align: center; }

.sticky-col { position: sticky; left: 0; z-index: 2; background: inherit; }
thead .sticky-col { background: rgba(128,128,128,0.06) !important; z-index: 3; }

.planilha-row td { border-bottom: 1px solid rgba(128,128,128,0.08); }
.planilha-row:last-child td { border-bottom: none; }
.planilha-row:hover td { background: rgba(128,128,128,0.03); }

.td-label  { padding: 9px 12px; font-size: 13px; font-weight: 500; }
.td-date   { padding: 9px 12px; font-size: 12px; color: rgba(128,128,128,0.8); }
.td-status { padding: 0; }
.celula-inner {
  padding: 8px 12px; min-height: 40px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 500;
}

.st-success { background: rgba(76,175,80,0.15) !important; color: #2e7d32; }
.st-error   { background: rgba(244,67,54,0.15) !important; color: #c62828; }
.st-warning { background: rgba(255,152,0,0.15) !important; color: #e65100; }
.st-pending { background: rgba(128,128,128,0.06) !important; }
.st-none    { background: transparent; }

/* Dark mode */
.v-theme--pratikaDark .planilha-wrapper { border-color: rgba(255,255,255,0.1); }
.v-theme--pratikaDark .planilha-table thead tr { background: rgba(255,255,255,0.04); }
.v-theme--pratikaDark thead .sticky-col { background: rgba(255,255,255,0.04) !important; }
.v-theme--pratikaDark .planilha-row td  { border-bottom-color: rgba(255,255,255,0.06); }
.v-theme--pratikaDark .st-success { color: #a5d6a7; }
.v-theme--pratikaDark .st-error   { color: #ef9a9a; }
.v-theme--pratikaDark .st-warning { color: #ffcc80; }
.v-theme--pratikaDark .stat-chip  { background: rgba(255,255,255,0.04); border-color: rgba(255,255,255,0.08); }
.v-theme--pratikaDark .pipeline-item { background: rgba(255,255,255,0.03); border-color: rgba(255,255,255,0.08); }
</style>
