<template>
  <div>
    <!-- Cabecalho -->
    <div class="d-flex align-center gap-4 mb-6">
      <div class="page-icon">
        <v-icon size="20" color="white">mdi-account-group-outline</v-icon>
      </div>
      <div>
        <h1 class="page-title">Clientes e Sindicos</h1>
        <p class="page-subtitle">Informacoes dos condominios, sindicos, subsindicos e gerentes</p>
      </div>
    </div>

    <!-- Filtros -->
    <v-card class="section-card mb-6" elevation="3">
      <div class="section-header">
        <v-icon color="white" class="mr-2">mdi-filter-outline</v-icon>
        <p class="section-title">Filtros</p>
      </div>
      <div class="pa-4">
        <v-row align="center">
          <v-col cols="12" sm="8">
            <v-text-field
              v-model="busca"
              label="Buscar por cliente, sindico, municipio ou CNPJ"
              variant="outlined"
              density="comfortable"
              hide-details
              clearable
              prepend-inner-icon="mdi-magnify"
              @keyup.enter="carregar"
              @click:clear="busca = ''; carregar()"
            />
          </v-col>
          <v-col cols="12" sm="4">
            <v-btn
              color="primary" block size="large"
              prepend-icon="mdi-magnify"
              :loading="loading"
              @click="carregar"
            >Buscar</v-btn>
          </v-col>
        </v-row>
      </div>
    </v-card>

    <!-- Loading -->
    <div v-if="loading" class="d-flex justify-center py-10">
      <v-progress-circular indeterminate color="primary" size="48" />
    </div>

    <!-- Erro -->
    <v-alert v-if="erro" type="error" class="mb-4" closable @click:close="erro = ''">
      {{ erro }}
    </v-alert>

    <!-- Resumo -->
    <v-card v-if="!loading && sindicos.length" class="mb-4 pa-4" elevation="1" rounded="lg">
      <div class="d-flex align-center gap-3">
        <v-icon color="success">mdi-check-circle-outline</v-icon>
        <span class="text-body-2">
          <strong>{{ sindicosFiltrados.length }}</strong> condominios encontrados
        </span>
      </div>
    </v-card>

    <!-- Cards dos sindicos -->
    <v-row v-if="!loading">
      <v-col
        v-for="(s, i) in sindicosPaginados"
        :key="i"
        cols="12"
      >
        <v-card class="section-card" elevation="3">
          <div class="section-header d-flex justify-space-between align-center">
            <div class="d-flex align-center">
              <v-icon color="white" class="mr-2">mdi-domain</v-icon>
              <p class="section-title">{{ s.cliente }}</p>
            </div>
            <div class="d-flex gap-2">
              <v-chip size="x-small" color="white" variant="tonal">{{ s.municipio || 'N/I' }}</v-chip>
              <v-chip size="x-small" color="white" variant="tonal">{{ s.qtd_unidades }} un.</v-chip>
            </div>
          </div>

          <div class="pa-5">
            <!-- Dados gerais -->
            <v-row dense>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">CNPJ</p>
                <p class="info-value">{{ s.cnpj || '-' }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Garantidora</p>
                <p class="info-value">{{ s.garantidora || '-' }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Juridico Pratika</p>
                <p class="info-value">{{ s.juridico_pratika || '-' }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Juridico Proprio</p>
                <p class="info-value">{{ s.juridico_proprio || '-' }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Contas a Pagar</p>
                <p class="info-value">{{ s.contas_pagar || '-' }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Folha Pagamento</p>
                <p class="info-value">{{ s.folha_pagamento || '-' }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Inicio Contrato</p>
                <p class="info-value">{{ s.data_inicio_contrato || '-' }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Folha pela Pratika?</p>
                <p class="info-value">{{ s.folha_pagamento_pratika || '-' }}</p>
              </v-col>
            </v-row>

            <v-divider class="my-4" />

            <!-- Contatos -->
            <p class="text-subtitle-2 font-weight-bold mb-3">Contatos</p>
            <v-row dense>
              <!-- Sindico -->
              <v-col cols="12" sm="4">
                <v-card variant="tonal" color="success" rounded="lg" class="pa-3">
                  <div class="d-flex align-center gap-2 mb-2">
                    <v-icon size="18" color="success">mdi-account-tie</v-icon>
                    <span class="text-caption font-weight-bold text-uppercase">Sindico</span>
                  </div>
                  <p class="text-body-2 font-weight-medium">{{ s.sindico || '-' }}</p>
                  <p class="text-caption">{{ s.telefone_sindico || '-' }}</p>
                  <div v-if="s.data_inicio_mandato || s.data_final_mandato" class="mt-1">
                    <p class="text-caption text-medium-emphasis">
                      Mandato: {{ s.data_inicio_mandato || '?' }} a {{ s.data_final_mandato || '?' }}
                    </p>
                  </div>
                </v-card>
              </v-col>
              <!-- Subsindico -->
              <v-col cols="12" sm="4">
                <v-card variant="tonal" color="info" rounded="lg" class="pa-3">
                  <div class="d-flex align-center gap-2 mb-2">
                    <v-icon size="18" color="info">mdi-account-outline</v-icon>
                    <span class="text-caption font-weight-bold text-uppercase">Subsindico</span>
                  </div>
                  <p class="text-body-2 font-weight-medium">{{ s.subsindico || '-' }}</p>
                  <p class="text-caption">{{ s.telefone_subsindico || '-' }}</p>
                </v-card>
              </v-col>
              <!-- Gerente -->
              <v-col cols="12" sm="4">
                <v-card variant="tonal" color="warning" rounded="lg" class="pa-3">
                  <div class="d-flex align-center gap-2 mb-2">
                    <v-icon size="18" color="warning">mdi-account-hard-hat</v-icon>
                    <span class="text-caption font-weight-bold text-uppercase">Gerente</span>
                  </div>
                  <p class="text-body-2 font-weight-medium">{{ s.gerente || '-' }}</p>
                  <p class="text-caption">{{ s.telefone_gerente || '-' }}</p>
                </v-card>
              </v-col>
            </v-row>

            <v-divider class="my-4" />

            <!-- Contratos -->
            <p class="text-subtitle-2 font-weight-bold mb-3">Contratos e Servicos</p>
            <v-row dense>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Empresa Terceirizada?</p>
                <p class="info-value">{{ s.empresa_terceirizada || '-' }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Portaria/ASG</p>
                <p class="info-value">{{ s.contrato_portaria || '-' }}</p>
                <p v-if="s.valor_contrato_portaria" class="text-caption text-success">{{ s.valor_contrato_portaria }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Vigilancia</p>
                <p class="info-value">{{ s.contrato_vigilancia || '-' }}</p>
                <p v-if="s.valor_contrato_vigilancia" class="text-caption text-success">{{ s.valor_contrato_vigilancia }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Jardinagem</p>
                <p class="info-value">{{ s.contrato_jardinagem || '-' }}</p>
                <p v-if="s.valor_contrato_jardinagem" class="text-caption text-success">{{ s.valor_contrato_jardinagem }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Paulo Conversou?</p>
                <p class="info-value">{{ s.paulo_conversou || '-' }}</p>
              </v-col>
              <v-col cols="12" sm="4" md="3">
                <p class="info-label">Relacionamento</p>
                <p class="info-value">{{ s.relacionamento || '-' }}</p>
              </v-col>
            </v-row>
          </div>
        </v-card>
      </v-col>
    </v-row>

    <!-- Paginacao -->
    <div v-if="totalPaginas > 1" class="d-flex justify-center mt-6">
      <v-pagination
        v-model="pagina"
        :length="totalPaginas"
        :total-visible="7"
        color="success"
      />
    </div>

    <!-- Vazio -->
    <div v-if="!loading && !erro && sindicos.length === 0" class="text-center py-10 text-medium-emphasis">
      <v-icon size="48" class="mb-2">mdi-inbox-outline</v-icon>
      <p>Nenhum registro encontrado.</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const busca = ref('')
const loading = ref(false)
const erro = ref('')
const sindicos = ref([])
const pagina = ref(1)
const porPagina = 10

const authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

const sindicosFiltrados = computed(() => sindicos.value)

const totalPaginas = computed(() =>
  Math.ceil(sindicosFiltrados.value.length / porPagina)
)

const sindicosPaginados = computed(() => {
  const inicio = (pagina.value - 1) * porPagina
  return sindicosFiltrados.value.slice(inicio, inicio + porPagina)
})

const carregar = async () => {
  loading.value = true
  erro.value = ''
  pagina.value = 1

  try {
    const params = busca.value ? `?busca=${encodeURIComponent(busca.value)}` : ''
    const res = await fetch(`/api/sindicos/${params}`, { headers: authHeader() })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Erro ao carregar dados')
    sindicos.value = data
  } catch (e) {
    erro.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(carregar)
</script>

<style scoped>
.page-icon {
  width: 42px; height: 42px; border-radius: 11px;
  background: linear-gradient(135deg, #34d399 0%, #059669 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(5,150,105,0.28); flex-shrink: 0;
  margin-right: 8px;
}
.page-title    { font-size: 1.2rem; font-weight: 700; line-height: 1.3; margin: 0; }
.page-subtitle { font-size: 0.82rem; opacity: .55; margin: 2px 0 0; }

.section-card   { border-radius: 14px !important; overflow: hidden; }
.section-header {
  background: linear-gradient(135deg, #059669 0%, #34d399 100%);
  padding: 14px 20px;
  display: flex; align-items: center;
}
.section-title { color: white; font-weight: 600; font-size: 0.92rem; margin: 0; }

.info-label { font-size: 0.72rem; text-transform: uppercase; letter-spacing: .05em; opacity: .5; margin: 0 0 2px; }
.info-value { font-size: 0.9rem; font-weight: 500; margin: 0; }
</style>
