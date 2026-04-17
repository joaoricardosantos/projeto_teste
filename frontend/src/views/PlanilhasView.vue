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
    <v-row v-if="isAdmin" class="mb-2">
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

    <!-- ── Alertas ── -->
    <v-alert v-if="!carregando && !configAtual && !isAdmin" type="info" variant="tonal" class="mb-4">
      Você ainda não possui uma planilha configurada. Contate o administrador.
    </v-alert>
    <v-alert v-if="!carregando && isAdmin && configs.length === 0" type="info" variant="tonal" class="mb-4">
      Nenhuma planilha configurada. Clique em "Gerenciar Planilhas" para criar.
    </v-alert>

    <!-- ── Dashboard ── -->
    <template v-if="configAtual">

      <!-- Seletor de aba + atualizar -->
      <div class="d-flex align-center flex-wrap gap-3 mb-5">
        <v-select
          v-model="abaSelecionada"
          :items="abas"
          item-title="title"
          item-value="title"
          label="Aba / Período"
          variant="outlined"
          density="comfortable"
          style="max-width:280px"
          prepend-inner-icon="mdi-table-large"
          :loading="carregandoAbas"
          @update:model-value="carregarDashboard"
        />
        <v-btn icon variant="tonal" size="small" :loading="carregandoDados" @click="carregarDashboard"
          title="Atualizar">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
        <span v-if="dashboard?.atualizado_em" class="text-caption text-medium-emphasis">
          Atualizado: {{ dashboard.atualizado_em }}
        </span>
      </div>

      <!-- ── KPI Cards ── -->
      <v-row v-if="dashboard" class="mb-5" dense>

        <!-- Prestação de Contas -->
        <v-col cols="12" md="4">
          <v-card
            class="kpi-card"
            :class="dashboard.kpis.prestacao.pendentes > 0 ? 'kpi-error' : 'kpi-ok'"
            rounded="lg"
            @click="abrirModalKpi('prestacao')"
            style="cursor:pointer"
          >
            <v-card-text class="pa-4">
              <div class="d-flex align-center justify-space-between mb-3">
                <div class="kpi-icon-wrap" :class="dashboard.kpis.prestacao.pendentes > 0 ? 'icon-error' : 'icon-ok'">
                  <v-icon size="22">mdi-file-check-outline</v-icon>
                </div>
                <v-chip
                  v-if="dashboard.kpis.prestacao.pendentes > 0"
                  color="error" variant="tonal" size="small"
                >
                  {{ dashboard.kpis.prestacao.pendentes }} atrasada{{ dashboard.kpis.prestacao.pendentes !== 1 ? 's' : '' }}
                </v-chip>
                <v-chip v-else color="success" variant="tonal" size="small">Em dia</v-chip>
              </div>
              <div class="text-subtitle-2 font-weight-semibold">Prestação de Contas</div>
              <div class="text-caption text-medium-emphasis mt-1">
                {{ dashboard.kpis.prestacao.total }} condomínios com prazo definido
              </div>
              <div v-if="dashboard.kpis.prestacao.pendentes > 0" class="text-caption mt-2" style="color:rgb(var(--v-theme-error))">
                Clique para ver quais estão atrasadas
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Recebimentos de Relatórios -->
        <v-col cols="12" md="4">
          <v-card
            class="kpi-card"
            :class="dashboard.kpis.recebimentos.total_pendentes > 0 ? 'kpi-error' : 'kpi-ok'"
            rounded="lg"
            @click="abrirModalKpi('recebimentos')"
            style="cursor:pointer"
          >
            <v-card-text class="pa-4">
              <div class="d-flex align-center justify-space-between mb-3">
                <div class="kpi-icon-wrap" :class="dashboard.kpis.recebimentos.total_pendentes > 0 ? 'icon-error' : 'icon-ok'">
                  <v-icon size="22">mdi-inbox-arrow-down-outline</v-icon>
                </div>
                <v-chip
                  v-if="dashboard.kpis.recebimentos.total_pendentes > 0"
                  color="error" variant="tonal" size="small"
                >
                  {{ dashboard.kpis.recebimentos.total_pendentes }} pendente{{ dashboard.kpis.recebimentos.total_pendentes !== 1 ? 's' : '' }}
                </v-chip>
                <v-chip v-else color="success" variant="tonal" size="small">Em dia</v-chip>
              </div>
              <div class="text-subtitle-2 font-weight-semibold">Recebimentos de Relatórios</div>
              <div class="d-flex gap-3 mt-2 flex-wrap">
                <span class="text-caption">
                  <span :class="dashboard.kpis.recebimentos.agua.pendentes > 0 ? 'text-error' : 'text-success'">
                    ● Água: {{ dashboard.kpis.recebimentos.agua.pendentes }}/{{ dashboard.kpis.recebimentos.agua.total }}
                  </span>
                </span>
                <span class="text-caption">
                  <span :class="dashboard.kpis.recebimentos.gas.pendentes > 0 ? 'text-error' : 'text-success'">
                    ● Gás: {{ dashboard.kpis.recebimentos.gas.pendentes }}/{{ dashboard.kpis.recebimentos.gas.total }}
                  </span>
                </span>
                <span class="text-caption">
                  <span :class="dashboard.kpis.recebimentos.reservas.pendentes > 0 ? 'text-error' : 'text-success'">
                    ● Reservas: {{ dashboard.kpis.recebimentos.reservas.pendentes }}/{{ dashboard.kpis.recebimentos.reservas.total }}
                  </span>
                </span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>

        <!-- Geração de Boletos -->
        <v-col cols="12" md="4">
          <v-card
            class="kpi-card"
            :class="dashboard.kpis.boletos.atrasados > 0 ? 'kpi-error' : 'kpi-ok'"
            rounded="lg"
            @click="abrirModalKpi('boletos')"
            style="cursor:pointer"
          >
            <v-card-text class="pa-4">
              <div class="d-flex align-center justify-space-between mb-3">
                <div class="kpi-icon-wrap" :class="dashboard.kpis.boletos.atrasados > 0 ? 'icon-error' : 'icon-ok'">
                  <v-icon size="22">mdi-barcode</v-icon>
                </div>
                <v-chip
                  v-if="dashboard.kpis.boletos.atrasados > 0"
                  color="error" variant="tonal" size="small"
                >
                  {{ dashboard.kpis.boletos.atrasados }} atrasado{{ dashboard.kpis.boletos.atrasados !== 1 ? 's' : '' }}
                </v-chip>
                <v-chip v-else color="success" variant="tonal" size="small">Em dia</v-chip>
              </div>
              <div class="text-subtitle-2 font-weight-semibold">Geração de Boletos</div>
              <div class="d-flex gap-4 mt-2">
                <span class="text-caption text-success">
                  ✔ {{ dashboard.kpis.boletos.no_prazo }} no prazo
                </span>
                <span v-if="dashboard.kpis.boletos.atrasados > 0" class="text-caption text-error">
                  ✖ {{ dashboard.kpis.boletos.atrasados }} atrasado{{ dashboard.kpis.boletos.atrasados !== 1 ? 's' : '' }}
                </span>
              </div>
            </v-card-text>
          </v-card>
        </v-col>
      </v-row>

      <!-- ── Legenda ── -->
      <div v-if="dashboard" class="d-flex gap-4 mb-4 flex-wrap">
        <div v-for="l in legenda" :key="l.label" class="d-flex align-center gap-2">
          <div class="legenda-dot" :style="`background:${l.cor}`"></div>
          <span class="text-caption text-medium-emphasis">{{ l.label }}</span>
        </div>
      </div>

      <!-- ── Tabela ── -->
      <div v-if="dashboard && !carregandoDados" class="planilha-wrapper">
        <div class="planilha-scroll">
          <table class="planilha-table">
            <thead>
              <tr>
                <th class="sticky-col th-label">Condomínio</th>
                <th class="th-date">Prazo Prestação</th>
                <th class="th-status">OK Prestação</th>
                <th class="th-status">Água</th>
                <th class="th-status">Gás</th>
                <th class="th-status">Reservas</th>
                <th class="th-date">Prazo Boleto</th>
                <th class="th-status">Geração</th>
                <th class="th-status">E-mail</th>
                <th class="th-status">Impresso</th>
                <th class="th-status">Gráfica</th>
                <th class="th-status">Retorno</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="dashboard.linhas.length === 0">
                <td colspan="12" class="text-center text-medium-emphasis py-8">
                  Nenhuma linha encontrada nesta aba.
                </td>
              </tr>
              <tr v-for="(l, i) in dashboard.linhas" :key="i" class="planilha-row">
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

      <div v-if="carregandoDados" class="d-flex justify-center py-12">
        <v-progress-circular indeterminate color="primary" />
      </div>

    </template>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- Modal KPI detalhe                                                    -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <v-dialog v-model="modalKpi.show" max-width="500">
      <v-card rounded="lg">
        <v-card-title class="pa-4 pb-2 d-flex align-center justify-space-between">
          <span class="text-subtitle-1 font-weight-medium">{{ modalKpi.titulo }}</span>
          <v-btn icon variant="text" size="small" @click="modalKpi.show = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4" style="max-height:60vh;overflow-y:auto">

          <!-- Prestação -->
          <template v-if="modalKpi.tipo === 'prestacao'">
            <v-alert v-if="dashboard.kpis.prestacao.pendentes === 0" type="success" variant="tonal" density="compact">
              Todas as prestações estão em dia!
            </v-alert>
            <v-list v-else lines="one" density="compact">
              <v-list-item v-for="nome in dashboard.kpis.prestacao.lista" :key="nome"
                prepend-icon="mdi-alert-circle-outline" color="error">
                <template #title><span class="text-body-2">{{ nome }}</span></template>
              </v-list-item>
            </v-list>
          </template>

          <!-- Recebimentos -->
          <template v-else-if="modalKpi.tipo === 'recebimentos'">
            <div v-if="dashboard.kpis.recebimentos.total_pendentes === 0">
              <v-alert type="success" variant="tonal" density="compact">
                Todos os relatórios foram recebidos!
              </v-alert>
            </div>
            <div v-else>
              <template v-for="(grupo, key) in recebGrupos" :key="key">
                <div v-if="dashboard.kpis.recebimentos[key].pendentes > 0" class="mb-4">
                  <div class="text-subtitle-2 mb-2 d-flex align-center gap-2">
                    <v-icon size="16" color="error">mdi-circle</v-icon>
                    {{ grupo }} —
                    <span class="text-error">{{ dashboard.kpis.recebimentos[key].pendentes }} pendente{{ dashboard.kpis.recebimentos[key].pendentes !== 1 ? 's' : '' }}</span>
                  </div>
                  <v-list lines="one" density="compact" class="rounded border">
                    <template v-for="(nome, ni) in dashboard.kpis.recebimentos[key].lista" :key="ni">
                      <v-divider v-if="ni > 0" />
                      <v-list-item prepend-icon="mdi-home-outline">
                        <template #title><span class="text-body-2">{{ nome }}</span></template>
                      </v-list-item>
                    </template>
                  </v-list>
                </div>
              </template>
            </div>
          </template>

          <!-- Boletos -->
          <template v-else-if="modalKpi.tipo === 'boletos'">
            <div class="d-flex gap-4 mb-3">
              <v-chip color="success" variant="tonal">✔ {{ dashboard.kpis.boletos.no_prazo }} no prazo</v-chip>
              <v-chip color="error" variant="tonal">✖ {{ dashboard.kpis.boletos.atrasados }} atrasados</v-chip>
            </div>
            <v-alert v-if="dashboard.kpis.boletos.atrasados === 0" type="success" variant="tonal" density="compact">
              Todos os boletos foram gerados no prazo!
            </v-alert>
            <v-list v-else lines="one" density="compact" class="rounded border">
              <template v-for="(nome, ni) in dashboard.kpis.boletos.lista_atrasados" :key="ni">
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
    <!-- Dialog: gerenciar configs (admin)                                    -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <v-dialog v-model="dialogGerenciar" max-width="620" scrollable>
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
                    {{ cfg.spreadsheet_id.substring(0, 30) }}…
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

          <!-- Form config -->
          <v-expand-transition>
            <div v-if="formConfig.aberto">
              <v-divider class="mb-4" />
              <div class="text-subtitle-2 mb-3">{{ formConfig.id ? 'Editar' : 'Nova planilha' }}</div>
              <v-row dense>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="formConfig.funcionario_id"
                    :items="usuarios"
                    item-title="nome"
                    item-value="id"
                    label="Funcionário"
                    variant="outlined"
                    density="comfortable"
                    :disabled="!!formConfig.id"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formConfig.nome"
                    label="Nome"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="formConfig.spreadsheet_id"
                    label="ID do Google Sheets"
                    variant="outlined"
                    density="comfortable"
                    hint="Cole o ID da URL da planilha (entre /d/ e /edit)"
                    persistent-hint
                  />
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

    <!-- ── Confirm dialog ── -->
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

    <!-- ── Snackbar ── -->
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

// ── Estado ────────────────────────────────────────────────────────────────────
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

const dialogGerenciar = ref(false)
const formConfig = ref({
  aberto: false, id: null, funcionario_id: null, nome: '', spreadsheet_id: '',
})

const modalKpi = ref({ show: false, tipo: '', titulo: '' })
const snack    = ref({ show: false, color: 'success', msg: '' })
const confirmDlg = ref({ show: false, msg: '', action: null })

const legenda = [
  { label: 'Concluído no prazo', cor: '#4caf50' },
  { label: 'Atrasado', cor: '#f44336' },
  { label: 'Vence em breve (2 dias)', cor: '#ff9800' },
  { label: 'Pendente / Sem prazo', cor: 'rgba(128,128,128,0.1)' },
]

const recebGrupos = { agua: 'Relatório de Água', gas: 'Relatório de Gás', reservas: 'Relatório de Reservas' }

// ── Helpers ───────────────────────────────────────────────────────────────────
function mostrarSnack(msg, color = 'success') {
  snack.value = { show: true, color, msg }
}
function confirmarExclusao(msg, action) {
  confirmDlg.value = {
    show: true, msg,
    action: async () => { await action(); confirmDlg.value.show = false },
  }
}

function celulaDisplay(celula) {
  if (!celula.valor) return '—'
  return celula.valor
}

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
  abas.value = []
  abaSelecionada.value = null
  dashboard.value = null
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
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    carregandoAbas.value = false
  }
}

async function carregarDashboard() {
  if (!configAtual.value || !abaSelecionada.value) return
  carregandoDados.value = true
  dashboard.value = null
  try {
    dashboard.value = await apiFetch(
      `/planilhas/configs/${configAtual.value.id}/dashboard?aba=${encodeURIComponent(abaSelecionada.value)}`
    )
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    carregandoDados.value = false
  }
}

// ── KPI modal ─────────────────────────────────────────────────────────────────
function abrirModalKpi(tipo) {
  const titulos = {
    prestacao: 'Prestação de Contas Atrasadas',
    recebimentos: 'Recebimentos de Relatórios Pendentes',
    boletos: 'Geração de Boletos',
  }
  modalKpi.value = { show: true, tipo, titulo: titulos[tipo] }
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
    const body = {
      funcionario_id: formConfig.value.funcionario_id,
      nome: formConfig.value.nome,
      spreadsheet_id: formConfig.value.spreadsheet_id,
    }
    if (formConfig.value.id) {
      const updated = await apiFetch(`/planilhas/configs/${formConfig.value.id}`, {
        method: 'PUT', body: JSON.stringify(body),
      })
      const idx = configs.value.findIndex(c => c.id === updated.id)
      if (idx >= 0) configs.value[idx] = updated
    } else {
      const created = await apiFetch('/planilhas/configs', { method: 'POST', body: JSON.stringify(body) })
      configs.value.push(created)
    }
    formConfig.value.aberto = false
    mostrarSnack('Planilha salva')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

async function deletarConfig(cfg) {
  salvando.value = true
  try {
    await apiFetch(`/planilhas/configs/${cfg.id}`, { method: 'DELETE' })
    configs.value = configs.value.filter(c => c.id !== cfg.id)
    if (configSelecionadaId.value === cfg.id) {
      configSelecionadaId.value = null
      configAtual.value = null
      dashboard.value = null
    }
    mostrarSnack('Planilha excluída')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

onMounted(init)
</script>

<style scoped>
/* KPI cards */
.kpi-card { transition: box-shadow 0.15s, transform 0.1s; }
.kpi-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.12) !important; transform: translateY(-1px); }
.kpi-error { border-left: 4px solid rgb(var(--v-theme-error)) !important; }
.kpi-ok    { border-left: 4px solid rgb(var(--v-theme-success)) !important; }

.kpi-icon-wrap {
  width: 40px; height: 40px; border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
}
.icon-error { background: rgba(var(--v-theme-error), 0.12); color: rgb(var(--v-theme-error)); }
.icon-ok    { background: rgba(var(--v-theme-success), 0.12); color: rgb(var(--v-theme-success)); }

/* Legenda */
.legenda-dot { width: 12px; height: 12px; border-radius: 3px; flex-shrink: 0; }

/* Tabela */
.planilha-wrapper {
  border: 1px solid rgba(128,128,128,0.2);
  border-radius: 8px; overflow: hidden;
}
.planilha-scroll { overflow-x: auto; }
.planilha-table  { width: 100%; border-collapse: collapse; min-width: 900px; }

.planilha-table thead tr { background: rgba(128,128,128,0.06); }
.planilha-table th {
  padding: 10px 12px;
  text-align: left;
  font-size: 11px; font-weight: 600;
  text-transform: uppercase; letter-spacing: 0.04em;
  border-bottom: 1px solid rgba(128,128,128,0.15);
  white-space: nowrap;
}
.th-label  { min-width: 160px; }
.th-date   { min-width: 110px; }
.th-status { min-width: 90px; text-align: center; }

/* Sticky col */
.sticky-col {
  position: sticky; left: 0; z-index: 2;
  background: inherit;
}
thead .sticky-col {
  background: rgba(128,128,128,0.06) !important;
  z-index: 3;
}

/* Linhas */
.planilha-row td { border-bottom: 1px solid rgba(128,128,128,0.08); }
.planilha-row:last-child td { border-bottom: none; }
.planilha-row:hover td { background: rgba(128,128,128,0.03); }

.td-label { padding: 9px 12px; font-size: 13px; font-weight: 500; }
.td-date  { padding: 9px 12px; font-size: 12px; color: rgba(128,128,128,0.8); }
.td-status { padding: 0; }
.celula-inner {
  padding: 8px 12px; min-height: 40px;
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 500;
}

/* Status */
.st-success { background: rgba(76,175,80,0.15) !important; color: #2e7d32; }
.st-error   { background: rgba(244,67,54,0.15) !important; color: #c62828; }
.st-warning { background: rgba(255,152,0,0.15) !important; color: #e65100; }
.st-pending { background: rgba(128,128,128,0.06) !important; }
.st-none    { background: transparent; }

/* Dark mode */
.v-theme--pratikaDark .planilha-wrapper { border-color: rgba(255,255,255,0.1); }
.v-theme--pratikaDark .planilha-table thead tr { background: rgba(255,255,255,0.04); }
.v-theme--pratikaDark thead .sticky-col { background: rgba(255,255,255,0.04) !important; }
.v-theme--pratikaDark .planilha-row td { border-bottom-color: rgba(255,255,255,0.06); }
.v-theme--pratikaDark .st-success { color: #a5d6a7; }
.v-theme--pratikaDark .st-error   { color: #ef9a9a; }
.v-theme--pratikaDark .st-warning { color: #ffcc80; }
</style>
