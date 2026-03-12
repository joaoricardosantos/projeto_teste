<template>
  <v-container>
    <!-- Cabeçalho -->
    <v-row class="mb-4" align="center" justify="space-between">
      <v-col cols="12" sm="6">
        <h1 class="text-h5 font-weight-bold">Administração</h1>
      </v-col>
      <v-col cols="12" sm="6" class="text-sm-right text-left">
        <v-btn variant="text" class="mr-2" @click="goToDashboard">Enviar mensagens</v-btn>
        <v-btn icon @click="logout"><v-icon>mdi-logout</v-icon></v-btn>
      </v-col>
    </v-row>

    <!-- Tabs -->
    <v-tabs v-model="activeTab" color="primary" class="mb-6">
      <v-tab value="users">Usuários</v-tab>
      <v-tab value="templates">Templates de mensagem</v-tab>
    </v-tabs>

    <v-tabs-window v-model="activeTab">

      <!-- ══════════════════════════════════════ -->
      <!-- ABA: USUÁRIOS                          -->
      <!-- ══════════════════════════════════════ -->
      <v-tabs-window-item value="users">

        <v-row class="mb-6">
          <v-col cols="12" md="6">
            <v-card elevation="4" class="pa-4">
              <h2 class="text-subtitle-1 font-weight-bold mb-4">Novo usuário</h2>
              <v-form @submit.prevent="handleCreateUser">
                <v-text-field v-model="newUser.name" label="Nome completo" required variant="outlined" class="mb-3" />
                <v-text-field v-model="newUser.email" label="E-mail" type="email" required variant="outlined" class="mb-3" />
                <v-text-field v-model="newUser.password" label="Senha" type="password" required variant="outlined" class="mb-3" />
                <v-alert v-if="createUserSuccess" type="success" class="mb-3" density="compact">{{ createUserSuccess }}</v-alert>
                <v-alert v-if="createUserError" type="error" class="mb-3" density="compact">{{ createUserError }}</v-alert>
                <v-btn type="submit" color="primary" :loading="isCreatingUser">Criar usuário</v-btn>
              </v-form>
            </v-card>
          </v-col>
        </v-row>

        <v-alert v-if="errorMessage" type="error" class="mb-4" density="compact">{{ errorMessage }}</v-alert>

        <v-card elevation="4">
          <v-table>
            <thead>
              <tr>
                <th>Nome</th>
                <th>E-mail</th>
                <th class="text-center">Status</th>
                <th class="text-center">Permissão</th>
                <th class="text-center">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="user in users" :key="user.id">
                <td>{{ user.name }}</td>
                <td>{{ user.email }}</td>
                <td class="text-center">
                  <v-chip :color="user.is_approved ? 'success' : 'warning'" size="small">
                    {{ user.is_approved ? 'Aprovado' : 'Pendente' }}
                  </v-chip>
                </td>
                <td class="text-center">
                  <v-chip :color="user.is_staff || user.is_superuser ? 'primary' : 'grey'" size="small">
                    {{ user.is_staff || user.is_superuser ? 'Admin' : 'Usuário' }}
                  </v-chip>
                </td>
                <td class="text-center">
                  <v-btn v-if="!user.is_approved" color="success" size="small" @click="updateUserStatus(user.id, true)">Aprovar</v-btn>
                  <v-btn v-else color="error" size="small" @click="updateUserStatus(user.id, false)">Revogar</v-btn>
                  <v-btn class="ml-2" size="small" :color="user.is_staff || user.is_superuser ? 'secondary' : 'primary'" @click="toggleAdmin(user)">
                    {{ user.is_staff || user.is_superuser ? 'Remover admin' : 'Tornar admin' }}
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-tabs-window-item>

      <!-- ══════════════════════════════════════ -->
      <!-- ABA: TEMPLATES                         -->
      <!-- ══════════════════════════════════════ -->
      <v-tabs-window-item value="templates">

        <v-row>
          <!-- Formulário -->
          <v-col cols="12" md="6">
            <v-card elevation="4" class="pa-4">
              <h2 class="text-subtitle-1 font-weight-bold mb-1">
                {{ editingTemplate ? 'Editar template' : 'Novo template' }}
              </h2>
              <p class="text-caption text-medium-emphasis mb-4">
                Variáveis disponíveis:
                <code @click="insertVar('{nome}')" class="var-chip">&#123;nome&#125;</code>
                <code @click="insertVar('{condominio}')" class="var-chip">&#123;condominio&#125;</code>
                <code @click="insertVar('{valor}')" class="var-chip">&#123;valor&#125;</code>
                <code @click="insertVar('{data_atraso}')" class="var-chip">&#123;data_atraso&#125;</code>
                <span class="text-caption"> (clique para inserir)</span>
              </p>

              <v-form @submit.prevent="handleSaveTemplate">
                <v-text-field
                  v-model="templateForm.name"
                  label="Nome do template"
                  variant="outlined"
                  required
                  class="mb-3"
                />
                <v-textarea
                  ref="bodyTextareaRef"
                  v-model="templateForm.body"
                  label="Corpo da mensagem"
                  variant="outlined"
                  rows="7"
                  required
                  class="mb-3"
                  hint="Use as variáveis acima para personalizar a mensagem"
                  persistent-hint
                />
                <v-switch
                  v-model="templateForm.is_active"
                  label="Definir como template ativo"
                  color="primary"
                  class="mb-3"
                />
                <v-alert v-if="templateSuccess" type="success" density="compact" class="mb-3">{{ templateSuccess }}</v-alert>
                <v-alert v-if="templateError" type="error" density="compact" class="mb-3">{{ templateError }}</v-alert>
                <div class="d-flex gap-2">
                  <v-btn type="submit" color="primary" :loading="isSavingTemplate">
                    {{ editingTemplate ? 'Salvar alterações' : 'Criar template' }}
                  </v-btn>
                  <v-btn v-if="editingTemplate" variant="text" @click="cancelEdit">Cancelar</v-btn>
                </div>
              </v-form>
            </v-card>
          </v-col>

          <!-- Preview WhatsApp -->
          <v-col cols="12" md="6">
            <v-card elevation="4" class="pa-4">
              <h2 class="text-subtitle-1 font-weight-bold mb-3">Preview da mensagem</h2>

              <!-- Bolha estilo WhatsApp -->
              <div class="whatsapp-bg pa-4 rounded-lg mb-2">
                <div class="whatsapp-bubble">
                  <pre class="whatsapp-text">{{ previewRendered }}</pre>
                  <span class="whatsapp-time">agora ✓✓</span>
                </div>
              </div>
              <p class="text-caption text-medium-emphasis">
                Os valores acima são apenas exemplos para visualização.
              </p>
            </v-card>
          </v-col>
        </v-row>

        <!-- Lista de templates -->
        <v-card elevation="4" class="mt-6">
          <v-card-title class="pa-4 text-subtitle-1 font-weight-bold">Templates cadastrados</v-card-title>
          <v-table>
            <thead>
              <tr>
                <th>Nome</th>
                <th class="text-center">Status</th>
                <th class="text-center">Ações</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="!templates.length">
                <td colspan="3" class="text-center text-medium-emphasis py-4">Nenhum template cadastrado.</td>
              </tr>
              <tr v-for="t in templates" :key="t.id">
                <td>{{ t.name }}</td>
                <td class="text-center">
                  <v-chip :color="t.is_active ? 'success' : 'grey'" size="small">
                    {{ t.is_active ? 'Ativo' : 'Inativo' }}
                  </v-chip>
                </td>
                <td class="text-center">
                  <v-btn v-if="!t.is_active" size="small" color="success" class="mr-1" @click="activateTemplate(t.id)">
                    Ativar
                  </v-btn>
                  <v-btn size="small" color="primary" variant="outlined" class="mr-1" @click="startEdit(t)">
                    Editar
                  </v-btn>
                  <v-btn size="small" color="error" variant="outlined" @click="deleteTemplate(t.id)">
                    Excluir
                  </v-btn>
                </td>
              </tr>
            </tbody>
          </v-table>
        </v-card>
      </v-tabs-window-item>

    </v-tabs-window>
  </v-container>
</template>

<script setup>
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

// ── Tabs ──────────────────────────────────────
const activeTab = ref('users')

// ── Usuários ──────────────────────────────────
const users           = ref([])
const errorMessage    = ref('')
const newUser         = reactive({ name: '', email: '', password: '' })
const isCreatingUser  = ref(false)
const createUserSuccess = ref('')
const createUserError   = ref('')

// ── Templates ─────────────────────────────────
const templates       = ref([])
const editingTemplate = ref(null)
const isSavingTemplate = ref(false)
const templateSuccess = ref('')
const templateError   = ref('')
const bodyTextareaRef = ref(null)

const templateForm = reactive({
  name: '',
  body: '',
  is_active: false,
})

// Dados de exemplo para preview
const PREVIEW_VARS = {
  nome: 'João Silva',
  condominio: 'Residencial das Flores',
  valor: '1.250,00',
  data_atraso: '01/02/2026',
}

const previewRendered = computed(() => {
  if (!templateForm.body) return '(escreva a mensagem ao lado para visualizar)'
  try {
    return templateForm.body
      .replace(/\{nome\}/g, PREVIEW_VARS.nome)
      .replace(/\{condominio\}/g, PREVIEW_VARS.condominio)
      .replace(/\{valor\}/g, PREVIEW_VARS.valor)
      .replace(/\{data_atraso\}/g, PREVIEW_VARS.data_atraso)
  } catch {
    return templateForm.body
  }
})

// Insere variável no cursor do textarea
const insertVar = (variable) => {
  const el = bodyTextareaRef.value?.$el?.querySelector('textarea')
  if (!el) {
    templateForm.body += variable
    return
  }
  const start = el.selectionStart
  const end   = el.selectionEnd
  templateForm.body =
    templateForm.body.slice(0, start) + variable + templateForm.body.slice(end)
  setTimeout(() => {
    el.focus()
    el.setSelectionRange(start + variable.length, start + variable.length)
  }, 0)
}

// ── API helpers ───────────────────────────────
const authHeaders = () => ({
  'Content-Type': 'application/json',
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

// ── Usuários ──────────────────────────────────
const fetchUsers = async () => {
  try {
    const res = await fetch('/api/admin/users', { headers: authHeaders() })
    if (!res.ok) throw new Error('Erro ao buscar usuários ou permissão negada')
    users.value = await res.json()
  } catch (e) { errorMessage.value = e.message }
}

const updateUserStatus = async (userId, isApproved) => {
  try {
    const res = await fetch('/api/admin/approve-user', {
      method: 'POST', headers: authHeaders(),
      body: JSON.stringify({ user_id: userId, is_approved: isApproved }),
    })
    if (!res.ok) throw new Error('Erro ao atualizar status')
    await fetchUsers()
  } catch (e) { errorMessage.value = e.message }
}

const toggleAdmin = async (user) => {
  try {
    const res = await fetch('/api/admin/set-admin', {
      method: 'POST', headers: authHeaders(),
      body: JSON.stringify({ user_id: user.id, make_admin: !(user.is_staff || user.is_superuser) }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || 'Erro ao atualizar permissão')
    await fetchUsers()
  } catch (e) { errorMessage.value = e.message }
}

const handleCreateUser = async () => {
  isCreatingUser.value = true
  createUserSuccess.value = ''
  createUserError.value = ''
  try {
    const res = await fetch('/api/admin/create-user', {
      method: 'POST', headers: authHeaders(),
      body: JSON.stringify({ name: newUser.name, email: newUser.email, password: newUser.password }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || 'Erro ao criar usuário')
    createUserSuccess.value = 'Usuário criado com sucesso. Aguarde aprovação.'
    Object.assign(newUser, { name: '', email: '', password: '' })
    await fetchUsers()
  } catch (e) { createUserError.value = e.message }
  finally { isCreatingUser.value = false }
}

// ── Templates ─────────────────────────────────
const fetchTemplates = async () => {
  try {
    const res = await fetch('/api/admin/templates', { headers: authHeaders() })
    if (!res.ok) throw new Error()
    templates.value = await res.json()
  } catch { /* sem templates ainda */ }
}

const handleSaveTemplate = async () => {
  isSavingTemplate.value = true
  templateSuccess.value = ''
  templateError.value = ''
  try {
    const url    = editingTemplate.value
      ? `/api/admin/templates/${editingTemplate.value}`
      : '/api/admin/templates'
    const method = editingTemplate.value ? 'PUT' : 'POST'
    const res = await fetch(url, {
      method, headers: authHeaders(),
      body: JSON.stringify({ ...templateForm }),
    })
    const data = await res.json().catch(() => ({}))
    if (!res.ok) throw new Error(data.detail || 'Erro ao salvar template')
    templateSuccess.value = editingTemplate.value ? 'Template atualizado!' : 'Template criado!'
    cancelEdit()
    await fetchTemplates()
  } catch (e) { templateError.value = e.message }
  finally { isSavingTemplate.value = false }
}

const startEdit = (t) => {
  editingTemplate.value = t.id
  Object.assign(templateForm, { name: t.name, body: t.body, is_active: t.is_active })
  activeTab.value = 'templates'
  templateSuccess.value = ''
  templateError.value = ''
}

const cancelEdit = () => {
  editingTemplate.value = null
  Object.assign(templateForm, { name: '', body: '', is_active: false })
}

const activateTemplate = async (id) => {
  try {
    const res = await fetch(`/api/admin/templates/${id}/activate`, {
      method: 'POST', headers: authHeaders(),
    })
    if (!res.ok) throw new Error()
    await fetchTemplates()
  } catch { templateError.value = 'Erro ao ativar template' }
}

const deleteTemplate = async (id) => {
  if (!confirm('Deseja excluir este template?')) return
  try {
    const res = await fetch(`/api/admin/templates/${id}`, {
      method: 'DELETE', headers: authHeaders(),
    })
    if (!res.ok) throw new Error()
    await fetchTemplates()
  } catch { templateError.value = 'Erro ao excluir template' }
}

// ── Nav ───────────────────────────────────────
const goToDashboard = () => router.push('/dashboard')
const logout = () => { localStorage.removeItem('access_token'); router.push('/') }

onMounted(() => { fetchUsers(); fetchTemplates() })
</script>

<style scoped>
.var-chip {
  background: #e8f5e9;
  color: #2e7d32;
  padding: 2px 6px;
  border-radius: 4px;
  margin: 0 2px;
  cursor: pointer;
  font-size: 0.78rem;
  transition: background 0.15s;
}
.var-chip:hover { background: #c8e6c9; }

.whatsapp-bg {
  background: #e5ddd5;
  min-height: 120px;
}
.whatsapp-bubble {
  background: #dcf8c6;
  border-radius: 0 8px 8px 8px;
  padding: 10px 14px 6px;
  display: inline-block;
  max-width: 100%;
  position: relative;
  box-shadow: 0 1px 2px rgba(0,0,0,0.15);
}
.whatsapp-text {
  font-family: 'Segoe UI', sans-serif;
  font-size: 0.9rem;
  white-space: pre-wrap;
  word-break: break-word;
  margin: 0 0 4px;
  color: #111;
}
.whatsapp-time {
  font-size: 0.7rem;
  color: #777;
  float: right;
  margin-left: 8px;
}
</style>