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
        <v-btn v-if="isAdmin" color="primary" variant="tonal" prepend-icon="mdi-cog-outline"
          @click="abrirGerenciar">
          Gerenciar
        </v-btn>
      </div>
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

    <!-- ── Alertas de estado ── -->
    <v-alert v-if="!carregando && !configAtual && !isAdmin" type="info" variant="tonal" class="mb-4">
      Você ainda não possui uma planilha configurada. Contate o administrador.
    </v-alert>
    <v-alert v-if="!carregando && isAdmin && configs.length === 0" type="info" variant="tonal" class="mb-4">
      Nenhuma planilha configurada. Clique em "Gerenciar" para criar.
    </v-alert>

    <!-- ── Dashboard ── -->
    <template v-if="configAtual">

      <!-- Seletor de aba + botão atualizar -->
      <div class="d-flex align-center flex-wrap gap-3 mb-4">
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
          @update:model-value="carregarDados"
        />
        <v-btn icon variant="tonal" size="small" :loading="carregandoDados" @click="carregarDados">
          <v-icon>mdi-refresh</v-icon>
        </v-btn>
        <span v-if="dadosSheet?.atualizado_em" class="text-caption text-medium-emphasis">
          Atualizado: {{ dadosSheet.atualizado_em }}
        </span>
      </div>

      <!-- Legenda -->
      <div class="d-flex gap-4 mb-4 flex-wrap">
        <div v-for="l in legenda" :key="l.label" class="d-flex align-center gap-2">
          <div class="legenda-dot" :style="`background:${l.cor}`"></div>
          <span class="text-caption text-medium-emphasis">{{ l.label }}</span>
        </div>
      </div>

      <!-- Tabela -->
      <div v-if="dadosSheet && !carregandoDados" class="planilha-wrapper">
        <div class="planilha-scroll">
          <table class="planilha-table">
            <thead>
              <tr>
                <th class="col-label sticky-col">Item</th>
                <th v-for="col in dadosSheet.colunas" :key="col" class="col-header">
                  <div>{{ col }}</div>
                  <div v-if="regraMap[col]" class="text-caption font-weight-regular" style="opacity:.7">
                    {{ tipoLabel(regraMap[col].tipo) }}
                    <span v-if="regraMap[col].prazo_dias"> · {{ regraMap[col].prazo_dias }}d</span>
                  </div>
                </th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="dadosSheet.linhas.length === 0">
                <td :colspan="dadosSheet.colunas.length + 1" class="text-center text-medium-emphasis py-8">
                  Nenhum dado encontrado nesta aba.
                </td>
              </tr>
              <tr v-for="(linha, li) in dadosSheet.linhas" :key="li" class="planilha-row">
                <td class="col-label sticky-col">
                  <span class="label-text">{{ linha.label }}</span>
                </td>
                <td
                  v-for="(celula, ci) in linha.celulas"
                  :key="ci"
                  class="col-celula"
                  :class="`status-${celula.status}`"
                >
                  <div class="celula-inner">
                    <template v-if="regraMap[dadosSheet.colunas[ci]]?.tipo === 'booleano'">
                      <v-icon
                        :color="isCelulaPreenchida(celula.valor) ? 'success' : 'grey-lighten-1'"
                        size="20"
                      >
                        {{ isCelulaPreenchida(celula.valor) ? 'mdi-check-circle' : 'mdi-circle-outline' }}
                      </v-icon>
                    </template>
                    <span v-else-if="celula.valor" class="celula-valor">{{ celula.valor }}</span>
                    <span v-else class="celula-vazia">—</span>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <div v-if="carregandoDados" class="d-flex justify-center py-12">
        <v-progress-circular indeterminate color="primary" />
      </div>

      <v-alert
        v-if="!carregandoDados && !dadosSheet && abaSelecionada"
        type="warning" variant="tonal" class="mt-4"
      >
        Não foi possível carregar os dados desta aba.
      </v-alert>

    </template>

    <!-- ════════════════════════════════════════════════════════════════════ -->
    <!-- Dialog: gerenciar configs + regras (admin)                          -->
    <!-- ════════════════════════════════════════════════════════════════════ -->
    <v-dialog v-model="dialogGerenciar" max-width="780" scrollable>
      <v-card>
        <v-card-title class="pa-4 pb-2 d-flex align-center justify-space-between">
          <span class="text-subtitle-1 font-weight-medium">Gerenciar Planilhas</span>
          <v-btn icon variant="text" @click="dialogGerenciar = false">
            <v-icon>mdi-close</v-icon>
          </v-btn>
        </v-card-title>
        <v-divider />
        <v-card-text class="pa-4" style="max-height:75vh">

          <!-- Lista configs -->
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
              <v-list-item :subtitle="cfg.spreadsheet_id || 'Sem planilha vinculada'"
                :class="{ 'bg-blue-lighten-5': configEditando?.id === cfg.id }">
                <template #title>{{ cfg.funcionario_nome }} — {{ cfg.nome }}</template>
                <template #append>
                  <v-btn icon size="x-small" variant="text" @click="abrirFormConfig(cfg)">
                    <v-icon size="16">mdi-pencil-outline</v-icon>
                  </v-btn>
                  <v-btn icon size="x-small" variant="text" color="error" @click="confirmar(
                    `Excluir planilha de ${cfg.funcionario_nome}?`, () => deletarConfig(cfg))">
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
              <div class="text-subtitle-2 mb-3">
                {{ formConfig.id ? 'Editar planilha' : 'Nova planilha' }}
              </div>
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
                    label="Nome da planilha"
                    variant="outlined"
                    density="comfortable"
                  />
                </v-col>
                <v-col cols="12">
                  <v-text-field
                    v-model="formConfig.spreadsheet_id"
                    label="ID do Google Sheets (da URL)"
                    variant="outlined"
                    density="comfortable"
                    hint="Ex: 1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="4">
                  <v-text-field
                    v-model.number="formConfig.linha_cabecalho"
                    label="Linha do cabeçalho"
                    type="number"
                    variant="outlined"
                    density="comfortable"
                    hint="Qual linha tem os títulos das colunas"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="4">
                  <v-text-field
                    v-model.number="formConfig.linha_dados_inicio"
                    label="Início dos dados"
                    type="number"
                    variant="outlined"
                    density="comfortable"
                    hint="Primeira linha com dados reais"
                    persistent-hint
                  />
                </v-col>
                <v-col cols="4">
                  <v-text-field
                    v-model.number="formConfig.coluna_label_indice"
                    label="Coluna do rótulo (0=A)"
                    type="number"
                    variant="outlined"
                    density="comfortable"
                    hint="Índice da coluna com nomes dos itens"
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

          <!-- Regras de cor da config selecionada -->
          <template v-if="configEditando">
            <v-divider class="my-4" />
            <div class="d-flex align-center justify-space-between mb-3">
              <div>
                <span class="text-subtitle-2">Regras de cor</span>
                <div class="text-caption text-medium-emphasis">
                  Defina prazo (dias) para cada coluna da planilha de {{ configEditando.funcionario_nome }}
                </div>
              </div>
              <v-btn size="small" color="secondary" variant="tonal" prepend-icon="mdi-plus"
                @click="abrirFormRegra()">
                Nova regra
              </v-btn>
            </div>

            <v-list v-if="configEditando.regras.length" lines="two" class="rounded border mb-3">
              <template v-for="(regra, ri) in configEditando.regras" :key="regra.id">
                <v-divider v-if="ri > 0" />
                <v-list-item>
                  <template #title>{{ regra.coluna_nome }}</template>
                  <template #subtitle>
                    {{ tipoLabel(regra.tipo) }}
                    <span v-if="regra.prazo_dias"> · Prazo: {{ regra.prazo_dias }} dias após início do mês</span>
                    <span v-else> · Sem prazo (apenas exibição)</span>
                  </template>
                  <template #append>
                    <v-btn icon size="x-small" variant="text" @click="abrirFormRegra(regra)">
                      <v-icon size="16">mdi-pencil-outline</v-icon>
                    </v-btn>
                    <v-btn icon size="x-small" variant="text" color="error"
                      @click="confirmar(`Excluir regra "${regra.coluna_nome}"?`, () => deletarRegra(regra))">
                      <v-icon size="16">mdi-delete-outline</v-icon>
                    </v-btn>
                  </template>
                </v-list-item>
              </template>
            </v-list>
            <v-alert v-else type="info" variant="tonal" density="compact" class="mb-3">
              Nenhuma regra. Sem regras, todas as células ficam sem cor.
            </v-alert>

            <!-- Form regra -->
            <v-expand-transition>
              <div v-if="formRegra.aberto">
                <v-row dense class="mt-1">
                  <v-col cols="12" md="4">
                    <v-text-field
                      v-model="formRegra.coluna_nome"
                      label="Nome da coluna (igual ao cabeçalho)"
                      variant="outlined"
                      density="comfortable"
                    />
                  </v-col>
                  <v-col cols="6" md="3">
                    <v-select
                      v-model="formRegra.tipo"
                      :items="tiposColuna"
                      item-title="label"
                      item-value="value"
                      label="Tipo"
                      variant="outlined"
                      density="comfortable"
                    />
                  </v-col>
                  <v-col cols="6" md="3">
                    <v-text-field
                      v-model.number="formRegra.prazo_dias"
                      label="Prazo (dias)"
                      type="number"
                      variant="outlined"
                      density="comfortable"
                      hint="Dias após 1º do mês"
                      persistent-hint
                    />
                  </v-col>
                  <v-col cols="12" md="2" class="d-flex align-center justify-end gap-2">
                    <v-btn variant="text" size="small" @click="formRegra.aberto = false">
                      Cancelar
                    </v-btn>
                    <v-btn color="primary" variant="tonal" size="small" @click="salvarRegra"
                      :loading="salvando" :disabled="!formRegra.coluna_nome">
                      {{ formRegra.id ? 'Atualizar' : 'Criar' }}
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

    <!-- ── Confirm dialog ── -->
    <v-dialog v-model="confirmDlg.show" max-width="340">
      <v-card>
        <v-card-text class="pa-5">{{ confirmDlg.msg }}</v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="confirmDlg.show = false">Cancelar</v-btn>
          <v-btn color="error" variant="tonal" @click="confirmDlg.action" :loading="salvando">
            Confirmar
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

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

const configs            = ref([])
const usuarios           = ref([])
const configSelecionadaId = ref(null)
const configAtual        = ref(null)
const configEditando     = ref(null)   // config aberta no gerenciador

const abas           = ref([])
const abaSelecionada = ref(null)
const dadosSheet     = ref(null)

const dialogGerenciar = ref(false)

const formConfig = ref({
  aberto: false, id: null, funcionario_id: null, nome: '',
  spreadsheet_id: '', linha_cabecalho: 1, linha_dados_inicio: 2, coluna_label_indice: 0,
})
const formRegra = ref({ aberto: false, id: null, coluna_nome: '', tipo: 'texto', prazo_dias: null })

const snack     = ref({ show: false, color: 'success', msg: '' })
const confirmDlg = ref({ show: false, msg: '', action: null })

const tiposColuna = [
  { label: 'Texto', value: 'texto' },
  { label: 'Data', value: 'data' },
  { label: 'Booleano (Sim/Não)', value: 'booleano' },
]

const legenda = [
  { label: 'Concluído', cor: '#4caf50' },
  { label: 'Atrasado', cor: '#f44336' },
  { label: 'Vence em breve', cor: '#ff9800' },
  { label: 'Pendente / Sem prazo', cor: 'rgba(128,128,128,0.15)' },
]

// ── Computed ──────────────────────────────────────────────────────────────────
const regraMap = computed(() => {
  if (!configAtual.value) return {}
  return Object.fromEntries(configAtual.value.regras.map(r => [r.coluna_nome, r]))
})

// ── Helpers ───────────────────────────────────────────────────────────────────
const tipoLabel = (t) => ({ texto: 'Texto', data: 'Data', booleano: 'Sim/Não' }[t] || t)

const isCelulaPreenchida = (v) =>
  Boolean(v && v.trim() && !['0', 'none', ''].includes(v.trim().toLowerCase()))

function mostrarSnack(msg, color = 'success') {
  snack.value = { show: true, color, msg }
}

function confirmar(msg, action) {
  confirmDlg.value = { show: true, msg, action: async () => { await action(); confirmDlg.value.show = false } }
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
        const cfg = await apiFetch('/planilhas/minha')
        configAtual.value = cfg
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
  dadosSheet.value = null
  if (configAtual.value) await carregarAbas()
}

async function carregarAbas() {
  if (!configAtual.value?.spreadsheet_id) return
  carregandoAbas.value = true
  try {
    abas.value = await apiFetch(`/planilhas/configs/${configAtual.value.id}/abas`)
    if (abas.value.length && !abaSelecionada.value) {
      abaSelecionada.value = abas.value[0].title
      await carregarDados()
    }
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    carregandoAbas.value = false
  }
}

async function carregarDados() {
  if (!configAtual.value || !abaSelecionada.value) return
  carregandoDados.value = true
  dadosSheet.value = null
  try {
    dadosSheet.value = await apiFetch(
      `/planilhas/configs/${configAtual.value.id}/dados?aba=${encodeURIComponent(abaSelecionada.value)}`
    )
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    carregandoDados.value = false
  }
}

// ── Gerenciar configs ─────────────────────────────────────────────────────────
async function abrirGerenciar() {
  if (!usuarios.value.length) {
    usuarios.value = await apiFetch('/planilhas/usuarios').catch(() => [])
  }
  configEditando.value = null
  formConfig.value.aberto = false
  formRegra.value.aberto = false
  dialogGerenciar.value = true
}

function abrirFormConfig(cfg = null) {
  configEditando.value = cfg || null
  formConfig.value = cfg
    ? {
        aberto: true, id: cfg.id, funcionario_id: cfg.funcionario_id, nome: cfg.nome,
        spreadsheet_id: cfg.spreadsheet_id, linha_cabecalho: cfg.linha_cabecalho,
        linha_dados_inicio: cfg.linha_dados_inicio, coluna_label_indice: cfg.coluna_label_indice,
      }
    : {
        aberto: true, id: null, funcionario_id: null, nome: '',
        spreadsheet_id: '', linha_cabecalho: 1, linha_dados_inicio: 2, coluna_label_indice: 0,
      }
  formRegra.value.aberto = false
}

async function salvarConfig() {
  salvando.value = true
  try {
    const body = {
      funcionario_id: formConfig.value.funcionario_id,
      nome: formConfig.value.nome,
      spreadsheet_id: formConfig.value.spreadsheet_id,
      linha_cabecalho: formConfig.value.linha_cabecalho,
      linha_dados_inicio: formConfig.value.linha_dados_inicio,
      coluna_label_indice: formConfig.value.coluna_label_indice,
    }
    if (formConfig.value.id) {
      const updated = await apiFetch(`/planilhas/configs/${formConfig.value.id}`, {
        method: 'PUT', body: JSON.stringify(body),
      })
      const idx = configs.value.findIndex(c => c.id === updated.id)
      if (idx >= 0) configs.value[idx] = updated
      configEditando.value = updated
    } else {
      const created = await apiFetch('/planilhas/configs', { method: 'POST', body: JSON.stringify(body) })
      configs.value.push(created)
      configEditando.value = created
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
      dadosSheet.value = null
    }
    if (configEditando.value?.id === cfg.id) configEditando.value = null
    mostrarSnack('Planilha excluída')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

// ── Regras de cor ─────────────────────────────────────────────────────────────
function abrirFormRegra(regra = null) {
  formRegra.value = regra
    ? { aberto: true, id: regra.id, coluna_nome: regra.coluna_nome, tipo: regra.tipo, prazo_dias: regra.prazo_dias }
    : { aberto: true, id: null, coluna_nome: '', tipo: 'texto', prazo_dias: null }
}

async function salvarRegra() {
  if (!configEditando.value) return
  salvando.value = true
  try {
    const body = {
      coluna_nome: formRegra.value.coluna_nome,
      tipo: formRegra.value.tipo,
      prazo_dias: formRegra.value.prazo_dias || null,
    }
    if (formRegra.value.id) {
      const updated = await apiFetch(`/planilhas/regras/${formRegra.value.id}`, {
        method: 'PUT', body: JSON.stringify(body),
      })
      const idx = configEditando.value.regras.findIndex(r => r.id === updated.id)
      if (idx >= 0) configEditando.value.regras[idx] = updated
    } else {
      const created = await apiFetch(`/planilhas/configs/${configEditando.value.id}/regras`, {
        method: 'POST', body: JSON.stringify(body),
      })
      configEditando.value.regras.push(created)
    }
    // Sincroniza com configs global
    const gi = configs.value.findIndex(c => c.id === configEditando.value.id)
    if (gi >= 0) configs.value[gi] = { ...configEditando.value }
    // Sincroniza com configAtual se for o mesmo
    if (configAtual.value?.id === configEditando.value.id) {
      configAtual.value = { ...configEditando.value }
    }
    formRegra.value.aberto = false
    mostrarSnack('Regra salva')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

async function deletarRegra(regra) {
  salvando.value = true
  try {
    await apiFetch(`/planilhas/regras/${regra.id}`, { method: 'DELETE' })
    configEditando.value.regras = configEditando.value.regras.filter(r => r.id !== regra.id)
    const gi = configs.value.findIndex(c => c.id === configEditando.value.id)
    if (gi >= 0) configs.value[gi] = { ...configEditando.value }
    if (configAtual.value?.id === configEditando.value.id) {
      configAtual.value = { ...configEditando.value }
    }
    mostrarSnack('Regra excluída')
  } catch (e) {
    mostrarSnack(e.message, 'error')
  } finally {
    salvando.value = false
  }
}

onMounted(init)
</script>

<style scoped>
.legenda-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
  flex-shrink: 0;
}

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
  min-width: 500px;
}
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
.col-header {
  min-width: 100px;
}
.sticky-col {
  position: sticky;
  left: 0;
  z-index: 2;
  background: inherit;
  min-width: 150px;
  max-width: 220px;
}
thead .sticky-col {
  background: rgba(128, 128, 128, 0.06) !important;
  z-index: 3;
}
.planilha-row td {
  border-bottom: 1px solid rgba(128, 128, 128, 0.1);
}
.planilha-row:last-child td { border-bottom: none; }
.planilha-row:hover td { background: rgba(128, 128, 128, 0.03); }

.col-celula { padding: 0; }
.celula-inner {
  padding: 9px 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 42px;
  min-width: 90px;
}
.celula-valor { font-size: 13px; font-weight: 500; }
.celula-vazia { font-size: 13px; color: rgba(128,128,128,0.4); }
.label-text { font-size: 13px; font-weight: 500; }

/* Status colors */
.status-success { background: rgba(76, 175, 80, 0.15) !important; }
.status-error   { background: rgba(244, 67, 54, 0.15) !important; }
.status-warning { background: rgba(255, 152, 0, 0.15) !important; }
.status-pending { background: rgba(128, 128, 128, 0.06) !important; }
.status-none    { background: transparent; }

.v-theme--pratikaDark .planilha-wrapper { border-color: rgba(255,255,255,0.1); }
.v-theme--pratikaDark .planilha-table thead tr { background: rgba(255,255,255,0.04); }
.v-theme--pratikaDark thead .sticky-col { background: rgba(255,255,255,0.04) !important; }
.v-theme--pratikaDark .planilha-row td { border-bottom-color: rgba(255,255,255,0.06); }
</style>
