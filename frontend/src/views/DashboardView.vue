<template>
  <v-container class="fill-height" fluid>
    <v-row align="center" justify="center">
      <v-col cols="12" sm="10" md="8" lg="6">
        <v-card elevation="8">
          <v-card-title class="text-h5 font-weight-bold pa-4">
            Enviar Mensagens
          </v-card-title>

          <v-card-text class="pa-4">
            <!-- Template ativo -->
            <v-card
              v-if="activeTemplate"
              variant="tonal"
              color="primary"
              class="mb-4 pa-3"
            >
              <div class="d-flex align-center mb-1">
                <v-icon size="small" class="mr-1">mdi-message-check</v-icon>
                <span class="text-caption font-weight-bold">Template ativo: {{ activeTemplate.name }}</span>
              </div>
              <pre class="template-preview">{{ activeTemplate.body }}</pre>
            </v-card>

            <v-alert v-else type="warning" variant="tonal" density="compact" class="mb-4">
              Nenhum template ativo. Será usado o template padrão.
              <router-link to="/admin" class="ml-1">Configurar na aba Administração →</router-link>
            </v-alert>

            <!-- Instruções -->
            <v-alert type="info" variant="tonal" class="mb-4" density="compact">
              Envie uma planilha <strong>.xlsx</strong> ou <strong>.csv</strong> com as colunas:<br />
              <code>Condomínio</code> · <code>Nome</code> · <code>Telefones</code> ·
              <code>Valor da dívida com juros</code> · <code>Data de atraso</code>
            </v-alert>

            <v-form @submit.prevent="handleFileUpload">
              <v-file-input
                v-model="selectedFile"
                accept=".csv,.xlsx"
                label="Selecione o arquivo (.csv ou .xlsx)"
                variant="outlined"
                prepend-icon="mdi-file-table"
                show-size
                required
                @update:model-value="onFileSelected"
              />

              <!-- Preview da planilha -->
              <div v-if="previewRows.length" class="mb-4">
                <p class="text-caption text-medium-emphasis mb-1">
                  Pré-visualização — primeiras {{ previewRows.length }} de {{ totalRows }} linhas:
                </p>
                <div style="overflow-x:auto">
                  <v-table density="compact" class="rounded border">
                    <thead>
                      <tr>
                        <th v-for="h in previewHeaders" :key="h">{{ h }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr v-for="(row, i) in previewRows" :key="i">
                        <td v-for="h in previewHeaders" :key="h">{{ row[h] }}</td>
                      </tr>
                    </tbody>
                  </v-table>
                </div>
              </div>

              <!-- Resultado -->
              <v-alert v-if="errorMessage" type="error" class="mt-4" density="compact">
                {{ errorMessage }}
              </v-alert>

              <v-alert v-if="successMessage" type="success" class="mt-4" density="compact">
                {{ successMessage }}
                <div v-if="resultDetails" class="mt-1">
                  <strong>✅ Enviados:</strong> {{ resultDetails.success }} &nbsp;
                  <strong>❌ Erros:</strong> {{ resultDetails.errors }}
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
                prepend-icon="mdi-whatsapp"
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
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import * as XLSX from 'https://cdn.jsdelivr.net/npm/xlsx@0.18.5/+esm'

const router = useRouter()

const selectedFile   = ref(null)
const loading        = ref(false)
const errorMessage   = ref('')
const successMessage = ref('')
const resultDetails  = ref(null)
const previewHeaders = ref([])
const previewRows    = ref([])
const totalRows      = ref(0)
const activeTemplate = ref(null)

// Busca template ativo para exibir no topo
const fetchActiveTemplate = async () => {
  try {
    const token = localStorage.getItem('access_token')
    const res = await fetch('/api/admin/templates/active', {
      headers: { Authorization: `Bearer ${token}` },
    })
    if (res.ok) activeTemplate.value = await res.json()
  } catch { /* nenhum template ativo */ }
}

// Preview local da planilha
const onFileSelected = async (file) => {
  previewHeaders.value = []
  previewRows.value    = []
  totalRows.value      = 0
  errorMessage.value   = ''
  successMessage.value = ''
  resultDetails.value  = null

  if (!file) return

  try {
    const buffer = await file.arrayBuffer()
    const wb     = XLSX.read(buffer, { type: 'array' })
    const ws     = wb.Sheets[wb.SheetNames[0]]
    const data   = XLSX.utils.sheet_to_json(ws, { defval: '' })
    if (!data.length) return
    previewHeaders.value = Object.keys(data[0])
    totalRows.value      = data.length
    previewRows.value    = data.slice(0, 5)
  } catch { /* CSV ou formato não suportado pelo XLSX — preview ignorado */ }
}

// Envio ao backend
const handleFileUpload = async () => {
  if (!selectedFile.value) return

  loading.value        = true
  errorMessage.value   = ''
  successMessage.value = ''
  resultDetails.value  = null

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const token = localStorage.getItem('access_token')
    if (!token) throw new Error('Usuário não autenticado')

    const res = await fetch('/api/messages/upload-defaulters', {
      method: 'POST',
      headers: { Authorization: `Bearer ${token}` },
      body: formData,
    })

    const data = await res.json()
    if (!res.ok) throw new Error(data.detail || 'Erro ao processar o arquivo')

    successMessage.value = 'Arquivo processado com sucesso!'
    resultDetails.value  = data.details
    selectedFile.value   = null
    previewHeaders.value = []
    previewRows.value    = []
    totalRows.value      = 0
  } catch (error) {
    errorMessage.value = error.message
    if (['Usuário não autenticado', 'Token_expired'].includes(error.message)) {
      localStorage.removeItem('access_token')
      router.push('/')
    }
  } finally {
    loading.value = false
  }
}

onMounted(fetchActiveTemplate)
</script>

<style scoped>
.template-preview {
  font-family: 'Segoe UI', sans-serif;
  font-size: 0.8rem;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0;
  opacity: 0.85;
}
</style>