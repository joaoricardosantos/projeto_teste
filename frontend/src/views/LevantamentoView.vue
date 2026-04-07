<template>
  <div>

    <!-- ── Cabeçalho ── -->
    <div class="d-flex align-center gap-4 mb-6">
      <div class="page-icon">
        <v-icon size="20" color="white">mdi-magnify-scan</v-icon>
      </div>
      <div>
        <h1 class="page-title">Levantamento</h1>
        <p class="page-subtitle">Identifique unidades com cadastro incompleto na Superlógica</p>
      </div>
    </div>

    <!-- ── Card: Sem CPF ── -->
    <v-card class="section-card" elevation="3">
      <div class="section-header">
        <div class="section-badge">
          <v-icon size="16" color="white">mdi-card-account-details-outline</v-icon>
        </div>
        <div>
          <p class="section-title">Unidades sem CPF/CNPJ</p>
          <p class="section-subtitle">Selecione um ou mais condomínios para verificar</p>
        </div>
      </div>

      <div class="pa-6">
        <v-row align="center">
          <v-col cols="12" sm="9">
            <v-autocomplete
              v-model="condominiosSelecionados"
              :items="condominios"
              item-title="label"
              item-value="id"
              label="Condomínio"
              variant="outlined"
              density="comfortable"
              clearable
              multiple
              chips
              closable-chips
              hide-details
              :disabled="loading || loadingCondominios"
              no-data-text="Nenhum condomínio encontrado"
              placeholder="Selecione um ou mais condomínios..."
            />
          </v-col>
          <v-col cols="12" sm="3">
            <v-btn
              color="primary"
              block
              size="large"
              prepend-icon="mdi-magnify"
              :loading="loading"
              :disabled="!condominiosSelecionados.length || loading"
              @click="buscar"
            >Buscar</v-btn>
          </v-col>
        </v-row>

        <v-expand-transition>
          <p v-if="loadingCondominios" class="text-caption mt-3" style="color:#059669;">
            <v-icon size="12" color="primary">mdi-office-building-outline</v-icon>
            Buscando condomínios...
          </p>
          <p v-else-if="condominios.length > 0" class="text-caption mt-3" style="color:#6b7280;">
            <v-icon size="12" color="success">mdi-check-circle-outline</v-icon>
            {{ condominios.length }} disponíveis
          </p>
        </v-expand-transition>

        <v-alert v-if="erro" type="error" class="mt-4" closable @click:close="erro = ''">{{ erro }}</v-alert>

        <!-- Resultado -->
        <div v-if="resultado !== null" class="mt-6">
          <div class="d-flex align-center justify-space-between mb-3">
            <p class="text-body-2 font-weight-medium">
              <v-icon size="16" color="warning" class="mr-1">mdi-alert-circle-outline</v-icon>
              <strong>{{ resultado.length }}</strong> unidade(s) sem CPF/CNPJ encontrada(s)
            </p>
            <v-menu v-if="resultado.length">
              <template #activator="{ props }">
                <v-btn
                  size="small"
                  color="primary"
                  prepend-icon="mdi-file-export"
                  append-icon="mdi-chevron-down"
                  :loading="exportando"
                  v-bind="props"
                >Exportar</v-btn>
              </template>
              <v-list elevation="4" rounded="lg" min-width="200">
                <v-list-item prepend-icon="mdi-microsoft-excel" title="Excel (.xlsx)" subtitle="Planilha formatada" @click="exportar('xlsx')" />
                <v-divider />
                <v-list-item prepend-icon="mdi-file-pdf-box" title="PDF" subtitle="Relatório formatado" color="red-darken-2" @click="exportar('pdf')" />
              </v-list>
            </v-menu>
          </div>

          <div v-if="resultado.length === 0">
            <v-alert type="success" variant="tonal">
              Todos os cadastros estão completos neste(s) condomínio(s).
            </v-alert>
          </div>

          <v-data-table
            v-else
            :headers="headers"
            :items="resultado"
            :items-per-page="20"
            density="comfortable"
            class="result-table"
          >
            <template #item.condominio="{ item }">
              <span class="text-body-2">{{ item.condominio }}</span>
            </template>
            <template #item.sacado="{ item }">
              <span class="text-body-2 font-weight-medium">{{ item.sacado || '—' }}</span>
            </template>
            <template #item.bloco="{ item }">
              <span class="text-body-2">{{ item.bloco || '—' }}</span>
            </template>
            <template #item.unidade="{ item }">
              <v-chip size="x-small" color="warning" variant="tonal">{{ item.unidade || '—' }}</v-chip>
            </template>
          </v-data-table>
        </div>
      </div>
    </v-card>

  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useCondominios } from '../composables/useCondominios.js'

const { condominios, loadingCondominios, carregarCondominios } = useCondominios()
const condominiosSelecionados = ref([])
const loading                = ref(false)
const exportando             = ref(false)
const erro                   = ref('')
const resultado              = ref(null)

const headers = [
  { title: 'Condomínio', key: 'condominio', sortable: true },
  { title: 'Bloco',      key: 'bloco',      sortable: true  },
  { title: 'Unidade',    key: 'unidade',    sortable: true  },
  { title: 'Responsável', key: 'sacado',    sortable: true  },
]

const authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})


const buscar = async () => {
  loading.value  = true
  erro.value     = ''
  resultado.value = null
  try {
    const ids = condominiosSelecionados.value.join(',')
    const res = await fetch(`/api/admin/sem-cpf?id_condominio=${ids}`, { headers: authHeader() })
    if (!res.ok) throw new Error('Erro ao buscar dados')
    resultado.value = await res.json()
  } catch (e) {
    erro.value = e.message
  } finally {
    loading.value = false
  }
}

const exportar = async (formato) => {
  exportando.value = true
  try {
    const ids = condominiosSelecionados.value.join(',')
    const res = await fetch(`/api/admin/sem-cpf/${formato}?id_condominio=${ids}`, { headers: authHeader() })
    if (!res.ok) throw new Error('Erro ao gerar arquivo')
    const blob = await res.blob()
    const a    = document.createElement('a')
    a.href     = URL.createObjectURL(blob)
    a.download = `sem_cpf.${formato}`
    a.click()
    a.remove()
  } catch (e) {
    erro.value = e.message
  } finally {
    exportando.value = false
  }
}

onMounted(() => carregarCondominios())
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

.section-card { border-radius: 14px !important; overflow: hidden; }
.section-header {
  background: linear-gradient(135deg, #059669 0%, #34d399 100%);
  padding: 14px 20px;
  display: flex; align-items: center; gap: 14px;
}
.section-badge {
  width: 28px; height: 28px; border-radius: 50%;
  background: rgba(255,255,255,0.2);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.section-title    { color: white; font-weight: 600; font-size: 0.92rem; margin: 0; }
.section-subtitle { color: rgba(255,255,255,0.7); font-size: 0.78rem; margin: 2px 0 0; }

.result-table { border-radius: 10px; overflow: hidden; }
</style>
