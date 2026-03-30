<template>
  <div>

    <!-- ── Cabeçalho ── -->
    <div class="d-flex align-center justify-space-between flex-wrap gap-3 mb-6">
      <div class="d-flex align-center gap-4">
        <div class="page-icon">
          <v-icon size="20" color="white">mdi-message-text-outline</v-icon>
        </div>
        <div>
          <h1 class="page-title">Templates de Mensagem</h1>
          <p class="page-subtitle">Crie e gerencie mensagens reutilizáveis com variáveis dinâmicas</p>
        </div>
      </div>
      <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
        Novo template
      </v-btn>
    </div>

    <v-alert v-if="errorMessage" type="error" class="mb-4" closable @click:close="errorMessage = ''">
      {{ errorMessage }}
    </v-alert>

    <!-- Loading -->
    <div v-if="loading" class="d-flex justify-center my-16">
      <v-progress-circular indeterminate color="primary" size="48" />
    </div>

    <!-- Vazio -->
    <v-card v-else-if="templates.length === 0" elevation="2" class="empty-card">
      <div class="d-flex flex-column align-center pa-16">
        <div class="empty-icon mb-5">
          <v-icon size="36" color="white">mdi-message-text-outline</v-icon>
        </div>
        <p class="text-h6 font-weight-bold mb-2">Nenhum template criado</p>
        <p class="text-body-2 text-medium-emphasis mb-6 text-center" style="max-width:320px;">
          Crie templates personalizados para automatizar e padronizar os disparos de cobrança.
        </p>
        <v-btn color="primary" prepend-icon="mdi-plus" @click="openCreateDialog">
          Criar meu primeiro template
        </v-btn>
      </div>
    </v-card>

    <!-- Grid de templates -->
    <v-row v-else>
      <v-col v-for="template in templates" :key="template.id" cols="12" md="6">
        <v-card class="template-card h-100" elevation="3">

          <!-- Header do card -->
          <div class="template-card-header">
            <div class="template-icon">
              <v-icon size="18" color="white">mdi-message-text</v-icon>
            </div>
            <span class="template-name">{{ template.name }}</span>
            <v-spacer />
            <v-btn icon size="small" variant="text" color="grey-darken-1" @click="openEditDialog(template)">
              <v-icon size="17">mdi-pencil</v-icon>
            </v-btn>
            <v-btn icon size="small" variant="text" color="error" @click="confirmDelete(template)">
              <v-icon size="17">mdi-delete</v-icon>
            </v-btn>
          </div>

          <v-card-text class="pa-4">
            <!-- Corpo da mensagem -->
            <v-sheet
              color="grey-lighten-4"
              rounded="lg"
              class="pa-3 mb-3"
              style="font-size: 0.83rem; white-space: pre-wrap; word-break: break-word; min-height: 64px; line-height: 1.6;"
            >{{ template.body }}</v-sheet>

            <!-- Variáveis usadas -->
            <div v-if="extractVariables(template.body).length" class="d-flex flex-wrap gap-1 mb-3">
              <v-chip
                v-for="variable in extractVariables(template.body)"
                :key="variable"
                size="x-small"
                color="primary"
                variant="tonal"
                prepend-icon="mdi-code-braces"
              >{{ variable }}</v-chip>
            </div>

            <p class="text-caption text-disabled">
              <v-icon size="11" class="mr-1">mdi-clock-outline</v-icon>
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
    <v-dialog v-model="dialog.open" max-width="960" persistent>
      <v-card class="overflow-hidden">
        <v-card-title class="pa-0">
          <div class="dialog-header">
            <div class="template-icon mr-3">
              <v-icon size="18" color="white">mdi-message-text-outline</v-icon>
            </div>
            <span>{{ dialog.isEdit ? 'Editar template' : 'Novo template' }}</span>
          </div>
        </v-card-title>

        <v-card-text class="pa-0">
          <v-row no-gutters style="min-height: 480px;">

            <!-- Formulário -->
            <v-col cols="12" md="6" class="pa-5" style="border-right: 1px solid rgba(0,0,0,0.08);">
              <p class="text-caption text-uppercase font-weight-bold text-medium-emphasis mb-4" style="letter-spacing:.06em;">
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

              <div class="mb-3">
                <p class="text-caption text-medium-emphasis mb-2">
                  <v-icon size="13" class="mr-1">mdi-cursor-pointer</v-icon>
                  Clique para inserir uma variável:
                </p>
                <div class="d-flex gap-2 flex-wrap">
                  <v-chip
                    v-for="variable in availableVariables"
                    :key="variable.value"
                    size="small" color="primary" variant="tonal"
                    prepend-icon="mdi-code-braces"
                    style="cursor:pointer; user-select:none;"
                    @click="insertVariable(variable.value)"
                  >{{ variable.label }}</v-chip>
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

            <!-- Preview WhatsApp -->
            <v-col cols="12" md="6" class="pa-5 d-flex flex-column" style="background: #ece5dd;">
              <p class="text-caption text-uppercase font-weight-bold mb-4" style="color:#54656f; letter-spacing:.08em;">
                Pré-visualização
              </p>

              <div class="d-flex align-center pa-3 mb-4 rounded-lg" style="background:#075e54;">
                <v-avatar size="36" color="grey-lighten-2" class="mr-3">
                  <v-icon color="grey-darken-1">mdi-account</v-icon>
                </v-avatar>
                <div>
                  <p class="text-body-2 font-weight-bold ma-0" style="color:white; line-height:1.2;">
                    {{ dialog.form.name || 'Nome do template' }}
                  </p>
                  <p class="text-caption ma-0" style="color:rgba(255,255,255,.7);">Sistema de cobrança</p>
                </div>
              </div>

              <div class="flex-grow-1 d-flex flex-column justify-end">
                <div v-if="!dialog.form.body" class="d-flex flex-column align-center justify-center flex-grow-1 text-center" style="opacity:.45;">
                  <v-icon size="48" style="color:#54656f;">mdi-message-outline</v-icon>
                  <p class="text-body-2 mt-2" style="color:#54656f;">Digite a mensagem ao lado<br>para ver o preview aqui</p>
                </div>

                <div v-else class="d-flex flex-column align-end">
                  <div class="pa-3 mb-1" style="background:#dcf8c6; max-width:88%; box-shadow:0 1px 2px rgba(0,0,0,.15); border-radius:8px 0 8px 8px; position:relative;">
                    <div style="position:absolute;top:0;right:-8px;width:0;height:0;border-left:8px solid #dcf8c6;border-bottom:8px solid transparent;" />
                    <p class="ma-0" style="font-size:.875rem;color:#111;white-space:pre-wrap;word-break:break-word;line-height:1.5;">
                      {{ renderPreview(dialog.form.body) }}
                    </p>
                    <div class="d-flex align-center justify-end mt-1 gap-1">
                      <span style="font-size:.7rem;color:#667781;">{{ currentTime }}</span>
                      <v-icon size="14" color="#4fc3f7">mdi-check-all</v-icon>
                    </div>
                  </div>

                  <div v-if="extractVariables(dialog.form.body).length" class="d-flex flex-wrap gap-1 mt-2 justify-end">
                    <v-chip v-for="v in extractVariables(dialog.form.body)" :key="v" size="x-small" color="success" variant="tonal">
                      {{ v }} substituído
                    </v-chip>
                  </div>
                </div>
              </div>

              <p class="text-caption mt-4 text-center" style="color:#8696a0;">Preview com dados de exemplo</p>
            </v-col>
          </v-row>
        </v-card-text>

        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="closeDialog" :disabled="dialog.loading">Cancelar</v-btn>
          <v-btn color="primary" variant="elevated" :loading="dialog.loading" @click="dialog.isEdit ? submitEdit() : submitCreate()">
            {{ dialog.isEdit ? 'Salvar alterações' : 'Criar template' }}
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ── Dialog: Excluir ── -->
    <v-dialog v-model="deleteDialog.open" max-width="400">
      <v-card>
        <v-card-title class="pa-4">Excluir template</v-card-title>
        <v-card-text class="pa-4 pt-0">
          Tem certeza que deseja excluir <strong>"{{ deleteDialog.template?.name }}"</strong>? Essa ação não pode ser desfeita.
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog.open = false">Cancelar</v-btn>
          <v-btn color="error" :loading="deleteDialog.loading" @click="submitDelete">Excluir</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, nextTick } from 'vue'

const templates    = ref([])
const loading      = ref(false)
const errorMessage = ref('')

const availableVariables = [
  { label: 'Condomínio',         value: '{{condominio}}' },
  { label: 'Bloco',              value: '{{bloco}}'      },
  { label: 'Unidade',            value: '{{unidade}}'    },
  { label: 'Nome',               value: '{{nome}}'       },
  { label: 'Qtd Inadimplências', value: '{{qtd}}'        },
  { label: 'Competência',        value: '{{competencia}}'},
  { label: 'Vencimento',         value: '{{vencimento}}' },
  { label: 'Valor Total',        value: '{{valor}}'      },
]

const currentTime = computed(() => {
  const now = new Date()
  return now.toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
})

const bodyTextareaRef = ref(null)

const dialog = reactive({
  open: false, isEdit: false, loading: false,
  error: '', editingId: null,
  form: { name: '', body: '' },
  errors: { name: '', body: '' },
})

const deleteDialog = reactive({ open: false, loading: false, template: null })

const authHeader = () => ({ Authorization: `Bearer ${localStorage.getItem('access_token')}` })

const extractVariables = (body) => {
  const matches = body.match(/\{\{(\w+)\}\}/g) || []
  return [...new Set(matches)]
}

const renderPreview = (body) =>
  body
    .replace(/\{\{condominio\}\}/g, 'Residencial Acácias')
    .replace(/\{\{unidade\}\}/g, '315 SALA')
    .replace(/\{\{nome\}\}/g, 'João Silva')
    .replace(/\{\{qtd\}\}/g, '5')
    .replace(/\{\{competencia\}\}/g, '10/2025')
    .replace(/\{\{vencimento\}\}/g, '01/11/2025')
    .replace(/\{\{valor\}\}/g, 'R$ 1.250,00')

const insertVariable = async (variable) => {
  const el = bodyTextareaRef.value?.$el?.querySelector('textarea')
  if (el) {
    const start = el.selectionStart ?? dialog.form.body.length
    const end   = el.selectionEnd   ?? dialog.form.body.length
    dialog.form.body = dialog.form.body.slice(0, start) + variable + dialog.form.body.slice(end)
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
  if (!dialog.form.name.trim()) { dialog.errors.name = 'O nome é obrigatório.'; valid = false }
  if (!dialog.form.body.trim()) { dialog.errors.body = 'O corpo da mensagem é obrigatório.'; valid = false }
  return valid
}

const fetchTemplates = async () => {
  loading.value = true; errorMessage.value = ''
  try {
    const res = await fetch('/api/templates', { headers: authHeader() })
    if (!res.ok) throw new Error('Erro ao carregar templates')
    templates.value = await res.json()
  } catch (e) {
    errorMessage.value = e.message
  } finally { loading.value = false }
}

const openCreateDialog = () => {
  dialog.isEdit = false; dialog.editingId = null
  dialog.form.name = ''; dialog.form.body = ''
  dialog.errors.name = ''; dialog.errors.body = ''
  dialog.error = ''; dialog.open = true
}

const openEditDialog = (template) => {
  dialog.isEdit = true; dialog.editingId = template.id
  dialog.form.name = template.name; dialog.form.body = template.body
  dialog.errors.name = ''; dialog.errors.body = ''
  dialog.error = ''; dialog.open = true
}

const closeDialog = () => { dialog.open = false }

const submitCreate = async () => {
  if (!validate()) return
  dialog.loading = true; dialog.error = ''
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
      if (msg === 'Template_name_already_exists') dialog.errors.name = 'Já existe um template com esse nome.'
      else dialog.error = msg
      return
    }
    templates.value.unshift(data); dialog.open = false
  } catch (e) { dialog.error = e.message }
  finally { dialog.loading = false }
}

const submitEdit = async () => {
  if (!validate()) return
  dialog.loading = true; dialog.error = ''
  try {
    const res = await fetch(`/api/templates/update?tid=${dialog.editingId}`, {
      method: 'PUT',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify(dialog.form),
    })
    const data = await res.json()
    if (!res.ok) {
      const msg = data.detail || 'Erro ao editar template'
      if (msg === 'Template_name_already_exists') dialog.errors.name = 'Já existe um template com esse nome.'
      else dialog.error = msg
      return
    }
    const idx = templates.value.findIndex((t) => t.id === dialog.editingId)
    if (idx !== -1) templates.value[idx] = data
    dialog.open = false
  } catch (e) { dialog.error = e.message }
  finally { dialog.loading = false }
}

const confirmDelete = (template) => { deleteDialog.template = template; deleteDialog.open = true }

const submitDelete = async () => {
  deleteDialog.loading = true
  try {
    const res = await fetch(`/api/templates/remove`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body: JSON.stringify({ tid: deleteDialog.template.id }),
    })
    if (!res.ok) throw new Error('Erro ao excluir template')
    templates.value = templates.value.filter((t) => t.id !== deleteDialog.template.id)
    deleteDialog.open = false
  } catch (e) { errorMessage.value = e.message; deleteDialog.open = false }
  finally { deleteDialog.loading = false }
}

onMounted(fetchTemplates)
</script>

<style scoped>
.page-icon {
  width: 42px; height: 42px; border-radius: 11px;
  background: linear-gradient(135deg, #34d399 0%, #059669 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(5,150,105,0.28); flex-shrink: 0; margin-right: 8px;
}
.page-title    { font-size: 1.2rem; font-weight: 700; line-height: 1.3; margin: 0; }
.page-subtitle { font-size: 0.82rem; opacity: .55; margin: 2px 0 0; }

/* Empty state */
.empty-card { border-radius: 14px !important; }
.empty-icon {
  width: 72px; height: 72px; border-radius: 18px;
  background: linear-gradient(135deg, #34d399 0%, #059669 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 0 0 1px rgba(52,211,153,0.2), 0 8px 24px rgba(5,150,105,0.28);
}

/* Template card */
.template-card { border-radius: 14px !important; overflow: hidden; }
.template-card-header {
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  border-left: 3px solid #34d399;
  padding: 12px 14px;
  display: flex; align-items: center; gap: 10px;
}
.template-icon {
  width: 30px; height: 30px; border-radius: 8px;
  background: linear-gradient(135deg, #34d399, #059669);
  box-shadow: 0 2px 8px rgba(5,150,105,0.3);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.template-name { color: #0f172a; font-weight: 600; font-size: 0.88rem; flex: 1; min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

/* Dialog header */
.dialog-header {
  background: #f8fafc;
  border-bottom: 1px solid #e2e8f0;
  border-left: 3px solid #34d399;
  padding: 14px 20px;
  display: flex; align-items: center;
  color: #0f172a; font-size: 0.95rem; font-weight: 600;
}
</style>
