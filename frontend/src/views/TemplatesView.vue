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

    <!-- ── Dialog: Criar / Editar (layout duas colunas) ── -->
    <v-dialog v-model="dialog.open" max-width="960" persistent>
      <v-card>
        <v-card-title class="pa-4 pb-2 d-flex align-center">
          <v-icon class="mr-2" color="primary">mdi-message-text-outline</v-icon>
          <span class="text-h6">{{ dialog.isEdit ? 'Editar template' : 'Novo template' }}</span>
        </v-card-title>

        <v-divider />

        <v-card-text class="pa-0">
          <v-row no-gutters style="min-height: 480px;">

            <!-- ── Coluna esquerda: formulário ── -->
            <v-col cols="12" md="6" class="pa-5" style="border-right: 1px solid rgba(0,0,0,0.08);">
              <p class="text-caption text-uppercase font-weight-bold text-medium-emphasis mb-4 letter-spacing-wide">
                Edição
              </p>

              <v-text-field
                v-model="dialog.form.name"
                label="Nome do template"
                variant="outlined"
                density="comfortable"
                :error-messages="dialog.errors.name"
                class="mb-4"
                @update:model-value="dialog.errors.name = ''"
              />

              <!-- Chips de variáveis -->
              <div class="mb-3">
                <p class="text-caption text-medium-emphasis mb-2">
                  <v-icon size="14" class="mr-1">mdi-cursor-pointer</v-icon>
                  Clique para inserir uma variável:
                </p>
                <div class="d-flex gap-2 flex-wrap">
                  <v-chip
                    v-for="variable in availableVariables"
                    :key="variable.value"
                    size="small"
                    color="primary"
                    variant="tonal"
                    prepend-icon="mdi-code-braces"
                    style="cursor: pointer; user-select: none;"
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
                rows="8"
                density="comfortable"
                :error-messages="dialog.errors.body"
                @update:model-value="dialog.errors.body = ''"
              />

              <v-alert v-if="dialog.error" type="error" class="mt-2" density="compact">
                {{ dialog.error }}
              </v-alert>
            </v-col>

            <!-- ── Coluna direita: preview WhatsApp ── -->
            <v-col
              cols="12"
              md="6"
              class="pa-5 d-flex flex-column"
              style="background: #ece5dd;"
            >
              <p class="text-caption text-uppercase font-weight-bold mb-4" style="color: #54656f; letter-spacing: 0.08em;">
                Pré-visualização
              </p>

              <!-- Barra do "chat" -->
              <div
                class="d-flex align-center pa-3 mb-4 rounded-lg"
                style="background: #075e54;"
              >
                <v-avatar size="36" color="grey-lighten-2" class="mr-3">
                  <v-icon color="grey-darken-1">mdi-account</v-icon>
                </v-avatar>
                <div>
                  <p class="text-body-2 font-weight-bold ma-0" style="color: white; line-height: 1.2;">
                    {{ dialog.form.name || 'Nome do template' }}
                  </p>
                  <p class="text-caption ma-0" style="color: rgba(255,255,255,0.7);">
                    Sistema de cobrança
                  </p>
                </div>
              </div>

              <!-- Área de mensagens -->
              <div class="flex-grow-1 d-flex flex-column justify-end">

                <!-- Estado vazio -->
                <div
                  v-if="!dialog.form.body"
                  class="d-flex flex-column align-center justify-center flex-grow-1 text-center"
                  style="opacity: 0.45;"
                >
                  <v-icon size="48" style="color: #54656f;">mdi-message-outline</v-icon>
                  <p class="text-body-2 mt-2" style="color: #54656f;">
                    Digite a mensagem ao lado<br>para ver o preview aqui
                  </p>
                </div>

                <!-- Balão de mensagem -->
                <div v-else class="d-flex flex-column align-end">
                  <!-- Hora fake + balão -->
                  <div
                    class="pa-3 rounded-lg mb-1"
                    style="
                      background: #dcf8c6;
                      max-width: 88%;
                      box-shadow: 0 1px 2px rgba(0,0,0,0.15);
                      border-radius: 8px 0px 8px 8px !important;
                      position: relative;
                    "
                  >
                    <!-- Orelha do balão -->
                    <div style="
                      position: absolute;
                      top: 0; right: -8px;
                      width: 0; height: 0;
                      border-left: 8px solid #dcf8c6;
                      border-bottom: 8px solid transparent;
                    "/>

                    <p
                      class="ma-0"
                      style="
                        font-size: 0.875rem;
                        color: #111;
                        white-space: pre-wrap;
                        word-break: break-word;
                        line-height: 1.5;
                      "
                    >{{ renderPreview(dialog.form.body) }}</p>

                    <div class="d-flex align-center justify-end mt-1 gap-1">
                      <span style="font-size: 0.7rem; color: #667781;">
                        {{ currentTime }}
                      </span>
                      <v-icon size="14" color="#4fc3f7">mdi-check-all</v-icon>
                    </div>
                  </div>

                  <!-- Chips das variáveis usadas -->
                  <div v-if="extractVariables(dialog.form.body).length" class="d-flex flex-wrap gap-1 mt-2 justify-end">
                    <v-chip
                      v-for="v in extractVariables(dialog.form.body)"
                      :key="v"
                      size="x-small"
                      color="success"
                      variant="tonal"
                    >
                      {{ v }} substituído
                    </v-chip>
                  </div>
                </div>
              </div>

              <!-- Nota de rodapé -->
              <p class="text-caption mt-4 text-center" style="color: #8696a0;">
                Preview com dados de exemplo
              </p>
            </v-col>

          </v-row>
        </v-card-text>

        <v-divider />

        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="closeDialog" :disabled="dialog.loading">
            Cancelar
          </v-btn>
          <v-btn
            color="primary"
            variant="elevated"
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
import { ref, reactive, computed, onMounted, nextTick } from 'vue'

// ── Estado principal ──────────────────────────────────────────────────────────
const templates = ref([])
const loading = ref(false)
const errorMessage = ref('')

// ── Variáveis disponíveis ─────────────────────────────────────────────────────
const availableVariables = [
  { label: 'Nome',       value: '{{nome}}'       },
  { label: 'Condomínio', value: '{{condominio}}' },
  { label: 'Valor',      value: '{{valor}}'      },
]

// ── Hora atual para o preview ─────────────────────────────────────────────────
const currentTime = computed(() => {
  const now = new Date()
  return now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
})

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
  const el = bodyTextareaRef.value?.$el?.querySelector('textarea')

  if (el) {
    const start = el.selectionStart ?? dialog.form.body.length
    const end   = el.selectionEnd   ?? dialog.form.body.length

    dialog.form.body =
      dialog.form.body.slice(0, start) +
      variable +
      dialog.form.body.slice(end)

    await nextTick()
    const newPos = start + variable.length
    el.setSelectionRange(newPos, newPos)
    el.focus()
  } else {
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
    const text = await res.text()
    let data = {}
    try { data = JSON.parse(text) } catch (_) { data = { detail: text } }
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