<template>
  <div>
    <!-- ── Cabeçalho ── -->
    <div class="d-flex align-center justify-space-between flex-wrap gap-3 mb-6">
      <div class="d-flex align-center gap-4">
        <div class="page-icon">
          <v-icon size="20" color="white">mdi-calendar-month-outline</v-icon>
        </div>
        <div>
          <h1 class="page-title">Agenda & Insights</h1>
          <p class="page-subtitle">Calendário de tarefas e métricas de inadimplência</p>
        </div>
      </div>
    </div>

    <!-- ── Layout principal: calendário + dashboard ── -->
    <v-row>

      <!-- ════════════════ COLUNA ESQUERDA: CALENDÁRIO ════════════════ -->
      <v-col cols="12" lg="7" xl="8">
        <v-card class="section-card" elevation="3">
          <!-- Header do calendário -->
          <div class="section-header d-flex align-center justify-space-between">
            <div class="d-flex align-center gap-3">
              <div class="section-badge" style="flex-shrink:0;">
                <v-icon size="16" color="white">mdi-calendar</v-icon>
              </div>
              <div style="flex-grow:1;">
                <p class="section-title">{{ mesLabel }}</p>
                <p class="section-subtitle">Clique num dia para ver detalhes</p>
              </div>
            </div>
            <div class="d-flex align-center gap-1">
              <v-btn icon size="small" variant="text" @click="mesAnterior">
                <v-icon>mdi-chevron-left</v-icon>
              </v-btn>
              <v-btn size="x-small" variant="tonal" color="primary" @click="irParaHoje">
                Hoje
              </v-btn>
              <v-btn icon size="small" variant="text" @click="mesProximo">
                <v-icon>mdi-chevron-right</v-icon>
              </v-btn>
            </div>
          </div>
          <v-divider />

          <div class="pa-4">
            <div class="cal-grid-15">
              <div
                v-for="(cel, idx) in diasDoCalendario"
                :key="idx"
                class="cal-cell"
                :class="{
                  'cal-cell--today':    cel.isToday,
                  'cal-cell--selected': cel.dateStr === diaSelecionado,
                  'cal-cell--near':     cel.isNear || cel.dateStr === diaSelecionado,
                }"
                @click="selecionarDia(cel)"
              >
                <!-- Cabeçalho da célula: nome do dia + número -->
                <div class="cal-day-header">
                  <span class="cal-day-name">{{ cel.dayName }}</span>
                  <span class="cal-day-num">{{ cel.day }}</span>
                  <span class="cal-day-mes">{{ cel.mesLabel }}</span>
                </div>

                <div class="cal-events">
                  <template v-for="t in cel.tarefas.slice(0, (cel.isNear || cel.dateStr === diaSelecionado) ? 5 : 2)" :key="t.id">
                    <div class="cal-event" :class="`cal-event--${t.cor}`">
                      <span class="cal-event-title">{{ t.titulo }}</span>
                      <span v-if="(cel.isNear || cel.dateStr === diaSelecionado) && t.descricao" class="cal-event-desc">
                        {{ t.descricao }}
                      </span>
                    </div>
                  </template>
                  <div v-if="cel.tarefas.length > ((cel.isNear || cel.dateStr === diaSelecionado) ? 5 : 2)" class="cal-event-more">
                    +{{ cel.tarefas.length - ((cel.isNear || cel.dateStr === diaSelecionado) ? 5 : 2) }} mais
                  </div>
                </div>

                <v-btn
                  class="cal-add"
                  icon size="x-small" variant="text"
                  @click.stop="abrirNovaTarefa(cel.dateStr)"
                >
                  <v-icon size="13">mdi-plus</v-icon>
                </v-btn>
              </div>
            </div>
          </div>
        </v-card>

        <!-- ── Detalhe do dia selecionado ── -->
        <v-card v-if="diaSelecionado" class="section-card mt-4" elevation="3">
          <div class="section-header d-flex align-center justify-space-between">
            <div class="d-flex align-center gap-3">
              <div class="section-badge" style="flex-shrink:0;">
                <v-icon size="16" color="white">mdi-calendar-check</v-icon>
              </div>
              <div style="flex-grow:1;">
                <p class="section-title">{{ formatarDataLabel(diaSelecionado) }}</p>
                <p class="section-subtitle">{{ tarefasDoDia.length }} tarefa{{ tarefasDoDia.length !== 1 ? 's' : '' }}</p>
              </div>
            </div>
            <div class="d-flex align-center gap-2">
              <v-btn size="small" variant="tonal" color="primary" prepend-icon="mdi-plus"
                @click="abrirNovaTarefa(diaSelecionado)">
                Adicionar
              </v-btn>
              <v-btn icon size="small" variant="text" @click="diaSelecionado = null">
                <v-icon>mdi-close</v-icon>
              </v-btn>
            </div>
          </div>
          <v-divider />

          <div class="pa-4">
            <div v-if="tarefasDoDia.length === 0" class="text-center py-6 text-disabled">
              <v-icon size="40" class="mb-2 opacity-30">mdi-calendar-blank-outline</v-icon>
              <p style="font-size:0.85rem;">Nenhuma tarefa para este dia.</p>
            </div>

            <div v-for="t in tarefasDoDia" :key="t.id" class="tarefa-item mb-3">
              <div class="tarefa-cor" :class="`tarefa-cor--${t.cor}`"></div>
              <div class="tarefa-body">
                <div class="d-flex align-center justify-space-between">
                  <span class="tarefa-titulo">{{ t.titulo }}</span>
                  <div class="d-flex gap-1">
                    <v-btn icon size="x-small" variant="text" @click="abrirEditarTarefa(t)">
                      <v-icon size="14">mdi-pencil-outline</v-icon>
                    </v-btn>
                    <v-btn icon size="x-small" variant="text" color="error" @click="excluirTarefa(t.id)">
                      <v-icon size="14">mdi-delete-outline</v-icon>
                    </v-btn>
                  </div>
                </div>
                <p v-if="t.hora" class="tarefa-hora">
                  <v-icon size="12">mdi-clock-outline</v-icon> {{ t.hora }}
                </p>
                <p v-if="t.descricao" class="tarefa-desc">{{ t.descricao }}</p>
              </div>
            </div>
          </div>
        </v-card>
      </v-col>

      <!-- ════════════════ COLUNA DIREITA: INSIGHTS ════════════════ -->
      <v-col cols="12" lg="5" xl="4">
        <v-card class="section-card" elevation="3">
          <div class="section-header d-flex align-center justify-space-between">
            <div class="d-flex align-center gap-3">
              <div class="section-badge" style="flex-shrink:0; background: linear-gradient(135deg,#6366f1,#8b5cf6);">
                <v-icon size="16" color="white">mdi-chart-line</v-icon>
              </div>
              <div style="flex-grow:1;">
                <p class="section-title">Insights Financeiros</p>
                <p class="section-subtitle">Inadimplência e contas a receber</p>
              </div>
            </div>
            <v-btn icon size="small" variant="text" :loading="loadingInsights" @click="fetchInsights">
              <v-icon size="18">mdi-refresh</v-icon>
            </v-btn>
          </div>
          <v-divider />

          <div class="pa-4">
            <!-- KPIs -->
            <div class="kpi-grid mb-5">
              <div class="kpi-card kpi-red">
                <p class="kpi-label">Inadimplência Total</p>
                <p class="kpi-value">{{ formatBRL(insights.inadimplencia?.total_a_receber || 0) }}</p>
                <p class="kpi-sub">
                  {{ insights.inadimplencia?.total_unidades || 0 }} unidade(s) ·
                  {{ insights.inadimplencia?.total_condominios || 0 }} cond.
                </p>
              </div>
              <div class="kpi-card kpi-orange">
                <p class="kpi-label">Maior Devedor</p>
                <p class="kpi-value" style="font-size:0.82rem;line-height:1.3;">
                  {{ insights.inadimplencia?.maior_condo_nome || '—' }}
                </p>
                <p class="kpi-sub">{{ formatBRL(insights.inadimplencia?.maior_condo_valor || 0) }}</p>
              </div>
              <div class="kpi-card kpi-blue">
                <p class="kpi-label">Demandas a Entregar</p>
                <p class="kpi-value">{{ insights.workflow?.demandas_pendentes ?? '—' }}</p>
                <p class="kpi-sub">pendentes</p>
              </div>
              <div class="kpi-card kpi-purple">
                <p class="kpi-label">Cadernos Pendentes</p>
                <p class="kpi-value">{{ insights.workflow?.cadernos_pendentes ?? '—' }}</p>
                <p class="kpi-sub">pendentes</p>
              </div>
              <div class="kpi-card kpi-teal">
                <p class="kpi-label">Cond. s/ Documentação</p>
                <p class="kpi-value">{{ insights.workflow?.condominios_sem_doc ?? '—' }}</p>
                <p class="kpi-sub">pendentes</p>
              </div>
              <div class="kpi-card kpi-amber">
                <p class="kpi-label">Folhas de Pagamento</p>
                <p class="kpi-value">{{ insights.workflow?.folhas_pendentes ?? '—' }}</p>
                <p class="kpi-sub">pendentes</p>
              </div>
              <div class="kpi-card kpi-green">
                <p class="kpi-label">Prestação de Contas</p>
                <p class="kpi-value">{{ insights.workflow?.prestacao_pendentes ?? '—' }}</p>
                <p class="kpi-sub">pendentes</p>
              </div>
              <div class="kpi-card kpi-indigo">
                <p class="kpi-label">Boletos Gerados</p>
                <p class="kpi-value">{{ insights.workflow?.boletos_gerados ?? '—' }}</p>
                <p class="kpi-sub">gerados</p>
              </div>
            </div>

            <!-- Alertas: Vencendo em 7 dias -->
            <div v-if="insights.despesas?.vencendo_7d?.length" class="mb-4">
              <p class="insight-section-title">
                <v-icon size="15" color="warning" class="mr-1">mdi-clock-alert-outline</v-icon>
                Vencendo em 7 dias
              </p>
              <div v-for="d in insights.despesas.vencendo_7d" :key="d.descricao + d.vencimento"
                class="insight-row">
                <div class="insight-row-dot insight-dot-orange"></div>
                <div style="flex:1; min-width:0;">
                  <p class="insight-row-title">{{ d.descricao }}</p>
                  <p class="insight-row-sub">{{ d.condominio }} · Vence {{ d.vencimento }}</p>
                </div>
                <span class="insight-row-value">{{ formatBRL(d.valor) }}</span>
              </div>
            </div>

            <!-- Alertas: Vencidos -->
            <div v-if="insights.despesas?.vencidos?.length" class="mb-4">
              <p class="insight-section-title">
                <v-icon size="15" color="error" class="mr-1">mdi-alert-circle-outline</v-icon>
                Despesas vencidas
              </p>
              <div v-for="d in insights.despesas.vencidos" :key="d.descricao + d.vencimento"
                class="insight-row">
                <div class="insight-row-dot insight-dot-red"></div>
                <div style="flex:1; min-width:0;">
                  <p class="insight-row-title">{{ d.descricao }}</p>
                  <p class="insight-row-sub">{{ d.condominio }} · Venceu {{ d.vencimento }}</p>
                </div>
                <span class="insight-row-value insight-value-red">{{ formatBRL(d.valor) }}</span>
              </div>
            </div>

            <!-- Top condomínios com despesas pendentes -->
            <div v-if="insights.despesas?.top_condominios?.length" class="mb-4">
              <p class="insight-section-title">
                <v-icon size="15" color="primary" class="mr-1">mdi-office-building-outline</v-icon>
                Maiores despesas pendentes
              </p>
              <div v-for="(c, i) in insights.despesas.top_condominios" :key="c.nome"
                class="insight-row">
                <span class="insight-rank">{{ i + 1 }}</span>
                <div style="flex:1; min-width:0;">
                  <p class="insight-row-title">{{ c.nome || 'Sem nome' }}</p>
                  <p class="insight-row-sub">{{ c.qtd }} despesa{{ c.qtd !== 1 ? 's' : '' }} pendente{{ c.qtd !== 1 ? 's' : '' }}</p>
                </div>
                <span class="insight-row-value">{{ formatBRL(c.total) }}</span>
              </div>
            </div>

            <!-- Top condomínios inadimplentes (do dashboard cache) -->
            <div v-if="insights.inadimplencia?.top_condominios?.length" class="mb-4">
              <p class="insight-section-title">
                <v-icon size="15" color="error" class="mr-1">mdi-domain-remove</v-icon>
                Top inadimplentes (Superlógica)
              </p>
              <div v-for="(c, i) in insights.inadimplencia.top_condominios" :key="c.nome"
                class="insight-row">
                <span class="insight-rank">{{ i + 1 }}</span>
                <div style="flex:1; min-width:0;">
                  <p class="insight-row-title">{{ c.nome }}</p>
                </div>
                <span class="insight-row-value insight-value-red">{{ formatBRL(c.total) }}</span>
              </div>
              <p v-if="insights.inadimplencia.ultima_atualizacao" class="insight-timestamp">
                Dados do dashboard · {{ insights.inadimplencia.ultima_atualizacao }}
              </p>
            </div>

            <!-- Sem dados -->
            <div
              v-if="!loadingInsights && !insights.despesas?.vencendo_7d?.length && !insights.despesas?.vencidos?.length && !insights.inadimplencia?.total_a_receber"
              class="text-center py-6 text-disabled"
            >
              <v-icon size="40" class="mb-2 opacity-30">mdi-chart-line-variant</v-icon>
              <p style="font-size:0.85rem;">Sem dados de inadimplência no momento.</p>
              <p style="font-size:0.75rem; opacity:.5;">Gere o dashboard para carregar métricas.</p>
            </div>

            <v-skeleton-loader v-if="loadingInsights" type="list-item-three-line,list-item-three-line" />
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- ── Dialog: Nova/Editar Tarefa ── -->
    <v-dialog v-model="dialogTarefa" max-width="480" persistent eager>
      <v-card rounded="xl">
        <div class="dialog-header d-flex align-center gap-3">
          <div class="page-icon" style="width:36px;height:36px;border-radius:9px;flex-shrink:0;">
            <v-icon size="18" color="white">{{ formTarefa.id ? 'mdi-pencil-outline' : 'mdi-plus' }}</v-icon>
          </div>
          <div>
            <p style="font-weight:700;font-size:0.95rem;margin:0;">{{ formTarefa.id ? 'Editar Tarefa' : 'Nova Tarefa' }}</p>
            <p style="font-size:0.75rem;opacity:.5;margin:2px 0 0;">{{ formatarDataLabel(formTarefa.data) }}</p>
          </div>
        </div>
        <v-divider />

        <div class="pa-5">
          <v-row>
            <v-col cols="12">
              <v-text-field
                v-model="formTarefa.titulo"
                label="Título *"
                variant="outlined"
                density="comfortable"
                hide-details="auto"
                autofocus
                :rules="[v => !!v || 'Obrigatório']"
              />
            </v-col>
            <v-col cols="12">
              <v-textarea
                v-model="formTarefa.descricao"
                label="Descrição"
                variant="outlined"
                density="comfortable"
                rows="3"
                hide-details
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formTarefa.data"
                label="Data *"
                variant="outlined"
                density="comfortable"
                type="date"
                hide-details
              />
            </v-col>
            <v-col cols="12" sm="6">
              <v-text-field
                v-model="formTarefa.hora"
                label="Hora (opcional)"
                variant="outlined"
                density="comfortable"
                type="time"
                hide-details
              />
            </v-col>
            <v-col cols="12">
              <p style="font-size:0.8rem;opacity:.6;margin-bottom:8px;">Cor</p>
              <div class="d-flex gap-2">
                <div
                  v-for="c in coresDisponiveis"
                  :key="c.value"
                  class="cor-picker"
                  :class="[`cor-picker--${c.value}`, formTarefa.cor === c.value ? 'cor-picker--active' : '']"
                  @click="formTarefa.cor = c.value"
                >
                  <v-icon v-if="formTarefa.cor === c.value" size="14" color="white">mdi-check</v-icon>
                </div>
              </div>
            </v-col>
          </v-row>

          <v-alert v-if="erroTarefa" type="error" density="compact" class="mt-3">{{ erroTarefa }}</v-alert>
        </div>

        <v-divider />
        <div class="d-flex justify-end gap-2 pa-4">
          <v-btn variant="text" color="grey" @click="dialogTarefa = false">Cancelar</v-btn>
          <v-btn color="primary" :loading="salvandoTarefa" @click="salvarTarefa">
            <v-icon start size="16">mdi-content-save-outline</v-icon>
            {{ formTarefa.id ? 'Salvar' : 'Criar' }}
          </v-btn>
        </div>
      </v-card>
    </v-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

// ── Auth ─────────────────────────────────────────────────────────────────────
const authHeader = () => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

// ── Estado do calendário ──────────────────────────────────────────────────────
const inicioRef    = ref((() => { const d = new Date(); d.setHours(0, 0, 0, 0); return d })())
const diaSelecionado = ref(null)   // "YYYY-MM-DD"
const tarefas      = ref([])       // tarefas da janela de 15 dias
const loadingTarefas = ref(false)

const mesLabel = computed(() => {
  const fim = new Date(inicioRef.value)
  fim.setDate(fim.getDate() + 14)
  const opts1 = { day: '2-digit', month: 'short' }
  const opts2 = { day: '2-digit', month: 'short', year: 'numeric' }
  return `${inicioRef.value.toLocaleDateString('pt-BR', opts1)} — ${fim.toLocaleDateString('pt-BR', opts2)}`
})

// Hoje à meia-noite para comparações
const hoje = computed(() => {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  return d
})

// Gera grid de 15 dias a partir de inicioRef
const diasDoCalendario = computed(() => {
  const nomes = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
  const meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
  return Array.from({ length: 15 }, (_, i) => {
    const dt = new Date(inicioRef.value)
    dt.setDate(dt.getDate() + i)
    dt.setHours(0, 0, 0, 0)
    const dateStr = `${dt.getFullYear()}-${String(dt.getMonth() + 1).padStart(2, '0')}-${String(dt.getDate()).padStart(2, '0')}`
    const diff = Math.floor((dt - hoje.value) / 86400000)
    return {
      day:      dt.getDate(),
      dayName:  nomes[dt.getDay()],
      mesLabel: meses[dt.getMonth()],
      dateStr,
      tarefas:  tarefas.value.filter(t => t.data === dateStr),
      isToday:  diff === 0,
      isNear:   diff >= 0 && diff < 5,
    }
  })
})

// Tarefas do dia selecionado
const tarefasDoDia = computed(() =>
  tarefas.value.filter(t => t.data === diaSelecionado.value)
    .sort((a, b) => (a.hora || '').localeCompare(b.hora || ''))
)

// ── Navegação ────────────────────────────────────────────────────────────────
const mesAnterior = () => {
  const d = new Date(inicioRef.value)
  d.setDate(d.getDate() - 15)
  inicioRef.value = d
}
const mesProximo = () => {
  const d = new Date(inicioRef.value)
  d.setDate(d.getDate() + 15)
  inicioRef.value = d
}
const irParaHoje = () => {
  const d = new Date()
  d.setHours(0, 0, 0, 0)
  inicioRef.value = d
  const h = hoje.value
  diaSelecionado.value = `${h.getFullYear()}-${String(h.getMonth() + 1).padStart(2, '0')}-${String(h.getDate()).padStart(2, '0')}`
}

// Recarrega tarefas ao mudar janela
watch(inicioRef, fetchTarefas, { immediate: false })

// ── Seleção de dia ────────────────────────────────────────────────────────────
const selecionarDia = (cel) => {
  diaSelecionado.value = cel.dateStr
}

const formatarDataLabel = (dateStr) => {
  if (!dateStr) return ''
  const [ano, mes, dia] = dateStr.split('-')
  return new Date(Number(ano), Number(mes) - 1, Number(dia))
    .toLocaleDateString('pt-BR', { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' })
    .replace(/^\w/, c => c.toUpperCase())
}

// ── Fetch tarefas ─────────────────────────────────────────────────────────────
async function fetchTarefas() {
  loadingTarefas.value = true
  const inicio = inicioRef.value
  const fim    = new Date(inicio)
  fim.setDate(fim.getDate() + 14)

  const fmt = d => `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`

  try {
    const res = await fetch(
      `/api/agenda/tarefas?data_inicio=${fmt(inicio)}&data_fim=${fmt(fim)}`,
      { headers: authHeader() }
    )
    if (res.ok) tarefas.value = await res.json()
  } catch (_) {}
  loadingTarefas.value = false
}

// ── Dialog Tarefa ─────────────────────────────────────────────────────────────
const dialogTarefa   = ref(false)
const salvandoTarefa = ref(false)
const erroTarefa     = ref('')

const formTarefaVazio = (dateStr = null) => ({
  id:        null,
  titulo:    '',
  descricao: '',
  data:      dateStr || new Date().toISOString().split('T')[0],
  hora:      '',
  cor:       'primary',
})
const formTarefa = ref(formTarefaVazio())

const coresDisponiveis = [
  { value: 'primary', label: 'Azul'    },
  { value: 'success', label: 'Verde'   },
  { value: 'error',   label: 'Vermelho'},
  { value: 'warning', label: 'Laranja' },
  { value: 'info',    label: 'Ciano'   },
]

const abrirNovaTarefa = (dateStr) => {
  erroTarefa.value = ''
  formTarefa.value = formTarefaVazio(dateStr)
  dialogTarefa.value = true
}

const abrirEditarTarefa = (t) => {
  erroTarefa.value = ''
  formTarefa.value = { id: t.id, titulo: t.titulo, descricao: t.descricao, data: t.data, hora: t.hora || '', cor: t.cor }
  dialogTarefa.value = true
}

const salvarTarefa = async () => {
  if (!formTarefa.value.titulo.trim()) { erroTarefa.value = 'Informe o título.'; return }
  salvandoTarefa.value = true
  erroTarefa.value = ''
  try {
    const isEdit = !!formTarefa.value.id
    const url  = isEdit ? `/api/agenda/tarefas/${formTarefa.value.id}` : '/api/agenda/tarefas'
    const method = isEdit ? 'PUT' : 'POST'
    const body = {
      titulo:    formTarefa.value.titulo,
      descricao: formTarefa.value.descricao,
      data:      formTarefa.value.data,
      hora:      formTarefa.value.hora || null,
      cor:       formTarefa.value.cor,
    }
    const res = await fetch(url, { method, headers: authHeader(), body: JSON.stringify(body) })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Erro ao salvar tarefa')
    dialogTarefa.value = false
    await fetchTarefas()
  } catch (e) {
    erroTarefa.value = e.message
  } finally {
    salvandoTarefa.value = false
  }
}

const excluirTarefa = async (id) => {
  if (!confirm('Excluir esta tarefa?')) return
  try {
    await fetch(`/api/agenda/tarefas/${id}`, { method: 'DELETE', headers: authHeader() })
    await fetchTarefas()
  } catch (_) {}
}

// ── Insights ──────────────────────────────────────────────────────────────────
const insights        = ref({ despesas: {}, inadimplencia: {}, workflow: {} })
const loadingInsights = ref(false)

async function fetchInsights() {
  loadingInsights.value = true
  try {
    const res = await fetch('/api/agenda/insights', { headers: authHeader() })
    if (res.ok) insights.value = await res.json()
  } catch (_) {}
  loadingInsights.value = false
}

// ── Utils ─────────────────────────────────────────────────────────────────────
const formatBRL = (v) =>
  Number(v || 0).toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })

// ── Init ──────────────────────────────────────────────────────────────────────
let insightsTimer = null

onMounted(() => {
  fetchTarefas()
  fetchInsights()
  // Auto-refresh dos insights a cada 5 minutos
  insightsTimer = setInterval(fetchInsights, 5 * 60 * 1000)
})

onUnmounted(() => {
  if (insightsTimer) clearInterval(insightsTimer)
})
</script>

<style scoped>
/* ── Section header (sobrescreve o global para garantir gap) ── */
.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  gap: 16px;
}
.section-header > div:first-child {
  display: flex;
  align-items: center;
  gap: 14px;
}
.section-badge {
  width: 34px;
  height: 34px;
  min-width: 34px;
  border-radius: 9px;
  background: linear-gradient(135deg, #34d399, #059669);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

/* ── Calendário ── */
.cal-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
}

.cal-wd {
  text-align: center;
  font-size: 0.75rem;
  font-weight: 700;
  opacity: 0.45;
  padding: 6px 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

/* ── 15-day grid ── */
.cal-grid-15 {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 6px;
}

.cal-day-header {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
  margin-bottom: 8px;
  gap: 1px;
}
.cal-day-name {
  font-size: 0.68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.07em;
  opacity: 0.45;
  line-height: 1;
}
.cal-day-mes {
  font-size: 0.63rem;
  opacity: 0.35;
  line-height: 1;
  margin-top: 1px;
}
.cal-cell--near .cal-day-name {
  font-size: 0.8rem;
  opacity: 0.7;
}
.cal-cell--near .cal-day-mes {
  font-size: 0.72rem;
  opacity: 0.55;
}

.cal-cell {
  position: relative;
  min-height: 160px;
  border-radius: 10px;
  padding: 10px 10px 24px 10px;
  cursor: pointer;
  border: 1px solid rgba(var(--v-border-color), 0.07);
  background: rgba(var(--v-theme-on-surface), 0.01);
  transition: background 0.15s, box-shadow 0.15s;
  overflow: hidden;
}
.cal-cell:hover {
  background: rgba(var(--v-theme-primary), 0.06);
}
.cal-cell--out {
  opacity: 0.2;
  cursor: default;
  pointer-events: none;
}
.cal-cell--near {
  min-height: 340px;
  border-width: 2px !important;
  border-color: rgba(var(--v-theme-primary), 0.5) !important;
  background: rgba(var(--v-theme-primary), 0.05) !important;
  box-shadow: 0 0 0 1px rgba(var(--v-theme-primary), 0.12), 0 4px 20px rgba(var(--v-theme-primary), 0.1) !important;
}
.cal-cell--today {
  border-color: rgb(var(--v-theme-primary)) !important;
  background: rgba(var(--v-theme-primary), 0.06) !important;
}
.cal-cell--selected {
  background: rgba(var(--v-theme-primary), 0.12) !important;
  border-color: rgba(var(--v-theme-primary), 0.5) !important;
}

.cal-day-num {
  font-size: 1.05rem;
  font-weight: 700;
  opacity: 0.65;
  margin-bottom: 2px;
  line-height: 1;
}
.cal-cell--today .cal-day-num {
  color: rgb(var(--v-theme-primary));
  opacity: 1;
  font-size: 1.1rem;
}
.cal-cell--near .cal-day-num {
  font-size: 2rem !important;
  font-weight: 800 !important;
  opacity: 1 !important;
  color: rgb(var(--v-theme-primary)) !important;
  margin-bottom: 4px;
  line-height: 1;
}
.cal-cell--near.cal-cell--today .cal-day-num {
  font-size: 2.2rem !important;
  color: rgb(var(--v-theme-primary)) !important;
}

.cal-events {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.cal-event {
  border-radius: 5px;
  padding: 4px 7px;
  font-size: 0.74rem;
  line-height: 1.4;
  overflow: hidden;
}
/* Dark mode — cores claras sobre fundo escuro */
.cal-event--primary { background: rgba(99,102,241,0.22);  color: #a5b4fc; border-color: rgba(99,102,241,0.3); }
.cal-event--success { background: rgba(52,211,153,0.18);  color: #6ee7b7; border-color: rgba(52,211,153,0.3); }
.cal-event--error   { background: rgba(239,68,68,0.18);   color: #fca5a5; border-color: rgba(239,68,68,0.3); }
.cal-event--warning { background: rgba(251,146,60,0.18);  color: #fdba74; border-color: rgba(251,146,60,0.3); }
.cal-event--info    { background: rgba(34,211,238,0.18);  color: #67e8f9; border-color: rgba(34,211,238,0.3); }

/* Near cells in dark mode — stronger colors */
.cal-cell--near .cal-event--primary { background: rgba(99,102,241,0.32);  border-color: rgba(99,102,241,0.5); }
.cal-cell--near .cal-event--success { background: rgba(52,211,153,0.28);  border-color: rgba(52,211,153,0.5); }
.cal-cell--near .cal-event--error   { background: rgba(239,68,68,0.28);   border-color: rgba(239,68,68,0.5); }
.cal-cell--near .cal-event--warning { background: rgba(251,146,60,0.28);  border-color: rgba(251,146,60,0.5); }
.cal-cell--near .cal-event--info    { background: rgba(34,211,238,0.28);  border-color: rgba(34,211,238,0.5); }

/* Light mode — fundo sólido + texto escuro para contraste */
.v-theme--pratikaLight .cal-event--primary { background: #e0e7ff; color: #3730a3; border-color: #c7d2fe; }
.v-theme--pratikaLight .cal-event--success { background: #d1fae5; color: #065f46; border-color: #a7f3d0; }
.v-theme--pratikaLight .cal-event--error   { background: #fee2e2; color: #991b1b; border-color: #fecaca; }
.v-theme--pratikaLight .cal-event--warning { background: #ffedd5; color: #92400e; border-color: #fed7aa; }
.v-theme--pratikaLight .cal-event--info    { background: #cffafe; color: #155e75; border-color: #a5f3fc; }

/* Light mode — near cells com as mesmas cores verdes do modo escuro */
.v-theme--pratikaLight .cal-cell--near {
  border-color: rgba(52,211,153,0.5) !important;
  background: rgba(52,211,153,0.05) !important;
  box-shadow: 0 0 0 1px rgba(52,211,153,0.12), 0 4px 20px rgba(52,211,153,0.1) !important;
}
.v-theme--pratikaLight .cal-cell--near .cal-day-num {
  color: #34d399 !important;
}
.v-theme--pratikaLight .cal-cell--near:hover {
  background: rgba(52,211,153,0.1) !important;
}

/* Light mode — número do dia */
.v-theme--pratikaLight .cal-day-num { opacity: 0.75; }
.v-theme--pratikaLight .cal-cell--out { opacity: 0.3; }

/* Light mode — dia selecionado bem visível */
.v-theme--pratikaLight .cal-cell--selected {
  background: rgba(5,150,105,0.15) !important;
  border-color: #059669 !important;
  border-width: 2px !important;
  box-shadow: 0 0 0 2px rgba(5,150,105,0.25) !important;
}

/* Light mode — célula hover */
.v-theme--pratikaLight .cal-cell:hover {
  background: rgba(5,150,105,0.06) !important;
}

.cal-event-title {
  font-weight: 600;
  display: block;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.cal-event-desc {
  display: block;
  opacity: 0.75;
  font-size: 0.68rem;
  margin-top: 2px;
  line-height: 1.4;
  white-space: normal;
}
.cal-cell--near .cal-event {
  padding: 10px 12px;
  font-size: 0.95rem;
  border-radius: 9px;
  margin-bottom: 4px;
  border-width: 1px;
  border-style: solid;
}
.cal-cell--near .cal-event-title {
  font-size: 1rem;
  font-weight: 700;
  white-space: normal;
  line-height: 1.4;
}
.cal-cell--near .cal-event-desc {
  font-size: 0.85rem;
  opacity: 0.9;
  line-height: 1.5;
  margin-top: 5px;
  white-space: normal;
}
.v-theme--pratikaLight .cal-event-desc {
  opacity: 1;
}
.cal-event-more {
  font-size: 0.68rem;
  opacity: 0.4;
  padding-left: 7px;
}

.cal-add {
  position: absolute !important;
  bottom: 4px;
  right: 4px;
  opacity: 0;
  transition: opacity 0.15s;
}
.cal-cell:hover .cal-add {
  opacity: 0.6;
}

/* ── Detalhe do dia ── */
.tarefa-item {
  display: flex;
  gap: 10px;
  align-items: flex-start;
  padding: 10px 12px;
  border-radius: 10px;
  background: rgba(var(--v-theme-on-surface), 0.03);
  border: 1px solid rgba(var(--v-border-color), 0.07);
}
.tarefa-cor {
  width: 4px;
  min-height: 40px;
  border-radius: 2px;
  flex-shrink: 0;
}
.tarefa-cor--primary { background: #818cf8; }
.tarefa-cor--success { background: #34d399; }
.tarefa-cor--error   { background: #f87171; }
.tarefa-cor--warning { background: #fb923c; }
.tarefa-cor--info    { background: #22d3ee; }

.tarefa-body { flex: 1; min-width: 0; }
.tarefa-titulo { font-size: 0.88rem; font-weight: 600; }
.tarefa-hora { font-size: 0.72rem; opacity: 0.5; margin: 2px 0 0; }
.tarefa-desc { font-size: 0.78rem; opacity: 0.65; margin: 4px 0 0; line-height: 1.4; }

/* ── KPI Grid ── */
.kpi-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

/* ── KPI Cards ── */
.kpi-card {
  border-radius: 12px;
  padding: 16px 18px;
  border: 1px solid rgba(var(--v-border-color), 0.1);
}
.kpi-red    { background: rgba(239,68,68,0.07);  border-color: rgba(239,68,68,0.15);  }
.kpi-green  { background: rgba(52,211,153,0.07); border-color: rgba(52,211,153,0.15); }
.kpi-orange { background: rgba(251,146,60,0.07); border-color: rgba(251,146,60,0.15); }
.kpi-blue   { background: rgba(99,102,241,0.07); border-color: rgba(99,102,241,0.15); }
.kpi-purple { background: rgba(139,92,246,0.07); border-color: rgba(139,92,246,0.15); }
.kpi-teal   { background: rgba(20,184,166,0.07); border-color: rgba(20,184,166,0.15); }
.kpi-amber  { background: rgba(245,158,11,0.07); border-color: rgba(245,158,11,0.15); }
.kpi-indigo { background: rgba(79,70,229,0.07);  border-color: rgba(79,70,229,0.15);  }

.kpi-label { font-size: 0.7rem; opacity: 0.55; margin: 0 0 4px; text-transform: uppercase; letter-spacing: 0.04em; }
.kpi-value { font-size: 1.15rem; font-weight: 700; margin: 0; line-height: 1.2; }
.kpi-sub   { font-size: 0.68rem; opacity: 0.45; margin: 3px 0 0; }

/* ── Insight rows ── */
.insight-section-title {
  font-size: 0.78rem;
  font-weight: 600;
  opacity: 0.6;
  margin: 0 0 8px;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.insight-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 7px 0;
  border-bottom: 1px solid rgba(var(--v-border-color), 0.05);
}
.insight-row:last-child { border-bottom: none; }

.insight-row-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.insight-dot-orange { background: #fb923c; }
.insight-dot-red    { background: #f87171; }

.insight-row-title { font-size: 0.8rem; font-weight: 500; margin: 0; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.insight-row-sub   { font-size: 0.68rem; opacity: 0.45; margin: 1px 0 0; }
.insight-row-value { font-size: 0.78rem; font-weight: 600; white-space: nowrap; }
.insight-value-red { color: #f87171; }

.insight-rank {
  width: 20px;
  height: 20px;
  border-radius: 50%;
  background: rgba(var(--v-theme-on-surface), 0.07);
  font-size: 0.65rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.insight-timestamp {
  font-size: 0.65rem;
  opacity: 0.35;
  margin: 6px 0 0;
  text-align: right;
}

/* ── Cor Picker ── */
.cor-picker {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid transparent;
  transition: transform 0.15s;
}
.cor-picker:hover { transform: scale(1.15); }
.cor-picker--active { border-color: rgba(var(--v-theme-on-surface), 0.5); }

.cor-picker--primary { background: #818cf8; }
.cor-picker--success { background: #34d399; }
.cor-picker--error   { background: #f87171; }
.cor-picker--warning { background: #fb923c; }
.cor-picker--info    { background: #22d3ee; }

/* ── Dialog header (padrão do sistema) ── */
.dialog-header {
  padding: 16px 20px;
  background: rgb(var(--v-theme-surface));
  border-left: 3px solid #818cf8;
}
</style>
