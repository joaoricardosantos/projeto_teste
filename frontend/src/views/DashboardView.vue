<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="10" md="8" lg="6">
        <v-card elevation="8">
          <v-card-title class="text-h5 font-weight-bold pa-4">
            Upload de Planilha (CSV)
          </v-card-title>
          <v-card-text class="pa-4">
            <v-form @submit.prevent="handleFileUpload">

              <!-- Seleção de template -->
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

              <!-- Preview do template selecionado -->
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
                accept=".csv"
                label="Selecione o arquivo CSV gerado pelo sistema"
                variant="outlined"
                prepend-icon="mdi-file-delimited"
                show-size
                required
              />

              <v-alert v-if="errorMessage" type="error" class="mt-4" dense>
                {{ errorMessage }}
              </v-alert>

              <v-alert v-if="successMessage" type="success" class="mt-4" dense>
                {{ successMessage }}
                <div v-if="resultDetails" class="mt-2">
                  <strong>Sucessos:</strong> {{ resultDetails.success }}<br />
                  <strong>Erros:</strong> {{ resultDetails.errors }}
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
import { useRouter } from 'vue-router'

const router = useRouter()

// Estado do upload
const selectedFile = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const resultDetails = ref(null)

// Estado dos templates
const templates = ref([])
const loadingTemplates = ref(false)
const selectedTemplateId = ref(null)

const selectedTemplate = computed(() =>
  templates.value.find((t) => t.id === selectedTemplateId.value) || null
)

const authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

const renderPreview = (body) =>
  body
    .replace(/\{\{nome\}\}/g, 'João Silva')
    .replace(/\{\{condominio\}\}/g, 'Residencial Acácias')
    .replace(/\{\{valor\}\}/g, 'R$ 1.250,00')

const fetchTemplates = async () => {
  loadingTemplates.value = true
  try {
    const res = await fetch('/api/templates', { headers: authHeader() })
    if (res.ok) templates.value = await res.json()
  } catch (_) {
    // silencioso — templates são opcionais no dashboard
  } finally {
    loadingTemplates.value = false
  }
}

const handleFileUpload = async () => {
  if (!selectedFile.value) return

  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''
  resultDetails.value = null

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const token = localStorage.getItem('access_token')
    if (!token) throw new Error('Usuário não autenticado')

    // Escolhe endpoint conforme template selecionado
    let url = '/api/messages/upload-defaulters'
    if (selectedTemplateId.value) {
      url = `/api/messages/upload-defaulters-template?template_id=${selectedTemplateId.value}`
    }

    const response = await fetch(url, {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    })

    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Erro ao processar o arquivo')
    }

    successMessage.value = 'Arquivo processado com sucesso!'
    resultDetails.value = data.details
    selectedFile.value = null
  } catch (error) {
    errorMessage.value = error.message
    if (['Usuário não autenticado', 'Token_expired'].includes(error.message)) {
      logout()
    }
  } finally {
    loading.value = false
  }
}

const logout = () => {
  localStorage.removeItem('access_token')
  router.push('/')
}

onMounted(fetchTemplates)
</script>