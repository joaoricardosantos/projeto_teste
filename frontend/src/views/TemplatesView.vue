<template>
  <v-container>
    <!-- Cabeçalho -->
    <v-row class="mb-6" align="center">
      <v-col cols="12" sm="8">
        <h1 class="text-h5 font-weight-bold">Templates de Mensagem</h1>
        <p class="text-body-2 text-medium-emphasis mt-1">
          Crie e gerencie templates reutilizáveis para os disparos.
          Use <code>{{nome}}</code>, <code>{{condominio}}</code> e <code>{{valor}}</code> como variáveis dinâmicas.
        </p>
      </v-col>
      <v-col cols="12" sm="4" class="text-sm-right">
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
          Novo template
        </v-btn>
      </v-col>
    </v-row>

    <!-- Alerta de erro global -->
    <v-alert v-if="errorMessage" type="error" class="mb-4" closable @click:close="errorMessage = ''">
      {{ errorMessage }}
    </v-alert>

    <!-- Loading -->
    <v-row v-if="loading" justify="center" class="my-10">
      <v-progress-circular indeterminate color="primary" size="48" />
    </v-row>

    <!-- Estado vazio -->
    <v-card v-else-if="templates.length === 0" elevation="2" class="pa-10 text-center">
      <v-icon size="64" color="grey-lighten-1" class="mb-4">mdi-message-text-outline</v-icon>
      <p class="text-h6 text-medium-emphasis">Nenhum template cadastrado</p>
      <p class="text-body-2 text-medium-emphasis mb-6">
        Crie seu primeiro template para personalizar os disparos de cobrança.
      </p>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
        Criar template
      </v-btn>
    </v-card>

    <!-- Lista de templates -->
    <v-row v-else>
      <v-col v-for="template in templates" :key="template.id" cols="12" md="6">
        <v-card elevation="3" class="h-100">
          <v-card-title class="d-flex align-center justify-space-between pa-4 pb-2">
            <span class="text-subtitle-1 font-weight-bold text-truncate">
              {{ template.name }}
            </span>
            <div class="d-flex gap-1 ml-2 flex-shrink-0">
              <v-btn icon size="small" variant="text" color="primary" @click="openEditDialog(template)">
                <v-icon size="18">mdi-pencil</v-icon>
              </v-btn>
              <v-btn icon size="small" variant="text" color="error" @click="confirmDelete(template)">
                <v-icon size="18">mdi-delete</v-icon>
              </v-btn>
            </div>
          </v-card-title>

          <v-card-text class="pa-4 pt-0">
            <v-sheet
              color="grey-lighten-4"
              rounded
              class="pa-3 mb-3"
              style="font-family: monospace; font-size: 0.85rem; white-space: pre-wrap; word-break: break-word; min-height: 60px;"
            >{{ template.body }}</v-sheet>

            <div class="d-flex flex-wrap gap-1 mb-2">
              <v-chip
                v-for="variable in extractVariables(template.body)"
                :key="variable"
                size="x-small"
                color="primary"
                variant="tonal"
                prepend-icon="mdi-code-braces"
              >
                {{ variable }}
              </v-chip>
            </div>

            <p class="text-caption text-disabled">
              Criado em {{ template.created_at }}
              <span v-if="template.updated_at !== template.created_at">
                · Editado em {{ template.updated_at }}
              </span>
            </p>
          </v-card-text>
        </v-card>
      </v-col>
    </v-row>

    <!-- ── Dialog: Criar / Editar ── -->
    <v-dialog v-model="dialog.open" max-width="600" persistent>
      <v-card>
        <v-card-title class="pa-4 pb-2">
          <span class="text-h6">{{ dialog.isEdit ? 'Editar template' : 'Novo template' }}</span>
        </v-card-title>

        <v-card-text class="pa-4">
          <v-text-field
            v-model="dialog.form.name"
            label="Nome do template"
            variant="outlined"
            :error-messages="dialog.errors.name"
            class="mb-3"
            @update:model-value="dialog.errors.name = ''"
          />

          <!-- Botões de inserção de variáveis -->
          <div class="mb-2">
            <p class="text-caption text-medium-emphasis mb-1">Clique para inserir uma variável:</p>
            <div class="d-flex gap-2 flex-wrap">
              <v-chip
                v-for="variable in availableVariables"
                :key="variable.value"
                size="small"
                color="primary"
                variant="tonal"
                prepend-icon="mdi-code-braces"
                style="cursor: pointer;"
                @click="insertVariable(variable.value)"
              >
                {{ variable.label }}
              </v-chip>
            </div>
          </div>

          <v-textarea
            ref="bodyTextareaRef"
            v-model="dialog.form.body"
            label="Corpo da mensagem"
            variant="outlined"
            rows="5"
            :error-messages="dialog.errors.body"
            @update:model-value="dialog.errors.body = ''"
          />

          <!-- Preview em tempo real -->
          <v-expand-transition>
            <div v-if="dialog.form.body">
              <p class="text-caption text-medium-emphasis mt-3 mb-1">Pré-visualização:</p>
              <v-sheet
                color="grey-lighten-4"
                rounded
                class="pa-3"
                style="font-size: 0.875rem; white-space: pre-wrap; word-break: break-word;"
              >{{ renderPreview(dialog.form.body) }}</v-sheet>
            </div>
          </v-expand-transition>

          <v-alert v-if="dialog.error" type="error" class="mt-3" dense>
            {{ dialog.error }}
          </v-alert>
        </v-card-text>

        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="closeDialog" :disabled="dialog.loading">
            Cancelar
          </v-btn>
          <v-btn
            color="primary"
            :loading="dialog.loading"
            @click="dialog.isEdit ? submitEdit() : submitCreate()"
          >
            {{ dialog.isEdit ? 'Salvar alterações' : 'Criar template' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ── Dialog: Confirmar exclusão ── -->
    <v-dialog v-model="deleteDialog.open" max-width="400">
      <v-card>
        <v-card-title class="pa-4">Excluir template</v-card-title>
        <v-card-text class="pa-4 pt-0">
          Tem certeza que deseja excluir o template
          <strong>"{{ deleteDialog.template?.name }}"</strong>?
          Essa ação não pode ser desfeita.
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog.open = false">Cancelar</v-btn>
          <v-btn color="error" :loading="deleteDialog.loading" @click="submitDelete">
            Excluir
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick } from 'vue'

// ── Estado principal ──────────────────────────────────────────────────────────
const templates = ref([])
const loading = ref(false)
const errorMessage = ref('')

// ── Variáveis disponíveis ─────────────────────────────────────────────────────
const availableVariables = [
  { label: 'Nome',        value: '{{nome}}'       },
  { label: 'Condomínio',  value: '{{condominio}}' },
  { label: 'Valor',       value: '{{valor}}'      },
]

// ── Ref do textarea para controle do cursor ───────────────────────────────────
const bodyTextareaRef = ref(null)

// ── Dialog criar/editar ───────────────────────────────────────────────────────
const dialog = reactive({
  open: false,
  isEdit: false,
  loading: false,
  error: '',
  editingId: null,
  form: { name: '', body: '' },
  errors: { name: '', body: '' },
})

// ── Dialog exclusão ───────────────────────────────────────────────────────────
const deleteDialog = reactive({
  open: false,
  loading: false,
  template: null,
})

// ── Helpers ───────────────────────────────────────────────────────────────────
const authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

const extractVariables = (body) => {
  const matches = body.match(/\{\{(\w+)\}\}/g) || []
  return [...new Set(matches)]
}

const renderPreview = (body) =>
  body
    .replace(/\{\{nome\}\}/g, 'João Silva')
    .replace(/\{\{condominio\}\}/g, 'Residencial Acácias')
    .replace(/\{\{valor\}\}/g, 'R$ 1.250,00')

// ── Inserção de variável na posição do cursor ─────────────────────────────────
const insertVariable = async (variable) => {
  // Tenta obter o elemento <textarea> nativo dentro do componente Vuetify
  const el = bodyTextareaRef.value?.$el?.querySelector('textarea')

  if (el) {
    const start = el.selectionStart ?? dialog.form.body.length
    const end   = el.selectionEnd   ?? dialog.form.body.length

    dialog.form.body =
      dialog.form.body.slice(0, start) +
      variable +
      dialog.form.body.slice(end)

    // Reposiciona o cursor após a variável inserida
    await nextTick()
    const newPos = start + variable.length
    el.setSelectionRange(newPos, newPos)
    el.focus()
  } else {
    // Fallback: insere no final
    dialog.form.body += variable
  }

  dialog.errors.body = ''
}

const validate = () => {
  let valid = true
  dialog.errors.name = ''
  dialog.errors.body = ''

  if (!dialog.form.name.trim()) {
    dialog.errors.name = 'O nome é obrigatório.'
    valid = false
  }
  if (!dialog.form.body.trim()) {
    dialog.errors.body = 'O corpo da mensagem é obrigatório.'
    valid = false
  }
  return valid
}

// ── CRUD ──────────────────────────────────────────────────────────────────────
const fetchTemplates = async () => {
  loading.value = true
  errorMessage.value = ''
  try {
    const res = await fetch('/api/templates', { headers: authHeader() })
    if (!res.ok) throw new Error('Erro ao carregar templates')
    templates.value = await res.json()
  } catch (e) {
    errorMessage.value = e.message
  } finally {
    loading.value = false
  }
}

const openCreateDialog = () => {
  dialog.isEdit = false
  dialog.editingId = null
  dialog.form.name = ''
  dialog.form.body = ''
  dialog.errors.name = ''
  dialog.errors.body = ''
  dialog.error = ''
  dialog.open = true
}

const openEditDialog = (template) => {
  dialog.isEdit = true
  dialog.editingId = template.id
  dialog.form.name = template.name
  dialog.form.body = template.body
  dialog.errors.name = ''
  dialog.errors.body = ''
  dialog.error = ''
  dialog.open = true
}

const closeDialog = () => {
  dialog.open = false
}

const submitCreate = async () => {
  if (!validate()) return
  dialog.loading = true
  dialog.error = ''
  try {
    const res = await fetch('/api/templates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(dialog.form),
    })
    const data = await res.json()
    if (!res.ok) {
      const msg = data.detail || 'Erro ao criar template'
      if (msg === 'Template_name_already_exists') {
        dialog.errors.name = 'Já existe um template com esse nome.'
      } else {
        dialog.error = msg
      }
      return
    }
    templates.value.unshift(data)
    dialog.open = false
  } catch (e) {
    dialog.error = e.message
  } finally {
    dialog.loading = false
  }
}

const submitEdit = async () => {
  if (!validate()) return
  dialog.loading = true
  dialog.error = ''
  try {
    const res = await fetch(`/api/templates/${dialog.editingId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(dialog.form),
    })
    const data = await res.json()
    if (!res.ok) {
      const msg = data.detail || 'Erro ao editar template'
      if (msg === 'Template_name_already_exists') {
        dialog.errors.name = 'Já existe um template com esse nome.'
      } else {
        dialog.error = msg
      }
      return
    }
    const idx = templates.value.findIndex((t) => t.id === dialog.editingId)
    if (idx !== -1) templates.value[idx] = data
    dialog.open = false
  } catch (e) {
    dialog.error = e.message
  } finally {
    dialog.loading = false
  }
}

const confirmDelete = (template) => {
  deleteDialog.template = template
  deleteDialog.open = true
}

const submitDelete = async () => {
  deleteDialog.loading = true
  try {
    const res = await fetch(`/api/templates/${deleteDialog.template.id}`, {
      method: 'DELETE',
      headers: authHeader(),
    })
    if (!res.ok) throw new Error('Erro ao excluir template')
    templates.value = templates.value.filter((t) => t.id !== deleteDialog.template.id)
    deleteDialog.open = false
  } catch (e) {
    errorMessage.value = e.message
    deleteDialog.open = false
  } finally {
    deleteDialog.loading = false
  }
}

onMounted(fetchTemplates)
</script>