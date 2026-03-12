<template>
  <v-container>
    <v-row class="mb-4" align="center">
      <v-col>
        <h1 class="text-h5 font-weight-bold">Templates de mensagem</h1>
        <p class="text-body-2 text-medium-emphasis">
          Apenas um template pode estar ativo por vez. O template ativo é usado no envio automático de cobranças.
        </p>
      </v-col>
    </v-row>

    <!-- Formulário de criação -->
    <v-card elevation="4" class="pa-6 mb-6">
      <h2 class="text-subtitle-1 font-weight-bold mb-4">Novo template</h2>
      <v-form @submit.prevent="handleCreate">
        <v-text-field
          v-model="form.name"
          label="Nome do template"
          variant="outlined"
          required
          class="mb-3"
        />
        <v-textarea
          v-model="form.body"
          label="Corpo da mensagem"
          variant="outlined"
          required
          rows="4"
          hint="Use {nome}, {condominio}, {valor} como variáveis"
          persistent-hint
          class="mb-3"
        />
        <v-checkbox
          v-model="form.is_active"
          label="Ativar este template imediatamente"
          color="primary"
          class="mb-3"
        />

        <v-alert v-if="createError" type="error" class="mb-3" dense>
          {{ createError }}
        </v-alert>
        <v-alert v-if="createSuccess" type="success" class="mb-3" dense>
          {{ createSuccess }}
        </v-alert>

        <v-btn type="submit" color="primary" :loading="isCreating">
          Criar template
        </v-btn>
      </v-form>
    </v-card>

    <!-- Lista de templates -->
    <v-alert v-if="fetchError" type="error" class="mb-4" dense>
      {{ fetchError }}
    </v-alert>

    <v-card elevation="4">
      <v-table>
        <thead>
          <tr>
            <th class="text-left">Nome</th>
            <th class="text-left">Corpo</th>
            <th class="text-center">Status</th>
            <th class="text-center">Ações</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="templates.length === 0">
            <td colspan="4" class="text-center py-6 text-medium-emphasis">
              Nenhum template cadastrado.
            </td>
          </tr>
          <tr v-for="tpl in templates" :key="tpl.id">
            <td>{{ tpl.name }}</td>
            <td class="text-truncate" style="max-width: 320px;">{{ tpl.body }}</td>
            <td class="text-center">
              <v-chip
                :color="tpl.is_active ? 'success' : 'grey'"
                text-color="white"
                size="small"
              >
                {{ tpl.is_active ? 'Ativo' : 'Inativo' }}
              </v-chip>
            </td>
            <td class="text-center">
              <v-btn
                v-if="!tpl.is_active"
                color="primary"
                size="small"
                class="mr-2"
                :loading="activatingId === tpl.id"
                @click="activateTemplate(tpl.id)"
              >
                Ativar
              </v-btn>
              <v-btn
                color="error"
                size="small"
                variant="outlined"
                :loading="deletingId === tpl.id"
                @click="deleteTemplate(tpl.id)"
              >
                Excluir
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'

const templates    = ref([])
const fetchError   = ref('')
const createError  = ref('')
const createSuccess = ref('')
const isCreating   = ref(false)
const activatingId = ref(null)
const deletingId   = ref(null)

const form = reactive({ name: '', body: '', is_active: false })

const authHeaders = () => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

const fetchTemplates = async () => {
  fetchError.value = ''
  try {
    const res = await fetch('/api/templates/', { headers: authHeaders() })
    if (!res.ok) throw new Error('Erro ao carregar templates')
    templates.value = await res.json()
  } catch (e) {
    fetchError.value = e.message
  }
}

const handleCreate = async () => {
  isCreating.value  = true
  createError.value = ''
  createSuccess.value = ''
  try {
    const res = await fetch('/api/templates/', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ name: form.name, body: form.body, is_active: form.is_active }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || 'Erro ao criar template')
    createSuccess.value = 'Template criado com sucesso!'
    form.name = ''
    form.body = ''
    form.is_active = false
    await fetchTemplates()
  } catch (e) {
    createError.value = e.message
  } finally {
    isCreating.value = false
  }
}

const activateTemplate = async (id) => {
  activatingId.value = id
  try {
    const res = await fetch('/api/templates/activate', {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({ template_id: id }),
    })
    if (!res.ok) throw new Error('Erro ao ativar template')
    await fetchTemplates()
  } catch (e) {
    fetchError.value = e.message
  } finally {
    activatingId.value = null
  }
}

const deleteTemplate = async (id) => {
  deletingId.value = id
  try {
    const res = await fetch(`/api/templates/${id}`, {
      method: 'DELETE',
      headers: authHeaders(),
    })
    if (!res.ok) throw new Error('Erro ao excluir template')
    await fetchTemplates()
  } catch (e) {
    fetchError.value = e.message
  } finally {
    deletingId.value = null
  }
}

onMounted(fetchTemplates)
</script>