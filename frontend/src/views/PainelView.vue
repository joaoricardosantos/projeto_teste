<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="10" md="8" lg="6">
        <v-card elevation="8">
          <v-card-title class="text-h5 font-weight-bold pa-4">
            Upload de Planilha (CSV ou Excel)
          </v-card-title>
          <v-card-text class="pa-4">
            <v-form @submit.prevent="handleFileUpload">

              <v-select
                v-model="selectedTemplateId"
                :items="templates"
                item-title="name"
                item-value="id"
                label="Template de mensagem (opcional)"
                variant="outlined"
                clearable
                prepend-icon="mdi-message-text"
                class="mb-2"
                :loading="loadingTemplates"
                no-data-text="Nenhum template cadastrado"
                hint="Se não selecionado, será usada a mensagem padrão"
                persistent-hint
              />

              <v-expand-transition>
                <v-sheet
                  v-if="selectedTemplate"
                  color="grey-lighten-4"
                  rounded
                  class="pa-3 mb-4"
                  style="font-size: 0.85rem; white-space: pre-wrap; word-break: break-word;"
                >
                  <p class="text-caption text-medium-emphasis mb-1">Pré-visualização:</p>
                  {{ renderPreview(selectedTemplate.body) }}
                </v-sheet>
              </v-expand-transition>

              <v-file-input
                v-model="selectedFile"
                accept=".csv,.xlsx"
                label="Selecione o arquivo (.csv ou .xlsx)"
                variant="outlined"
                prepend-icon="mdi-file-table"
                show-size
                required
              />

              <v-alert v-if="errorMessage" type="error" class="mt-4" dense>
                {{ errorMessage }}
              </v-alert>

              <!-- Resultado do processamento -->
              <v-alert
                v-if="resultDetails"
                type="success"
                class="mt-4"
                closable
                @click:close="resultDetails = null; successMessage = ''"
              >
                <div class="font-weight-bold mb-2">{{ successMessage }}</div>

                <div>✅ Enviados com sucesso: <strong>{{ resultDetails.success }}</strong></div>
                <div>❌ Falhas no envio: <strong>{{ envioFailures.length }}</strong></div>
                <div>📵 Sem número cadastrado: <strong>{{ resultDetails.sem_numero?.length || 0 }}</strong></div>

                <!-- Unidades sem número -->
                <div v-if="resultDetails.sem_numero && resultDetails.sem_numero.length" class="mt-3">
                  <div class="text-caption font-weight-bold text-medium-emphasis mb-1">
                    📵 Unidades sem número cadastrado:
                  </div>
                  <v-sheet color="orange-lighten-5" rounded class="pa-2">
                    <div
                      v-for="(f, i) in resultDetails.sem_numero"
                      :key="i"
                      class="text-caption py-1"
                      :style="i < resultDetails.sem_numero.length - 1 ? 'border-bottom: 1px solid rgba(0,0,0,0.08)' : ''"
                    >
                      <strong>{{ f.unidade }}</strong>
                      <span v-if="f.nome"> — {{ f.nome }}</span>
                    </div>
                  </v-sheet>
                </div>

                <!-- Falhas de envio reais -->
                <div v-if="envioFailures.length" class="mt-3">
                  <div class="text-caption font-weight-bold text-medium-emphasis mb-1">
                    ❌ Falhas no envio:
                  </div>
                  <div
                    v-for="f in envioFailures"
                    :key="f.phone"
                    class="text-caption"
                  >
                    {{ f.phone }} — {{ f.error }}
                  </div>
                </div>
              </v-alert>

              <v-btn
                type="submit"
                color="primary"
                block
                size="large"
                class="mt-6"
                :loading="loading"
                :disabled="!selectedFile"
              >
                Processar e Enviar Mensagens
              </v-btn>
            </v-form>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>
  </v-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'

const selectedFile     = ref(null)
const loading          = ref(false)
const errorMessage     = ref('')
const successMessage   = ref('')
const resultDetails    = ref(null)
const templates        = ref([])
const loadingTemplates = ref(false)
const selectedTemplateId = ref(null)

const selectedTemplate = computed(() =>
  templates.value.find(t => t.id === selectedTemplateId.value) || null
)

// Filtra apenas falhas reais de envio (exclui entradas de "sem número")
const envioFailures = computed(() => {
  if (!resultDetails.value?.failures) return []
  return resultDetails.value.failures.filter(f => f.phone !== '—')
})

const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` })

const renderPreview = (body) =>
  body
    .replace(/\{\{condominio\}\}/g, 'Residencial Acácias')
    .replace(/\{\{unidade\}\}/g, '315 SALA')
    .replace(/\{\{nome\}\}/g, 'João Silva')
    .replace(/\{\{qtd\}\}/g, '5')
    .replace(/\{\{competencia\}\}/g, '10/2025')
    .replace(/\{\{vencimento\}\}/g, '01/11/2025')
    .replace(/\{\{valor\}\}/g, 'R$ 1.250,00')

const fetchTemplates = async () => {
  loadingTemplates.value = true
  try {
    const res = await fetch('/api/templates', { headers: authHeader() })
    if (res.ok) templates.value = await res.json()
  } catch (_) {}
  finally { loadingTemplates.value = false }
}

const handleFileUpload = async () => {
  if (!selectedFile.value) return
  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  resultDetails.value = null

  try {
    const formData = new FormData()
    formData.append('file', selectedFile.value)
    let url = '/api/messages/upload-defaulters'
    if (selectedTemplateId.value) {
      url = `/api/messages/upload-defaulters-template?template_id=${selectedTemplateId.value}`
    }
    const res = await fetch(url, { method: 'POST', headers: authHeader(), body: formData })
    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Erro ao processar')
    successMessage.value = 'Processamento concluído!'
    resultDetails.value = data.details
    selectedFile.value = null
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    loading.value = false
  }
}

onMounted(fetchTemplates)
</script>