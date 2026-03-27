<template>
  <div>
    <!-- Cabeçalho -->
    <div class="d-flex align-center gap-4 mb-6">
      <div class="page-icon">
        <v-icon size="20" color="white">mdi-gavel</v-icon>
      </div>
      <div>
        <h1 class="page-title">Consulta PJE — TJRN</h1>
        <p class="page-subtitle">Acompanhe processos judiciais e veja a última movimentação</p>
      </div>
    </div>

    <!-- Abas -->
    <v-tabs v-model="aba" color="success" class="mb-6">
      <v-tab value="processo">
        <v-icon start>mdi-file-document-outline</v-icon>
        Por Número do Processo
      </v-tab>
      <v-tab value="oab">
        <v-icon start>mdi-card-account-details-outline</v-icon>
        Por OAB
      </v-tab>
    </v-tabs>

    <v-tabs-window v-model="aba">

      <!-- ===== ABA: PROCESSO ===== -->
      <v-tabs-window-item value="processo">

        <!-- Busca -->
        <v-card class="section-card mb-6" elevation="3">
          <div class="section-header">
            <v-icon color="white" class="mr-2">mdi-magnify</v-icon>
            <p class="section-title">Consultar Processo</p>
          </div>
          <div class="pa-6">
            <v-row align="center">
              <v-col cols="12" sm="8">
                <v-text-field
                  v-model="numeroInput"
                  label="Número do processo (CNJ)"
                  placeholder="Ex: 08420089520198205001"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                  prepend-inner-icon="mdi-file-document-outline"
                  @keyup.enter="consultar"
                />
              </v-col>
              <v-col cols="12" sm="4">
                <v-btn
                  color="primary" block size="large"
                  prepend-icon="mdi-magnify"
                  :loading="loading"
                  :disabled="!numeroInput || loading"
                  @click="consultar"
                >{{ loading ? 'Consultando...' : 'Consultar' }}</v-btn>
              </v-col>
            </v-row>
            <v-alert v-if="erro" type="error" class="mt-4" closable @click:close="erro = ''">
              {{ erro }}
            </v-alert>
          </div>
        </v-card>

        <!-- Resultado processo -->
        <v-expand-transition>
          <div v-if="processo">

            <v-card class="section-card mb-4" elevation="3">
              <div class="section-header">
                <v-icon color="white" class="mr-2">mdi-file-document-check-outline</v-icon>
                <p class="section-title">{{ processo.numero }}</p>
              </div>
              <div class="pa-6">
                <v-row>
                  <v-col cols="12" sm="6" md="4">
                    <p class="info-label">Classe</p>
                    <p class="info-value">{{ processo.classe || '—' }}</p>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <p class="info-label">Tribunal / Grau</p>
                    <p class="info-value">{{ processo.tribunal }} — {{ processo.grau }}</p>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <p class="info-label">Ajuizamento</p>
                    <p class="info-value">{{ processo.data_ajuizamento || '—' }}</p>
                  </v-col>
                  <v-col cols="12" sm="12" md="8">
                    <p class="info-label">Órgão Julgador</p>
                    <p class="info-value">{{ processo.orgao_julgador || '—' }}</p>
                  </v-col>
                  <v-col cols="12" sm="6" md="4">
                    <p class="info-label">Assunto(s)</p>
                    <p class="info-value">{{ processo.assuntos.join(', ') || '—' }}</p>
                  </v-col>
                </v-row>

                <div v-if="processo.partes?.length" class="mt-4">
                  <p class="info-label mb-2">Partes</p>
                  <v-chip
                    v-for="(p, i) in processo.partes"
                    :key="i"
                    class="mr-2 mb-1"
                    :color="p.polo === 'AT' ? 'blue-darken-1' : p.polo === 'RE' ? 'red-darken-1' : 'grey'"
                    variant="tonal"
                    size="small"
                  >
                    <strong class="mr-1">{{ p.polo }}</strong> {{ p.nome }}
                  </v-chip>
                </div>
              </div>
            </v-card>

            <v-card class="mb-4" elevation="2" rounded="lg" v-if="processo.ultimo_movimento?.descricao">
              <v-card-text class="d-flex align-center gap-4 pa-5">
                <div class="ultimo-mov-icon">
                  <v-icon color="white" size="22">mdi-clock-check-outline</v-icon>
                </div>
                <div>
                  <p class="text-caption text-medium-emphasis mb-1">ÚLTIMA MOVIMENTAÇÃO</p>
                  <p class="text-body-1 font-weight-bold">{{ processo.ultimo_movimento.descricao }}</p>
                  <p class="text-caption text-medium-emphasis">{{ processo.ultimo_movimento.data }}</p>
                </div>
              </v-card-text>
            </v-card>

            <v-card class="section-card" elevation="3">
              <div class="section-header d-flex justify-space-between align-center">
                <div class="d-flex align-center">
                  <v-icon color="white" class="mr-2">mdi-timeline-text-outline</v-icon>
                  <p class="section-title">Movimentações ({{ movimentos.length }})</p>
                </div>
                <v-btn
                  v-if="!movimentosCarregados"
                  size="small" variant="tonal" color="white"
                  :loading="loadingMov"
                  @click="carregarMovimentos"
                >Ver todas</v-btn>
              </div>
              <div class="pa-4">
                <v-timeline density="compact" side="end" v-if="movimentos.length">
                  <v-timeline-item
                    v-for="(m, i) in movimentos"
                    :key="i"
                    :dot-color="i === 0 ? 'success' : 'grey-lighten-1'"
                    size="small"
                  >
                    <div class="d-flex justify-space-between align-start">
                      <div>
                        <p class="text-body-2 font-weight-medium">{{ m.descricao || '(sem descrição)' }}</p>
                      </div>
                      <p class="text-caption text-medium-emphasis ml-4 text-no-wrap">{{ m.data }}</p>
                    </div>
                  </v-timeline-item>
                </v-timeline>
                <p v-else class="text-caption text-medium-emphasis pa-2">Nenhum movimento registrado.</p>
              </div>
            </v-card>

          </div>
        </v-expand-transition>

      </v-tabs-window-item>

      <!-- ===== ABA: OAB ===== -->
      <v-tabs-window-item value="oab">

        <!-- Busca por OAB -->
        <v-card class="section-card mb-6" elevation="3">
          <div class="section-header">
            <v-icon color="white" class="mr-2">mdi-card-account-details-outline</v-icon>
            <p class="section-title">Consultar por OAB — PJE Comunica</p>
          </div>
          <div class="pa-6">
            <v-row align="center">
              <v-col cols="12" sm="5">
                <v-text-field
                  v-model="oabNumero"
                  label="Número da OAB"
                  placeholder="Ex: 12345"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                  clearable
                  prepend-inner-icon="mdi-card-account-details-outline"
                  @keyup.enter="consultarOab"
                />
              </v-col>
              <v-col cols="12" sm="3">
                <v-select
                  v-model="oabUf"
                  :items="ufs"
                  label="UF"
                  variant="outlined"
                  density="comfortable"
                  hide-details
                />
              </v-col>
              <v-col cols="12" sm="4">
                <v-btn
                  color="primary" block size="large"
                  prepend-icon="mdi-magnify"
                  :loading="loadingOab"
                  :disabled="!oabNumero || !oabUf || loadingOab"
                  @click="consultarOab"
                >{{ loadingOab ? 'Consultando...' : 'Consultar' }}</v-btn>
              </v-col>
            </v-row>
            <v-alert v-if="erroOab" type="error" class="mt-4" closable @click:close="erroOab = ''">
              {{ erroOab }}
            </v-alert>
          </div>
        </v-card>

        <!-- Resultados OAB -->
        <v-expand-transition>
          <div v-if="oabConsultado">

            <div v-if="comunicacoes.length === 0" class="text-center py-10 text-medium-emphasis">
              <v-icon size="48" class="mb-2">mdi-inbox-outline</v-icon>
              <p>Nenhuma comunicação encontrada para esta OAB.</p>
            </div>

            <template v-else>
              <!-- Resumo -->
              <v-card class="mb-4 pa-4" elevation="1" rounded="lg">
                <div class="d-flex align-center gap-3">
                  <v-icon color="success">mdi-check-circle-outline</v-icon>
                  <span class="text-body-2">
                    Exibindo <strong>{{ comunicacoes.length }}</strong> de
                    <strong>{{ oabTotal }}</strong> comunicações
                    (página {{ oabPagina }} de {{ oabTotalPaginas }})
                  </span>
                </div>
              </v-card>

              <!-- Lista de comunicações -->
              <v-card
                v-for="(c, i) in comunicacoes"
                :key="i"
                class="mb-3"
                elevation="2"
                rounded="lg"
              >
                <v-card-text class="pa-4">
                  <div class="d-flex justify-space-between align-start flex-wrap gap-2 mb-2">
                    <div>
                      <p class="text-body-2 font-weight-bold mb-0">{{ c.numero_processo || '—' }}</p>
                      <p class="text-caption text-medium-emphasis">{{ c.orgao_julgador || '—' }}</p>
                    </div>
                    <div class="d-flex gap-2 flex-wrap">
                      <v-chip v-if="c.tipo_comunicacao" size="x-small" color="blue" variant="tonal">
                        {{ c.tipo_comunicacao }}
                      </v-chip>
                      <v-chip v-if="c.status" size="x-small"
                        :color="c.status === 'Lida' ? 'success' : 'orange'"
                        variant="tonal"
                      >
                        {{ c.status }}
                      </v-chip>
                    </div>
                  </div>

                  <v-divider class="mb-2" />

                  <v-row dense>
                    <v-col v-if="c.destinatario" cols="12" sm="6">
                      <p class="info-label">Destinatário</p>
                      <p class="info-value">{{ c.destinatario }}</p>
                    </v-col>
                    <v-col v-if="c.data_disponibilizacao" cols="12" sm="3">
                      <p class="info-label">Disponibilizado em</p>
                      <p class="info-value">{{ c.data_disponibilizacao }}</p>
                    </v-col>
                    <v-col v-if="c.prazo" cols="12" sm="3">
                      <p class="info-label">Prazo</p>
                      <p class="info-value">{{ c.prazo }}</p>
                    </v-col>
                    <v-col v-if="c.meio_comunicacao" cols="12" sm="3">
                      <p class="info-label">Meio</p>
                      <p class="info-value">{{ c.meio_comunicacao }}</p>
                    </v-col>
                  </v-row>

                  <div v-if="c.texto" class="mt-2">
                    <p class="info-label">Teor</p>
                    <p class="text-body-2 text-medium-emphasis">{{ c.texto }}{{ c.texto.length >= 300 ? '…' : '' }}</p>
                  </div>
                </v-card-text>
              </v-card>

              <!-- Paginação -->
              <div class="d-flex justify-center mt-4" v-if="oabTotalPaginas > 1">
                <v-pagination
                  v-model="oabPagina"
                  :length="oabTotalPaginas"
                  :total-visible="7"
                  color="success"
                  @update:model-value="mudarPagina"
                />
              </div>
            </template>

          </div>
        </v-expand-transition>

      </v-tabs-window-item>

    </v-tabs-window>

  </div>
</template>

<script setup>
import { ref } from 'vue'

// ---- Aba ativa ----
const aba = ref('processo')

// ---- Aba Processo ----
const numeroInput          = ref('')
const loading              = ref(false)
const loadingMov           = ref(false)
const erro                 = ref('')
const processo             = ref(null)
const movimentos           = ref([])
const movimentosCarregados = ref(false)

// ---- Aba OAB ----
const oabNumero       = ref('')
const oabUf           = ref('RN')
const loadingOab      = ref(false)
const erroOab         = ref('')
const oabConsultado   = ref(false)
const comunicacoes    = ref([])
const oabTotal        = ref(0)
const oabPagina       = ref(1)
const oabTotalPaginas = ref(1)

const ufs = [
  'AC','AL','AM','AP','BA','CE','DF','ES','GO','MA','MG','MS','MT',
  'PA','PB','PE','PI','PR','RJ','RN','RO','RR','RS','SC','SE','SP','TO',
]

const authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

// ---- Funções: Processo ----
const consultar = async () => {
  if (!numeroInput.value) return
  loading.value              = true
  erro.value                 = ''
  processo.value             = null
  movimentos.value           = []
  movimentosCarregados.value = false

  try {
    const res  = await fetch(`/api/pje/consultar?numero=${encodeURIComponent(numeroInput.value)}`, { headers: authHeader() })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Erro ao consultar processo')
    processo.value = data.processo
    if (data.processo.ultimo_movimento?.descricao) {
      movimentos.value = [data.processo.ultimo_movimento]
    }
  } catch (e) {
    erro.value = e.message
  } finally {
    loading.value = false
  }
}

const carregarMovimentos = async () => {
  loadingMov.value = true
  try {
    const res  = await fetch(`/api/pje/movimentos?numero=${encodeURIComponent(numeroInput.value)}`, { headers: authHeader() })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Erro ao carregar movimentos')
    movimentos.value           = data.movimentos
    movimentosCarregados.value = true
  } catch (e) {
    erro.value = e.message
  } finally {
    loadingMov.value = false
  }
}

// ---- Funções: OAB ----
const consultarOab = async (pagina = 1) => {
  if (!oabNumero.value || !oabUf.value) return
  loadingOab.value  = true
  erroOab.value     = ''
  oabConsultado.value = false
  comunicacoes.value  = []

  try {
    const params = new URLSearchParams({
      numero_oab: oabNumero.value.trim(),
      uf_oab:     oabUf.value,
      pagina:     pagina,
    })
    const res  = await fetch(`/api/pje/oab?${params}`, { headers: authHeader() })
    const data = await res.json()
    if (!res.ok) throw new Error(typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail) || 'Erro ao consultar OAB')
    comunicacoes.value    = data.comunicacoes
    oabTotal.value        = data.total
    oabPagina.value       = data.pagina
    oabTotalPaginas.value = data.total_paginas
    oabConsultado.value   = true
  } catch (e) {
    erroOab.value = e.message
  } finally {
    loadingOab.value = false
  }
}

const mudarPagina = (p) => consultarOab(p)
</script>

<style scoped>
.page-icon {
  width: 42px; height: 42px; border-radius: 11px;
  background: linear-gradient(135deg, #00a651 0%, #006837 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(0,168,81,0.3); flex-shrink: 0;
  margin-right: 8px;
}
.page-title    { font-size: 1.2rem; font-weight: 700; line-height: 1.3; margin: 0; }
.page-subtitle { font-size: 0.82rem; opacity: .55; margin: 2px 0 0; }

.section-card   { border-radius: 14px !important; overflow: hidden; }
.section-header {
  background: linear-gradient(135deg, #006837 0%, #00a651 100%);
  padding: 14px 20px;
  display: flex; align-items: center;
}
.section-title { color: white; font-weight: 600; font-size: 0.92rem; margin: 0; }

.info-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: .05em; opacity: .5; margin: 0 0 2px; }
.info-value { font-size: 0.9rem; font-weight: 500; margin: 0; }

.ultimo-mov-icon {
  width: 44px; height: 44px; border-radius: 12px; flex-shrink: 0;
  background: linear-gradient(135deg, #00a651, #006837);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(0,168,81,0.25);
}
</style>
