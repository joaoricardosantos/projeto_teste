<template>
  <div>
    <!-- Header -->
    <div class="d-flex align-center mb-6">
      <div class="page-icon">
        <v-icon color="white" size="22">mdi-gavel</v-icon>
      </div>
      <div>
        <h1 class="page-title">Juridico</h1>
        <p class="page-subtitle">Dashboard e planilhas dos advogados</p>
      </div>
    </div>

    <!-- Tabs -->
    <v-tabs v-model="tabAtiva" color="success" class="mb-6">
      <v-tab value="dashboard">Dashboard Geral</v-tab>
      <v-tab value="advogados">Advogados</v-tab>
    </v-tabs>

    <!-- ═══════════════════ TAB DASHBOARD ═══════════════════ -->
    <div v-if="tabAtiva === 'dashboard'">
      <div v-if="loadingDash" class="text-center py-10">
        <v-progress-circular indeterminate color="success" size="48" />
        <div class="mt-3" style="opacity:0.5">Carregando dashboard...</div>
      </div>

      <v-alert v-else-if="erroDash" type="error" variant="tonal" density="compact" class="mb-4">
        {{ erroDash }}
      </v-alert>

      <template v-else-if="dash">
        <!-- KPI Cards -->
        <v-row class="mb-6">
          <v-col cols="12" sm="6" md="3">
            <v-card class="kpi-card" elevation="1">
              <v-card-text class="d-flex align-center" style="gap:14px">
                <div class="kpi-icon" style="background: linear-gradient(135deg, #34d399, #059669)">
                  <v-icon color="white" size="22">mdi-currency-brl</v-icon>
                </div>
                <div>
                  <div class="kpi-value">{{ formatarMoeda(dash.resumo.total_geral) }}</div>
                  <div class="kpi-label">Total em Dividas</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card class="kpi-card" elevation="1">
              <v-card-text class="d-flex align-center" style="gap:14px">
                <div class="kpi-icon" style="background: linear-gradient(135deg, #60a5fa, #3b82f6)">
                  <v-icon color="white" size="22">mdi-file-document-outline</v-icon>
                </div>
                <div>
                  <div class="kpi-value">{{ dash.resumo.total_processos }}</div>
                  <div class="kpi-label">Total de Processos</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card class="kpi-card" elevation="1">
              <v-card-text class="d-flex align-center" style="gap:14px">
                <div class="kpi-icon" style="background: linear-gradient(135deg, #f59e0b, #d97706)">
                  <v-icon color="white" size="22">mdi-scale-balance</v-icon>
                </div>
                <div>
                  <div class="kpi-value">{{ dash.resumo.com_processo }}</div>
                  <div class="kpi-label">Ajuizados</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="3">
            <v-card class="kpi-card" elevation="1">
              <v-card-text class="d-flex align-center" style="gap:14px">
                <div class="kpi-icon" style="background: linear-gradient(135deg, #f87171, #ef4444)">
                  <v-icon color="white" size="22">mdi-alert-circle-outline</v-icon>
                </div>
                <div>
                  <div class="kpi-value">{{ dash.resumo.sem_processo }}</div>
                  <div class="kpi-label">Sem Processo</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- KPI linha 2 -->
        <v-row class="mb-6">
          <v-col cols="12" sm="6" md="4">
            <v-card class="kpi-card" elevation="1">
              <v-card-text class="d-flex align-center" style="gap:14px">
                <div class="kpi-icon" style="background: linear-gradient(135deg, #a78bfa, #7c3aed)">
                  <v-icon color="white" size="22">mdi-domain</v-icon>
                </div>
                <div>
                  <div class="kpi-value">{{ dash.resumo.total_condominios }}</div>
                  <div class="kpi-label">Condominios</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="4">
            <v-card class="kpi-card" elevation="1">
              <v-card-text class="d-flex align-center" style="gap:14px">
                <div class="kpi-icon" style="background: linear-gradient(135deg, #2dd4bf, #14b8a6)">
                  <v-icon color="white" size="22">mdi-account-group</v-icon>
                </div>
                <div>
                  <div class="kpi-value">{{ dash.resumo.total_advogados }}</div>
                  <div class="kpi-label">Advogados</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
          <v-col cols="12" sm="6" md="4">
            <v-card class="kpi-card" elevation="1">
              <v-card-text class="d-flex align-center" style="gap:14px">
                <div class="kpi-icon" style="background: linear-gradient(135deg, #fb923c, #f97316)">
                  <v-icon color="white" size="22">mdi-lightning-bolt</v-icon>
                </div>
                <div>
                  <div class="kpi-value">{{ dash.resumo.movimentou_semana }}</div>
                  <div class="kpi-label">Movimentaram na Semana</div>
                </div>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>

        <!-- Por Advogado -->
        <v-card class="section-card mb-6" elevation="1">
          <div class="section-header d-flex align-center" style="gap:12px">
            <v-avatar class="section-badge" size="32">
              <v-icon size="16">mdi-account-tie</v-icon>
            </v-avatar>
            <div>
              <div class="section-title font-weight-bold" style="font-size:0.95rem">Por Advogado</div>
              <div class="section-subtitle" style="font-size:0.78rem">Distribuicao de processos e valores</div>
            </div>
          </div>
          <v-card-text>
            <v-row>
              <v-col v-for="adv in dash.por_advogado" :key="adv.nome" cols="12" sm="6" md="3">
                <v-card variant="outlined" class="adv-dash-card">
                  <v-card-text>
                    <div class="d-flex align-center mb-3" style="gap:10px">
                      <v-avatar size="36" color="success" variant="tonal">
                        <span class="font-weight-bold" style="font-size:13px">{{ iniciais(adv.nome) }}</span>
                      </v-avatar>
                      <div class="font-weight-bold" style="font-size:0.95rem">{{ adv.nome }}</div>
                    </div>
                    <div class="d-flex flex-column" style="gap:6px">
                      <div class="d-flex justify-space-between">
                        <span class="text-caption" style="opacity:0.6">Total divida</span>
                        <span class="font-weight-bold" style="font-size:0.85rem; color:#059669">{{ formatarMoeda(adv.total) }}</span>
                      </div>
                      <div class="d-flex justify-space-between">
                        <span class="text-caption" style="opacity:0.6">Processos</span>
                        <span class="font-weight-bold" style="font-size:0.85rem">{{ adv.processos }}</span>
                      </div>
                      <div class="d-flex justify-space-between">
                        <span class="text-caption" style="opacity:0.6">Ajuizados</span>
                        <v-chip size="x-small" color="info" variant="tonal">{{ adv.com_processo }}</v-chip>
                      </div>
                      <div class="d-flex justify-space-between">
                        <span class="text-caption" style="opacity:0.6">Sem processo</span>
                        <v-chip size="x-small" color="warning" variant="tonal">{{ adv.sem_processo }}</v-chip>
                      </div>
                      <div class="d-flex justify-space-between">
                        <span class="text-caption" style="opacity:0.6">Mov. semana</span>
                        <v-chip size="x-small" :color="adv.movimentou > 0 ? 'success' : 'default'" variant="tonal">{{ adv.movimentou }}</v-chip>
                      </div>
                    </div>
                  </v-card-text>
                </v-card>
              </v-col>
            </v-row>
          </v-card-text>
        </v-card>

        <!-- Por Condomínio -->
        <v-card class="section-card mb-6" elevation="1">
          <div class="section-header d-flex align-center" style="gap:12px">
            <v-avatar class="section-badge" size="32">
              <v-icon size="16">mdi-domain</v-icon>
            </v-avatar>
            <div>
              <div class="section-title font-weight-bold" style="font-size:0.95rem">Por Condominio</div>
              <div class="section-subtitle" style="font-size:0.78rem">Divida e processos por condominio</div>
            </div>
          </div>
          <v-card-text>
            <v-table density="compact" hover>
              <thead>
                <tr>
                  <th style="font-size:0.78rem; font-weight:700">Condominio</th>
                  <th style="font-size:0.78rem; font-weight:700" class="text-center">Processos</th>
                  <th style="font-size:0.78rem; font-weight:700" class="text-end">Total Divida</th>
                  <th style="font-size:0.78rem; font-weight:700; width:40%"></th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="c in dash.por_condominio" :key="c.condominio">
                  <td style="font-size:0.82rem">{{ c.condominio }}</td>
                  <td class="text-center">
                    <v-chip size="x-small" color="info" variant="tonal">{{ c.processos }}</v-chip>
                  </td>
                  <td class="text-end font-weight-bold" style="font-size:0.82rem; color:#059669">{{ formatarMoeda(c.total) }}</td>
                  <td>
                    <div class="barra-container">
                      <div class="barra-fill" :style="{ width: barraWidth(c.total) }"></div>
                    </div>
                  </td>
                </tr>
              </tbody>
            </v-table>
          </v-card-text>
        </v-card>

        <v-row>
          <!-- Por Situação Judicial -->
          <v-col cols="12" md="5">
            <v-card class="section-card" elevation="1" style="height:100%">
              <div class="section-header d-flex align-center" style="gap:12px">
                <v-avatar class="section-badge" size="32">
                  <v-icon size="16">mdi-chart-pie</v-icon>
                </v-avatar>
                <div>
                  <div class="section-title font-weight-bold" style="font-size:0.95rem">Situacao Judicial</div>
                  <div class="section-subtitle" style="font-size:0.78rem">Distribuicao por status</div>
                </div>
              </div>
              <v-card-text>
                <div v-for="s in dash.por_situacao" :key="s.situacao" class="d-flex align-center mb-2" style="gap:10px">
                  <div class="sit-dot" :style="{ background: corSituacao(s.situacao) }"></div>
                  <div style="flex:1; font-size:0.82rem">{{ s.situacao }}</div>
                  <v-chip size="x-small" variant="tonal" :color="corSituacaoChip(s.situacao)">{{ s.quantidade }}</v-chip>
                </div>
              </v-card-text>
            </v-card>
          </v-col>

          <!-- Top Devedores -->
          <v-col cols="12" md="7">
            <v-card class="section-card" elevation="1" style="height:100%">
              <div class="section-header d-flex align-center" style="gap:12px">
                <v-avatar class="section-badge" size="32">
                  <v-icon size="16">mdi-podium</v-icon>
                </v-avatar>
                <div>
                  <div class="section-title font-weight-bold" style="font-size:0.95rem">Maiores Devedores</div>
                  <div class="section-subtitle" style="font-size:0.78rem">Top 20 por valor de divida</div>
                </div>
              </div>
              <v-card-text style="max-height:460px; overflow-y:auto">
                <v-table density="compact" hover>
                  <thead>
                    <tr>
                      <th style="font-size:0.75rem; font-weight:700">#</th>
                      <th style="font-size:0.75rem; font-weight:700">Nome</th>
                      <th style="font-size:0.75rem; font-weight:700">Condominio</th>
                      <th style="font-size:0.75rem; font-weight:700">Advogado</th>
                      <th style="font-size:0.75rem; font-weight:700" class="text-end">Valor</th>
                    </tr>
                  </thead>
                  <tbody>
                    <tr v-for="(d, i) in dash.top_devedores" :key="i">
                      <td style="font-size:0.8rem; opacity:0.5">{{ i + 1 }}</td>
                      <td class="text-no-wrap" style="font-size:0.8rem">{{ d.nome }}</td>
                      <td class="text-no-wrap" style="font-size:0.78rem; opacity:0.7">{{ d.condominio }}</td>
                      <td style="font-size:0.78rem">
                        <v-chip size="x-small" color="success" variant="tonal">{{ d.advogado }}</v-chip>
                      </td>
                      <td class="text-end font-weight-bold text-no-wrap" style="font-size:0.82rem; color:#ef4444">{{ formatarMoeda(d.valor) }}</td>
                    </tr>
                  </tbody>
                </v-table>
              </v-card-text>
            </v-card>
          </v-col>
        </v-row>
      </template>
    </div>

    <!-- ═══════════════════ TAB ADVOGADOS ═══════════════════ -->
    <div v-if="tabAtiva === 'advogados'">
      <!-- Card de cadastro de advogados -->
      <v-card class="section-card mb-6" elevation="1">
        <div class="section-header d-flex align-center" style="gap:12px">
          <v-avatar class="section-badge" size="32">
            <v-icon size="16">mdi-account-tie</v-icon>
          </v-avatar>
          <div>
            <div class="section-title font-weight-bold" style="font-size:0.95rem">Advogados Cadastrados</div>
            <div class="section-subtitle" style="font-size:0.78rem">Gerencie os advogados e suas planilhas</div>
          </div>
          <v-spacer />
          <v-btn color="success" variant="flat" size="small" prepend-icon="mdi-plus" @click="dialogAdv = true">
            Adicionar
          </v-btn>
        </div>

        <v-card-text>
          <v-alert v-if="erroAdvogados" type="error" variant="tonal" density="compact" class="mb-4">
            {{ erroAdvogados }}
          </v-alert>

          <div v-if="loadingAdvogados" class="text-center py-6">
            <v-progress-circular indeterminate color="success" />
          </div>

          <v-row v-else>
            <v-col v-for="adv in advogados" :key="adv.id" cols="12" sm="6" md="3">
              <v-card
                :color="advSelecionado?.id === adv.id ? 'success' : undefined"
                :variant="advSelecionado?.id === adv.id ? 'tonal' : 'outlined'"
                class="adv-card"
                @click="selecionarAdvogado(adv)"
                style="cursor:pointer"
              >
                <v-card-text class="d-flex align-center" style="gap:12px">
                  <v-avatar size="40" color="success" variant="tonal">
                    <span class="font-weight-bold" style="font-size:14px">{{ iniciais(adv.nome) }}</span>
                  </v-avatar>
                  <div style="min-width:0; flex:1">
                    <div class="font-weight-bold text-truncate" style="font-size:0.9rem">{{ adv.nome }}</div>
                    <div class="text-caption" style="opacity:0.6">{{ adv.aba || 'Sem aba definida' }}</div>
                  </div>
                  <v-menu>
                    <template #activator="{ props }">
                      <v-btn v-bind="props" icon variant="text" size="x-small" @click.stop>
                        <v-icon size="18">mdi-dots-vertical</v-icon>
                      </v-btn>
                    </template>
                    <v-list density="compact">
                      <v-list-item @click="abrirEditarAdv(adv)">
                        <template #prepend><v-icon size="16">mdi-pencil</v-icon></template>
                        <v-list-item-title>Editar</v-list-item-title>
                      </v-list-item>
                      <v-list-item @click="confirmarDeletar(adv)">
                        <template #prepend><v-icon size="16" color="error">mdi-delete</v-icon></template>
                        <v-list-item-title class="text-error">Excluir</v-list-item-title>
                      </v-list-item>
                    </v-list>
                  </v-menu>
                </v-card-text>
              </v-card>
            </v-col>
          </v-row>

          <div v-if="!loadingAdvogados && advogados.length === 0" class="text-center py-6" style="opacity:0.5">
            <v-icon size="48" class="mb-2">mdi-account-off-outline</v-icon>
            <div>Nenhum advogado cadastrado</div>
          </div>
        </v-card-text>
      </v-card>

      <!-- Dados da planilha do advogado selecionado -->
      <v-card v-if="advSelecionado" class="section-card" elevation="1">
        <div class="section-header d-flex align-center" style="gap:12px">
          <v-avatar class="section-badge" size="32">
            <v-icon size="16">mdi-google-spreadsheet</v-icon>
          </v-avatar>
          <div>
            <div class="section-title font-weight-bold" style="font-size:0.95rem">{{ advSelecionado.nome }}</div>
            <div class="section-subtitle" style="font-size:0.78rem">Dados da planilha</div>
          </div>
          <v-spacer />

          <v-select
            v-if="abasDisponiveis.length > 0"
            v-model="abaSelecionada"
            :items="abasDisponiveis"
            item-title="title"
            item-value="title"
            label="Aba"
            density="compact"
            variant="outlined"
            hide-details
            style="max-width:220px"
            @update:model-value="carregarDados"
          />

          <v-btn icon variant="text" size="small" @click="carregarDados" :loading="loadingDados">
            <v-icon size="20">mdi-refresh</v-icon>
          </v-btn>
        </div>

        <v-card-text>
          <v-alert v-if="erroDados" type="error" variant="tonal" density="compact" class="mb-4">
            {{ erroDados }}
          </v-alert>

          <div v-if="loadingDados" class="text-center py-8">
            <v-progress-circular indeterminate color="success" />
            <div class="mt-2" style="opacity:0.5; font-size:0.85rem">Carregando planilha...</div>
          </div>

          <template v-else-if="dadosPlanilha">
            <div class="d-flex align-center mb-4" style="gap:8px">
              <v-chip color="success" variant="tonal" size="small" prepend-icon="mdi-table">
                {{ dadosPlanilha.total_linhas }} linhas
              </v-chip>
              <v-chip v-if="dadosPlanilha.aba" variant="tonal" size="small" prepend-icon="mdi-tab">
                {{ dadosPlanilha.aba }}
              </v-chip>
            </div>

            <v-text-field
              v-model="buscaDados"
              placeholder="Buscar na planilha..."
              prepend-inner-icon="mdi-magnify"
              variant="outlined"
              density="compact"
              hide-details
              clearable
              class="mb-4"
              style="max-width:400px"
            />

            <div style="overflow-x:auto">
              <v-table density="compact" hover>
                <thead>
                  <tr>
                    <th
                      v-for="(col, i) in dadosPlanilha.cabecalho"
                      :key="i"
                      class="text-no-wrap col-header"
                      style="font-size:0.78rem; font-weight:700; cursor:pointer; user-select:none"
                      @click="ordenarPor(i)"
                    >
                      {{ col }}
                      <v-icon v-if="sortCol === i" size="14" class="ml-1">
                        {{ sortAsc ? 'mdi-arrow-up' : 'mdi-arrow-down' }}
                      </v-icon>
                    </th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(row, ri) in linhasFiltradas" :key="ri">
                    <td v-for="(cel, ci) in completarLinha(row)" :key="ci" class="text-no-wrap" style="font-size:0.8rem">
                      {{ cel }}
                    </td>
                  </tr>
                </tbody>
              </v-table>
            </div>

            <div v-if="linhasFiltradas.length === 0" class="text-center py-4" style="opacity:0.5; font-size:0.85rem">
              Nenhum resultado encontrado
            </div>
          </template>
        </v-card-text>
      </v-card>
    </div>

    <!-- Dialog adicionar/editar advogado -->
    <v-dialog v-model="dialogAdv" max-width="500" persistent>
      <v-card>
        <v-card-title class="d-flex align-center" style="gap:8px">
          <v-icon color="success">{{ editandoAdv ? 'mdi-pencil' : 'mdi-plus' }}</v-icon>
          {{ editandoAdv ? 'Editar Advogado' : 'Adicionar Advogado' }}
        </v-card-title>
        <v-card-text>
          <v-text-field v-model="formAdv.nome" label="Nome do advogado" variant="outlined" density="compact" class="mb-3" />
          <v-text-field v-model="formAdv.spreadsheet_id" label="ID da planilha Google Sheets" variant="outlined" density="compact" class="mb-3"
            hint="Encontrado na URL da planilha: docs.google.com/spreadsheets/d/ID_AQUI/edit" persistent-hint />
          <v-text-field v-model="formAdv.aba" label="Nome da aba (opcional)" variant="outlined" density="compact"
            hint="Se vazio, usa a primeira aba da planilha" persistent-hint />
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="fecharDialogAdv">Cancelar</v-btn>
          <v-btn color="success" variant="flat" @click="salvarAdvogado" :loading="salvandoAdv">
            {{ editandoAdv ? 'Salvar' : 'Adicionar' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Dialog confirmar exclusao -->
    <v-dialog v-model="dialogDeletar" max-width="400">
      <v-card>
        <v-card-title>Confirmar exclusao</v-card-title>
        <v-card-text>
          Deseja remover o advogado <strong>{{ advParaDeletar?.nome }}</strong>?
        </v-card-text>
        <v-card-actions>
          <v-spacer />
          <v-btn variant="text" @click="dialogDeletar = false">Cancelar</v-btn>
          <v-btn color="error" variant="flat" @click="deletarAdvogado">Excluir</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const API = import.meta.env.VITE_API_URL || ''
const headers = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
  'Content-Type': 'application/json',
})

// ── Estado geral ────────────────────────────────────────────────────────────
const tabAtiva = ref('dashboard')

// ── Dashboard ───────────────────────────────────────────────────────────────
const dash = ref(null)
const loadingDash = ref(false)
const erroDash = ref('')

// ── Advogados ───────────────────────────────────────────────────────────────
const advogados = ref([])
const loadingAdvogados = ref(false)
const erroAdvogados = ref('')

const advSelecionado = ref(null)
const abasDisponiveis = ref([])
const abaSelecionada = ref('')
const dadosPlanilha = ref(null)
const loadingDados = ref(false)
const erroDados = ref('')
const buscaDados = ref('')
const sortCol = ref(null)
const sortAsc = ref(true)

const dialogAdv = ref(false)
const editandoAdv = ref(false)
const salvandoAdv = ref(false)
const formAdv = ref({ nome: '', spreadsheet_id: '', aba: '' })

const dialogDeletar = ref(false)
const advParaDeletar = ref(null)

// ── Computed ────────────────────────────────────────────────────────────────
const linhasFiltradas = computed(() => {
  if (!dadosPlanilha.value?.linhas) return []
  let resultado = dadosPlanilha.value.linhas
  if (buscaDados.value) {
    const b = buscaDados.value.toLowerCase()
    resultado = resultado.filter(row =>
      row.some(cel => String(cel).toLowerCase().includes(b))
    )
  }
  if (sortCol.value !== null) {
    const col = sortCol.value
    const dir = sortAsc.value ? 1 : -1
    resultado = [...resultado].sort((a, b) => {
      const va = String(a[col] ?? '').trim()
      const vb = String(b[col] ?? '').trim()
      const na = parseFloat(va.replace(/[R$\s.]/g, '').replace(',', '.'))
      const nb = parseFloat(vb.replace(/[R$\s.]/g, '').replace(',', '.'))
      if (!isNaN(na) && !isNaN(nb)) return (na - nb) * dir
      return va.localeCompare(vb, 'pt-BR', { sensitivity: 'base' }) * dir
    })
  }
  return resultado
})

// ── Helpers ─────────────────────────────────────────────────────────────────
const formatarMoeda = (v) => {
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: 'BRL' }).format(v || 0)
}

const barraWidth = (valor) => {
  if (!dash.value?.por_condominio?.length) return '0%'
  const max = dash.value.por_condominio[0].total
  return max > 0 ? `${Math.round((valor / max) * 100)}%` : '0%'
}

const corSituacao = (sit) => {
  const s = sit.toLowerCase()
  if (s.includes('despacho')) return '#60a5fa'
  if (s.includes('decisão') || s.includes('decisao')) return '#f59e0b'
  if (s.includes('cumprimento')) return '#34d399'
  if (s.includes('certidão') || s.includes('certidao')) return '#a78bfa'
  if (s.includes('sisbajud')) return '#f87171'
  if (s.includes('prazo')) return '#fb923c'
  return '#94a3b8'
}

const corSituacaoChip = (sit) => {
  const s = sit.toLowerCase()
  if (s.includes('despacho')) return 'info'
  if (s.includes('decisão') || s.includes('decisao')) return 'warning'
  if (s.includes('cumprimento')) return 'success'
  if (s.includes('sisbajud')) return 'error'
  return 'default'
}

const ordenarPor = (col) => {
  if (sortCol.value === col) {
    sortAsc.value = !sortAsc.value
  } else {
    sortCol.value = col
    sortAsc.value = true
  }
}

const iniciais = (nome) => {
  const parts = nome.trim().split(' ')
  return parts.length >= 2
    ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
    : parts[0].slice(0, 2).toUpperCase()
}

const completarLinha = (row) => {
  if (!dadosPlanilha.value?.cabecalho) return row
  const total = dadosPlanilha.value.cabecalho.length
  const result = [...row]
  while (result.length < total) result.push('')
  return result
}

// ── API Dashboard ───────────────────────────────────────────────────────────
const carregarDashboard = async () => {
  loadingDash.value = true
  erroDash.value = ''
  try {
    const res = await fetch(`${API}/api/juridico/dashboard`, { headers: headers() })
    if (!res.ok) throw new Error('Erro ao carregar dashboard')
    dash.value = await res.json()
  } catch (e) {
    erroDash.value = e.message
  } finally {
    loadingDash.value = false
  }
}

// ── API Advogados ───────────────────────────────────────────────────────────
const carregarAdvogados = async () => {
  loadingAdvogados.value = true
  erroAdvogados.value = ''
  try {
    const res = await fetch(`${API}/api/juridico/advogados`, { headers: headers() })
    if (!res.ok) throw new Error('Erro ao carregar advogados')
    advogados.value = await res.json()
  } catch (e) {
    erroAdvogados.value = e.message
  } finally {
    loadingAdvogados.value = false
  }
}

const selecionarAdvogado = async (adv) => {
  advSelecionado.value = adv
  dadosPlanilha.value = null
  erroDados.value = ''
  buscaDados.value = ''
  sortCol.value = null
  sortAsc.value = true

  try {
    const res = await fetch(`${API}/api/juridico/advogados/${adv.id}/abas`, { headers: headers() })
    const data = await res.json()
    abasDisponiveis.value = data.abas || []
    abaSelecionada.value = adv.aba || (abasDisponiveis.value.length > 0 ? abasDisponiveis.value[0].title : '')
  } catch {
    abasDisponiveis.value = []
    abaSelecionada.value = adv.aba || ''
  }

  await carregarDados()
}

const carregarDados = async () => {
  if (!advSelecionado.value) return
  loadingDados.value = true
  erroDados.value = ''
  try {
    const params = abaSelecionada.value ? `?aba=${encodeURIComponent(abaSelecionada.value)}` : ''
    const res = await fetch(`${API}/api/juridico/advogados/${advSelecionado.value.id}/dados${params}`, { headers: headers() })
    const data = await res.json()
    if (data.erro) {
      erroDados.value = data.erro
      dadosPlanilha.value = null
    } else {
      dadosPlanilha.value = data
    }
  } catch (e) {
    erroDados.value = e.message
  } finally {
    loadingDados.value = false
  }
}

const salvarAdvogado = async () => {
  salvandoAdv.value = true
  try {
    const url = editandoAdv.value
      ? `${API}/api/juridico/advogados/${formAdv.value.id}`
      : `${API}/api/juridico/advogados`
    const method = editandoAdv.value ? 'PUT' : 'POST'
    const res = await fetch(url, {
      method,
      headers: headers(),
      body: JSON.stringify({
        nome: formAdv.value.nome,
        spreadsheet_id: formAdv.value.spreadsheet_id,
        aba: formAdv.value.aba,
      }),
    })
    if (!res.ok) throw new Error('Erro ao salvar')
    fecharDialogAdv()
    await carregarAdvogados()
  } catch (e) {
    erroAdvogados.value = e.message
  } finally {
    salvandoAdv.value = false
  }
}

const abrirEditarAdv = (adv) => {
  editandoAdv.value = true
  formAdv.value = { ...adv }
  dialogAdv.value = true
}

const fecharDialogAdv = () => {
  dialogAdv.value = false
  editandoAdv.value = false
  formAdv.value = { nome: '', spreadsheet_id: '', aba: '' }
}

const confirmarDeletar = (adv) => {
  advParaDeletar.value = adv
  dialogDeletar.value = true
}

const deletarAdvogado = async () => {
  try {
    await fetch(`${API}/api/juridico/advogados/${advParaDeletar.value.id}`, {
      method: 'DELETE',
      headers: headers(),
    })
    dialogDeletar.value = false
    if (advSelecionado.value?.id === advParaDeletar.value.id) {
      advSelecionado.value = null
      dadosPlanilha.value = null
    }
    await carregarAdvogados()
  } catch (e) {
    erroAdvogados.value = e.message
  }
}

// ── Lifecycle ───────────────────────────────────────────────────────────────
onMounted(() => {
  carregarDashboard()
  carregarAdvogados()
})
</script>

<style scoped>
.kpi-card {
  border-radius: 14px !important;
  border-left: 3px solid transparent;
}
.kpi-icon {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.kpi-value {
  font-size: 1.15rem;
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.2;
}
.kpi-label {
  font-size: 0.75rem;
  opacity: 0.55;
  margin-top: 1px;
}
.adv-card {
  border-radius: 12px !important;
  transition: all 0.15s ease;
}
.adv-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.1);
}
.adv-dash-card {
  border-radius: 12px !important;
}
.col-header:hover {
  background: rgba(52, 211, 153, 0.08);
}
.barra-container {
  height: 8px;
  background: rgba(0,0,0,0.06);
  border-radius: 4px;
  overflow: hidden;
}
.barra-fill {
  height: 100%;
  background: linear-gradient(90deg, #34d399, #059669);
  border-radius: 4px;
  transition: width 0.4s ease;
}
.sit-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
</style>
