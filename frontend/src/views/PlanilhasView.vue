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
      <div class="d-flex align-center gap-2">
        <v-btn v-if="isAdmin" color="primary" variant="tonal" prepend-icon="mdi-cog-outline" @click="abrirGerenciarConfigs">
          Gerenciar Planilhas
        </v-btn>
      </div>
    </div>

    <!-- ── Seletor de funcionário (admin) ── -->
    <v-row v-if="isAdmin" class="mb-4">
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

    <!-- ── Estado: sem planilha ── -->
    <v-alert v-if="!carregando && !configAtual && !isAdmin" type="info" variant="tonal" class="mb-4">
      Você ainda não possui uma planilha configurada. Entre em contato com o administrador.
    </v-alert>
    <v-alert v-if="!carregando && isAdmin && configs.length === 0" type="info" variant="tonal" class="mb-4">
      Nenhuma planilha configurada ainda. Clique em "Gerenciar Planilhas" para criar.
    </v-alert>

    <!-- ── Dashboard ── -->
    <template v-if="configAtual">

      <!-- Navegação de período -->
      <div class="d-flex align-center justify-space-between mb-4 flex-wrap gap-3">
        <div class="d-flex align-center gap-2">
          <v-btn icon variant="text" @click="mudarMes(-1)">
            <v-icon>mdi-chevron-left</v-icon>
          </v-btn>
          <span class="text-subtitle-1 font-weight-medium" style="min-width:160px;text-align:center;">
            {{ nomeMes(mesSelecionado) }} {{ anoSelecionado }}
          </span>
          <v-btn icon variant="text" @click="mudarMes(1)">
            <v-icon>mdi-chevron-right</v-icon>
          </v-btn>
        </div>

        <div class="d-flex align-center gap-2">
          <v-chip v-if="periodoAtual" size="small" color="success" variant="tonal">
            <v-icon start size="14">mdi-check-circle-outline</v-icon>
            Período disponível
          </v-chip>
          <v-chip v-else size="small" color="warning" variant="tonal">
            <v-icon start size="14">mdi-clock-outline</v-icon>
            Sem dados este mês
          </v-chip>
          <v-btn v-if="isAdmin && !periodoAtual" color="primary" size="small" variant="tonal"
            prepend-icon="mdi-plus" @click="criarPeriodo" :loading="salvando">
            Criar período
          </v-btn>
          <v-btn v-if="isAdmin && periodoAtual" color="secondary" size="small" variant="tonal"
            prepend-icon="mdi-plus" @click="dialogLinha = true">
            Adicionar linha
          </v-btn>
        </div>
      </div>

      <!-- Legenda -->
      <div class="d-flex gap-3 mb-4 flex-wrap">
        <div class="legenda-item">
          <div class="legenda-dot" style="background:#4caf50"></div>
          <span class="text-caption text-medium-emphasis">Concluído</span>
        </div>
        <div class="legenda-item">
          <div class="legenda-dot" style="background:#f44336"></div>
          <span class="text-caption text-medium-emphasis">Atrasado</span>
        </div>
        <div class="legenda-item">
          <div class="legenda-dot" style="background:#ff9800"></div>
          <span class="text-caption text-medium-emphasis">Vence em breve</span>
        </div>
        <div class="legenda-item">
          <div class="legenda-dot" style="background:rgba(128,128,128,0.15)"></div>
          <span class="text-caption text-medium-emphasis">Pendente</span>
        </div>
      </div>

      <!-- Tabela de dashboard -->
      <div v-if="periodoAtual && !carregandoPeriodo" class="planilha-wrapper">
        <div class="planilha-scroll">
          <table class="planilha-table">
            <thead>
              <tr>
                <th class="col-label sticky-col">Item / Condomínio</th>
                <th v-for="col in configAtual.colunas" :key="col.id" class="col-header">
                  <div class="col-header-inner">
                    <span>{{ col.nome }}</span>
                    <v-chip v-if="col.prazo_dias" size="x-small" color="info" variant="tonal" class="ml-1">
                      {{ col.prazo_dias }}d
                    </v-chip>
                  </div>
                  <div class="text-caption text-medium-emphasis mt-1">{{ tipoLabel(col.tipo) }}</div>
                </th>
                <th v-if="isAdmin" class="col-acoes">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="periodoAtual.linhas.length === 0">
                <td :colspan="configAtual.colunas.length + (isAdmin ? 2 : 1)" class="text-center text-medium-emphasis py-8">
                  Nenhuma linha cadastrada. Clique em "Adicionar linha" para começar.
                </td>
              </tr>
              <tr v-for="linha in periodoAtual.linhas" :key="linha.id" class="planilha-row">
                <td class="col-label sticky-col">
                  <span class="label-text">{{ linha.label }}</span>
                </td>
                <td
                  v-for="col in configAtual.colunas"
                  :key="col.id"
                  class="col-celula"
                  :class="statusClass(col, getCelula(linha, col.id), anoSelecionado, mesSelecionado)"
                  @click="editarCelula(linha, col)"
                >
                  <div class="celula-inner">
                    <template v-if="col.tipo === 'booleano'">
                      <v-icon
                        :color="getCelula(linha, col.id)?.valor === 'true' ? 'success' : 'grey-lighten-1'"
                        size="20"
                      >
                        {{ getCelula(linha, col.id)?.valor === 'true' ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                      </v-icon>
                    </template>
                    <template v-else-if="col.tipo === 'data'">
                      <span class="celula-valor" v-if="getCelula(linha, col.id)?.valor">
                        {{ formatarData(getCelula(linha, col.id).valor) }}
                      </span>
                      <span class="celula-vazia" v-else>—</span>
                    </template>
                    <template v-else>
                      <span class="celula-valor" v-if="getCelula(linha, col.id)?.valor">
                        {{ getCelula(linha, col.id).valor }}
                      </span>
                      <span class="celula-vazia" v-else>—</span>
                    </template>
                  </div>
                </td>
                <td v-if="isAdmin" class="col-acoes">
                  <v-btn icon size="x-small" variant="text" color="error" @click.stop="confirmarDeleteLinha(linha)">
                    <v-icon size="16">mdi-delete-outline</v-icon>
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="carregandoPeriodo" class="d-flex justify-center py-12">
        <v-progress-circular indeterminate color="primary" />
      </div>

      <div v-if="!periodoAtual && !carregandoPeriodo && !isAdmin" class="text-center py-12 text-medium-emphasis">
        <v-icon size="48" class="mb-3">mdi-calendar-blank-outline</v-icon>
        <div>Nenhum dado disponível para este mês.</div>
      </div>

    </template>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- Dialog: editar célula                                                  -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <v-dialog v-model="dialogCelula" max-width="380" @keydown.esc="dialogCelula = false">
      <v-card v-if="celulaEdit">
        <v-card-title class="text-subtitle-1 font-weight-medium pa-4 pb-2">
          {{ celulaEdit.coluna.nome }}
          <div class="text-caption text-medium-emphasis font-weight-regular">{{ celulaEdit.linha.label }}</div>
        </v-card-title>
        <v-card-text class="pa-4 pt-2">
          <!-- Booleano -->
          <template v-if="celulaEdit.coluna.tipo === 'booleano'">
            <v-switch
              v-model="celulaValorTemp"
              :true-value="'true'"
              :false-value="'false'"
              color="success"
              label="Concluído"
              hide-details
            />
          </template>
          <!-- Data -->
          <template v-else-if="celulaEdit.coluna.tipo === 'data'">
            <v-text-field
              v-model="celulaValorTemp"
              type="date"
              label="Data"
              variant="outlined"
              density="comfortable"
            />
          </template>
          <!-- Texto -->
          <template v-else>
            <v-text-field
              v-model="celulaValorTemp"
              label="Valor"
              variant="outlined"
              density="comfortable"
              autofocus
            />
          </template>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0 gap-2">
          <v-btn variant="text" color="error" @click="salvarCelula(null)">Limpar</v-btn>
          <v-spacer />
          <v-btn variant="text" @click="dialogCelula = false">Cancelar</v-btn>
          <v-btn color="primary" variant="tonal" @click="salvarCelula(celulaValorTemp)" :loading="salvando">
            Salvar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- Dialog: adicionar linha                                                -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <v-dialog v-model="dialogLinha" max-width="400" @keydown.esc="dialogLinha = false">
      <v-card>
        <v-card-title class="pa-4 pb-2 text-subtitle-1 font-weight-medium">Adicionar linha</v-card-title>
        <v-card-text class="pa-4 pt-2">
          <v-text-field
            v-model="novaLinhaLabel"
            label="Nome do item / condomínio"
            variant="outlined"
            density="comfortable"
            autofocus
            @keydown.enter="adicionarLinha"
          />
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="dialogLinha = false">Cancelar</v-btn>
          <v-btn color="primary" variant="tonal" @click="adicionarLinha" :loading="salvando"
            :disabled="!novaLinhaLabel.trim()">
            Adicionar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <!-- Dialog: gerenciar configs (admin)                                      -->
    <!-- ══════════════════════════════════════════════════════════════════════ -->
    <v-dialog v-model="dialogGerenciar" max-width="720" scrollable>
      <v-card>
        <v-card-title class="pa-4 pb-2 d-flex align-center justify-space-between">
          <span class="text-subtitle-1 font-weight-medium">Gerenciar Planilhas</span>
          <v-btn icon variant="text" @click="dialogGerenciar = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4" style="max-height:70vh">

          <!-- Lista de configs existentes -->
          <div class="d-flex align-center justify-space-between mb-3">
            <span class="text-subtitle-2">Planilhas configuradas</span>
            <v-btn size="small" color="primary" variant="tonal" prepend-icon="mdi-plus" @click="abrirNovaConfig">
              Nova planilha
            </v-btn>
          </div>

          <v-list v-if="configs.length > 0" lines="two" class="rounded border mb-4">
            <template v-for="(cfg, idx) in configs" :key="cfg.id">
              <v-divider v-if="idx > 0" />
              <v-list-item>
                <template #title>{{ cfg.funcionario_nome }}</template>
                <template #subtitle>{{ cfg.nome }}</template>
                <template #append>
                  <div class="d-flex gap-1">
                    <v-btn icon size="x-small" variant="text" @click="selecionarConfigParaEditar(cfg)">
                      <v-icon size="16">mdi-pencil-outline</v-icon>
                    </v-btn>
                    <v-btn icon size="x-small" variant="text" color="error" @click="confirmarDeleteConfig(cfg)">
                      <v-icon size="16">mdi-delete-outline</v-icon>
                    </v-btn>
                  </div>
                </template>
              </v-list-item>
            </template>
          </v-list>

          <v-alert v-else type="info" variant="tonal" density="compact" class="mb-4">
            Nenhuma planilha configurada ainda.
          </v-alert>

          <!-- Form nova/editar config -->
          <v-expand-transition>
            <div v-if="formConfig.aberto" class="mt-2">
              <v-divider class="mb-4" />
              <div class="text-subtitle-2 mb-3">
                {{ formConfig.editandoId ? 'Editar planilha' : 'Nova planilha' }}
              </div>
              <v-row dense>
                <v-col cols="12" md="6">
                  <v-select
                    v-model="formConfig.funcionarioId"
                    :items="usuarios"
                    item-title="nome"
                    item-value="id"
                    label="Funcionário"
                    variant="outlined"
                    density="comfortable"
                    :disabled="!!formConfig.editandoId"
                  />
                </v-col>
                <v-col cols="12" md="6">
                  <v-text-field
                    v-model="formConfig.nome"
                    label="Nome da planilha"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
              </v-row>
              <div class="d-flex gap-2 justify-end mt-2">
                <v-btn variant="text" @click="formConfig.aberto = false">Cancelar</v-btn>
                <v-btn color="primary" variant="tonal" @click="salvarConfig" :loading="salvando"
                  :disabled="!formConfig.funcionarioId || !formConfig.nome">
                  {{ formConfig.editandoId ? 'Atualizar' : 'Criar' }}
                </v-btn>
              </div>
            </div>
          </v-expand-transition>

          <!-- Gerenciar colunas da config selecionada -->
          <template v-if="configParaColunas">
            <v-divider class="my-4" />
            <div class="d-flex align-center justify-space-between mb-3">
              <span class="text-subtitle-2">Colunas de {{ configParaColunas.funcionario_nome }}</span>
              <v-btn size="small" color="secondary" variant="tonal" prepend-icon="mdi-plus"
                @click="abrirNovaColuna">
                Nova coluna
              </v-btn>
            </div>

            <v-list v-if="configParaColunas.colunas.length > 0" lines="two" class="rounded border mb-3">
              <template v-for="(col, idx) in configParaColunas.colunas" :key="col.id">
                <v-divider v-if="idx > 0" />
                <v-list-item>
                  <template #title>{{ col.nome }}</template>
                  <template #subtitle>
                    {{ tipoLabel(col.tipo) }}
                    <span v-if="col.prazo_dias"> · Prazo: {{ col.prazo_dias }} dias</span>
                  </template>
                  <template #append>
                    <div class="d-flex gap-1">
                      <v-btn icon size="x-small" variant="text" @click="selecionarColunaParaEditar(col)">
                        <v-icon size="16">mdi-pencil-outline</v-icon>
                      </v-btn>
                      <v-btn icon size="x-small" variant="text" color="error" @click="confirmarDeleteColuna(col)">
                        <v-icon size="16">mdi-delete-outline</v-icon>
                      </v-btn>
                    </div>
                  </template>
                </v-list-item>
              </template>
            </v-list>

            <v-alert v-else type="info" variant="tonal" density="compact" class="mb-3">
              Nenhuma coluna. Adicione colunas para definir o que será rastreado.
            </v-alert>

            <!-- Form coluna -->
            <v-expand-transition>
              <div v-if="formColuna.aberto">
                <v-row dense>
                  <v-col cols="12" md="4">
                    <v-text-field
                      v-model="formColuna.nome"
                      label="Nome da coluna"
                      variant="outlined"
                      density="comfortable"
                    />
                  </v-col>
                  <v-col cols="6" md="3">
                    <v-select
                      v-model="formColuna.tipo"
                      :items="tiposColuna"
                      item-title="label"
                      item-value="value"
                      label="Tipo"
                      variant="outlined"
                      density="comfortable"
                    />
                  </v-col>
                  <v-col cols="6" md="2">
                    <v-text-field
                      v-model.number="formColuna.prazo_dias"
                      label="Prazo (dias)"
                      type="number"
                      variant="outlined"
                      density="comfortable"
                      hint="Dias após início do mês"
                    />
                  </v-col>
                  <v-col cols="6" md="1" class="d-flex align-center">
                    <v-text-field
                      v-model.number="formColuna.ordem"
                      label="Ordem"
                      type="number"
                      variant="outlined"
                      density="comfortable"
                    />
                  </v-col>
                  <v-col cols="6" md="2" class="d-flex align-center justify-end gap-2">
                    <v-btn variant="text" size="small" @click="formColuna.aberto = false">Cancelar</v-btn>
                    <v-btn color="primary" variant="tonal" size="small" @click="salvarColuna"
                      :loading="salvando" :disabled="!formColuna.nome">
                      {{ formColuna.editandoId ? 'Atualizar' : 'Criar' }}
                    </v-btn>
                  </v-col>
                </v-row>
              </div>
            </v-expand-transition>
          </template>

        </v-card-text>
      </v-card>
    </v-dialog>

    <!-- ── Snackbar ── -->
    <v-snackbar v-model="snack.show" :color="snack.color" :timeout="3000" location="bottom right">
      {{ snack.msg }}
    </v-snackbar>

    <!-- ── Confirm delete ── -->
    <v-dialog v-model="confirmDialog.show" max-width="340">
      <v-card>
        <v-card-text class="pa-5">{{ confirmDialog.msg }}</v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="confirmDialog.show = false">Cancelar</v-btn>
          <v-btn color="error" variant="tonal" @click="confirmDialog.action" :loading="salvando">
            Excluir
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </v-container>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'

const API = '/api'
const token = () => localStorage.getItem('access_token')
const isAdmin = computed(() => localStorage.getItem('is_admin') === 'true')

// ── Estado global ─────────────────────────────────────────────────────────────
const carregando       = ref(false)
const carregandoPeriodo = ref(false)
const salvando         = ref(false)
const configs          = ref([])        // lista de configs (admin)
const usuarios         = ref([])        // lista de usuários (admin)
const configSelecionadaId = ref(null)   // id da config selecionada no dropdown (admin)
const configAtual      = ref(null)      // config completa em exibição
const periodoAtual     = ref(null)      // dados do período selecionado

const anoSelecionado   = ref(new Date().getFullYear())
const mesSelecionado   = ref(new Date().getMonth() + 1)

// ── Dialogs ───────────────────────────────────────────────────────────────────
const dialogCelula    = ref(false)
const dialogLinha     = ref(false)
const dialogGerenciar = ref(false)
const novaLinhaLabel  = ref('')

const celulaEdit      = ref(null)   // { linha, coluna }
const celulaValorTemp = ref(null)

const configParaColunas = ref(null) // config sendo editada no gerenciador

const formConfig = ref({ aberto: false, editandoId: null, funcionarioId: null, nome: '' })
const formColuna = ref({ aberto: false, editandoId: null, nome: '', tipo: 'texto', prazo_dias: null, ordem: 0 })

const snack       = ref({ show: false, color: 'success', msg: '' })
const confirmDialog = ref({ show: false, msg: '', action: null })

const tiposColuna = [
  { label: 'Texto', value: 'texto' },
  { label: 'Data', value: 'data' },
  { label: 'Booleano (Sim/Não)', value: 'booleano' },
]

// ── Helpers ───────────────────────────────────────────────────────────────────
const nomeMes = (m) => ['Janeiro','Fevereiro','Março','Abril','Maio','Junho',
  'Julho','Agosto','Setembro','Outubro','Novembro','Dezembro'][m - 1]

const tipoLabel = (t) => ({ texto: 'Texto', data: 'Data', booleano: 'Sim/Não' }[t] || t)

const formatarData = (v) => {
  if (!v) return '—'
  const [y, m, d] = v.split('-')
  return `${d}/${m}/${y}`
}

const getCelula = (linha, colunaId) => linha.celulas.find(c => c.coluna_id === colunaId)

function statusClass(coluna, celula, ano, mes) {
  if (!coluna.prazo_dias) return ''
  const isDone = celula?.valor && celula.valor !== '' && celula.valor !== 'false'
  if (isDone) return 'status-success'

  const deadline = new Date(ano, mes - 1, 1)
  deadline.setDate(deadline.getDate() + coluna.prazo_dias)
  deadline.setHours(0, 0, 0, 0)
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  if (today > deadline) return 'status-error'
  const warn = new Date(deadline)
  warn.setDate(warn.getDate() - 2)
  if (today >= warn) return 'status-warning'
  return 'status-pending'
}

function mostrarSnack(msg, color = 'success') {
  snack.value = { show: true, color, msg }
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

// ── Carregamento ──────────────────────────────────────────────────────────────
async function carregarDados() {
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
        const data = await apiFetch('/planilhas/minha')
        configAtual.value = data.config
        await carregarPeriodo()
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
  periodoAtual.value = null
  if (configAtual.value) await carregarPeriodo()
}

async function carregarPeriodo() {
  if (!configAtual.value) return
  carregandoPeriodo.value = true
  periodoAtual.value = null
  try {
    const periodos = await apiFetch(`/planilhas/configs/${configAtual.value.id}/periodos`)
    const p = periodos.find(x => x.ano === anoSelecionado.value && x.mes === mesSelecionado.value)
    if (p) {
      periodoAtual.value = await apiFetch(`/planilhas/periodos/${p.id}`)
    }
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    carregandoPeriodo.value = false
  }
}

function mudarMes(delta) {
  let m = mesSelecionado.value + delta
  let a = anoSelecionado.value
  if (m > 12) { m = 1; a++ }
  if (m < 1)  { m = 12; a-- }
  mesSelecionado.value = m
  anoSelecionado.value = a
}

watch([anoSelecionado, mesSelecionado], () => {
  if (configAtual.value) carregarPeriodo()
})

// ── Período ───────────────────────────────────────────────────────────────────
async function criarPeriodo() {
  if (!configAtual.value) return
  salvando.value = true
  try {
    await apiFetch(`/planilhas/configs/${configAtual.value.id}/periodos`, {
      method: 'POST',
      body: JSON.stringify({ ano: anoSelecionado.value, mes: mesSelecionado.value }),
    })
    await carregarPeriodo()
    mostrarSnack('Período criado com sucesso')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

// ── Linhas ────────────────────────────────────────────────────────────────────
async function adicionarLinha() {
  if (!novaLinhaLabel.value.trim() || !periodoAtual.value) return
  salvando.value = true
  try {
    const nova = await apiFetch(`/planilhas/periodos/${periodoAtual.value.id}/linhas`, {
      method: 'POST',
      body: JSON.stringify({ label: novaLinhaLabel.value.trim(), ordem: periodoAtual.value.linhas.length }),
    })
    periodoAtual.value.linhas.push(nova)
    novaLinhaLabel.value = ''
    dialogLinha.value = false
    mostrarSnack('Linha adicionada')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

function confirmarDeleteLinha(linha) {
  confirmDialog.value = {
    show: true,
    msg: `Excluir a linha "${linha.label}" e todos os seus dados?`,
    action: () => deletarLinha(linha),
  }
}

async function deletarLinha(linha) {
  salvando.value = true
  try {
    await apiFetch(`/planilhas/linhas/${linha.id}`, { method: 'DELETE' })
    periodoAtual.value.linhas = periodoAtual.value.linhas.filter(l => l.id !== linha.id)
    confirmDialog.value.show = false
    mostrarSnack('Linha removida')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

// ── Células ───────────────────────────────────────────────────────────────────
function editarCelula(linha, coluna) {
  celulaEdit.value = { linha, coluna }
  const existente = getCelula(linha, coluna.id)
  celulaValorTemp.value = existente?.valor ?? (coluna.tipo === 'booleano' ? 'false' : '')
  dialogCelula.value = true
}

async function salvarCelula(valor) {
  if (!celulaEdit.value) return
  salvando.value = true
  try {
    const { linha, coluna } = celulaEdit.value
    const result = await apiFetch('/planilhas/celulas', {
      method: 'PUT',
      body: JSON.stringify({ linha_id: linha.id, coluna_id: coluna.id, valor: valor ?? null }),
    })
    const idx = linha.celulas.findIndex(c => c.coluna_id === coluna.id)
    if (idx >= 0) linha.celulas[idx] = result
    else linha.celulas.push(result)
    dialogCelula.value = false
    mostrarSnack('Salvo')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

// ── Gerenciar configs (admin) ─────────────────────────────────────────────────
async function abrirGerenciarConfigs() {
  if (usuarios.value.length === 0) {
    const users = await apiFetch('/planilhas/usuarios').catch(() => [])
    usuarios.value = users
  }
  configParaColunas.value = null
  formConfig.value = { aberto: false, editandoId: null, funcionarioId: null, nome: '' }
  formColuna.value = { aberto: false, editandoId: null, nome: '', tipo: 'texto', prazo_dias: null, ordem: 0 }
  dialogGerenciar.value = true
}

function abrirNovaConfig() {
  formConfig.value = { aberto: true, editandoId: null, funcionarioId: null, nome: '' }
}

function selecionarConfigParaEditar(cfg) {
  configParaColunas.value = cfg
  formConfig.value = { aberto: true, editandoId: cfg.id, funcionarioId: cfg.funcionario_id, nome: cfg.nome }
}

async function salvarConfig() {
  salvando.value = true
  try {
    const body = { funcionario_id: formConfig.value.funcionarioId, nome: formConfig.value.nome }
    if (formConfig.value.editandoId) {
      const updated = await apiFetch(`/planilhas/configs/${formConfig.value.editandoId}`, {
        method: 'PUT', body: JSON.stringify(body),
      })
      const idx = configs.value.findIndex(c => c.id === updated.id)
      if (idx >= 0) configs.value[idx] = updated
      if (configParaColunas.value?.id === updated.id) configParaColunas.value = updated
    } else {
      const created = await apiFetch('/planilhas/configs', { method: 'POST', body: JSON.stringify(body) })
      configs.value.push(created)
      configParaColunas.value = created
    }
    formConfig.value.aberto = false
    mostrarSnack('Planilha salva')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

function confirmarDeleteConfig(cfg) {
  confirmDialog.value = {
    show: true,
    msg: `Excluir a planilha de ${cfg.funcionario_nome} e todos os seus dados?`,
    action: () => deletarConfig(cfg),
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
      periodoAtual.value = null
    }
    if (configParaColunas.value?.id === cfg.id) configParaColunas.value = null
    confirmDialog.value.show = false
    mostrarSnack('Planilha excluída')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

// ── Colunas ───────────────────────────────────────────────────────────────────
function abrirNovaColuna() {
  formColuna.value = {
    aberto: true, editandoId: null, nome: '', tipo: 'texto',
    prazo_dias: null, ordem: configParaColunas.value?.colunas.length ?? 0,
  }
}

function selecionarColunaParaEditar(col) {
  formColuna.value = {
    aberto: true, editandoId: col.id, nome: col.nome, tipo: col.tipo,
    prazo_dias: col.prazo_dias, ordem: col.ordem,
  }
}

async function salvarColuna() {
  if (!configParaColunas.value) return
  salvando.value = true
  try {
    const body = {
      nome: formColuna.value.nome,
      tipo: formColuna.value.tipo,
      ordem: formColuna.value.ordem,
      prazo_dias: formColuna.value.prazo_dias || null,
      obrigatorio: true,
    }
    if (formColuna.value.editandoId) {
      const updated = await apiFetch(`/planilhas/colunas/${formColuna.value.editandoId}`, {
        method: 'PUT', body: JSON.stringify(body),
      })
      const idx = configParaColunas.value.colunas.findIndex(c => c.id === updated.id)
      if (idx >= 0) configParaColunas.value.colunas[idx] = updated
    } else {
      const created = await apiFetch(`/planilhas/configs/${configParaColunas.value.id}/colunas`, {
        method: 'POST', body: JSON.stringify(body),
      })
      configParaColunas.value.colunas.push(created)
    }
    // atualiza a config no array global também
    const gIdx = configs.value.findIndex(c => c.id === configParaColunas.value.id)
    if (gIdx >= 0) configs.value[gIdx] = { ...configParaColunas.value }
    formColuna.value.aberto = false
    mostrarSnack('Coluna salva')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

function confirmarDeleteColuna(col) {
  confirmDialog.value = {
    show: true,
    msg: `Excluir a coluna "${col.nome}" e todos os seus dados?`,
    action: () => deletarColuna(col),
  }
}

async function deletarColuna(col) {
  salvando.value = true
  try {
    await apiFetch(`/planilhas/colunas/${col.id}`, { method: 'DELETE' })
    configParaColunas.value.colunas = configParaColunas.value.colunas.filter(c => c.id !== col.id)
    confirmDialog.value.show = false
    mostrarSnack('Coluna excluída')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

onMounted(carregarDados)
</script>

<style scoped>
/* ── Legenda ── */
.legenda-item {
  display: flex;
  align-items: center;
  gap: 6px;
}
.legenda-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

/* ── Tabela ── */
.planilha-wrapper {
  border: 1px solid rgba(128, 128, 128, 0.2);
  border-radius: 8px;
  overflow: hidden;
}
.planilha-scroll {
  overflow-x: auto;
}
.planilha-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 600px;
}

/* Cabeçalho */
.planilha-table thead tr {
  background: rgba(128, 128, 128, 0.06);
}
.planilha-table th {
  padding: 10px 14px;
  text-align: left;
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid rgba(128, 128, 128, 0.15);
  white-space: nowrap;
}
.col-header-inner {
  display: flex;
  align-items: center;
}
.col-acoes {
  width: 48px;
  text-align: center;
}

/* Sticky primeira coluna */
.sticky-col {
  position: sticky;
  left: 0;
  z-index: 2;
  background: inherit;
  min-width: 160px;
  max-width: 220px;
}
thead .sticky-col {
  background: rgba(128, 128, 128, 0.06) !important;
  z-index: 3;
}

/* Linhas */
.planilha-row td {
  border-bottom: 1px solid rgba(128, 128, 128, 0.1);
}
.planilha-row:last-child td {
  border-bottom: none;
}
.planilha-row:hover td {
  background: rgba(128, 128, 128, 0.04);
}

/* Células */
.col-celula {
  padding: 0;
  cursor: pointer;
  transition: background 0.15s;
}
.col-celula:hover {
  filter: brightness(0.96);
}
.celula-inner {
  padding: 10px 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 44px;
  min-width: 90px;
}
.celula-valor {
  font-size: 13px;
  font-weight: 500;
}
.celula-vazia {
  font-size: 13px;
  color: rgba(128, 128, 128, 0.5);
}
.label-text {
  font-size: 13px;
  font-weight: 500;
}

/* Status colors */
.status-success {
  background: rgba(76, 175, 80, 0.15) !important;
}
.status-error {
  background: rgba(244, 67, 54, 0.15) !important;
}
.status-warning {
  background: rgba(255, 152, 0, 0.15) !important;
}
.status-pending {
  background: rgba(128, 128, 128, 0.06) !important;
}

/* Theme: dark mode adjustments */
.v-theme--pratikaDark .planilha-wrapper {
  border-color: rgba(255, 255, 255, 0.1);
}
.v-theme--pratikaDark .planilha-table thead tr {
  background: rgba(255, 255, 255, 0.04);
}
.v-theme--pratikaDark thead .sticky-col {
  background: rgba(255, 255, 255, 0.04) !important;
}
.v-theme--pratikaDark .planilha-row td {
  border-bottom-color: rgba(255, 255, 255, 0.06);
}
.v-theme--pratikaDark .planilha-row:hover td {
  background: rgba(255, 255, 255, 0.03);
}
</style>
