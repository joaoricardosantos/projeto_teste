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
              <v-file-input
                v-model="selectedFile"
                accept=".csv"
                label="Selecione o arquivo CSV gerado pelo sistema"
                variant="outlined"
                prepend-icon="mdi-file-delimited"
                show-size
                required
              ></v-file-input>

              <v-alert v-if="errorMessage" type="error" class="mt-4" dense>
                {{ errorMessage }}
              </v-alert>

              <v-alert v-if="successMessage" type="success" class="mt-4" dense>
                {{ successMessage }}
                <div v-if="resultDetails" class="mt-2">
                  <strong>Sucessos:</strong> {{ resultDetails.success }} <br />
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const selectedFile = ref(null)
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const resultDetails = ref(null)

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
    if (!token) {
      throw new Error('Usuário não autenticado')
    }

    const response = await fetch('/api/messages/upload-defaulters', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`
      },
      body: formData
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
    if (error.message === 'Usuário não autenticado' || error.message === 'Token_expired') {
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
</script>