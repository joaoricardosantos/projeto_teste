<template>
  <div>

    <!-- ── Cabeçalho ── -->
    <div class="d-flex align-center gap-4 mb-6">
      <div class="page-icon">
        <v-icon size="20" color="white">mdi-shield-account-outline</v-icon>
      </div>
      <div>
        <h1 class="page-title">Administração de Usuários</h1>
        <p class="page-subtitle">Gerencie acessos, aprovações e permissões da plataforma</p>
      </div>
    </div>

    <v-alert v-if="errorMessage" type="error" class="mb-5" closable @click:close="errorMessage = ''">
      {{ errorMessage }}
    </v-alert>

    <v-row>

      <!-- ── Formulário novo usuário ── -->
      <v-col cols="12" md="4">
        <v-card class="section-card" elevation="3">
          <div class="section-header">
            <div class="section-icon">
              <v-icon size="16" color="white">mdi-account-plus-outline</v-icon>
            </div>
            <div>
              <p class="section-title">Novo Usuário</p>
              <p class="section-subtitle">Criar acesso à plataforma</p>
            </div>
          </div>

          <div class="pa-5">
            <v-form @submit.prevent="handleCreateUser">
              <v-text-field
                v-model="newUser.name"
                label="Nome completo"
                required
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-account-outline"
                class="mb-3"
              />
              <v-text-field
                v-model="newUser.email"
                label="E-mail"
                type="email"
                required
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-email-outline"
                class="mb-3"
              />
              <v-text-field
                v-model="newUser.password"
                label="Senha"
                type="password"
                required
                variant="outlined"
                density="comfortable"
                prepend-inner-icon="mdi-lock-outline"
                class="mb-4"
              />

              <v-alert v-if="createUserSuccess" type="success" class="mb-3" density="compact">{{ createUserSuccess }}</v-alert>
              <v-alert v-if="createUserError"   type="error"   class="mb-3" density="compact">{{ createUserError }}</v-alert>

              <v-btn type="submit" color="primary" block size="large" :loading="isCreatingUser" prepend-icon="mdi-account-plus">
                Criar usuário
              </v-btn>
            </v-form>
          </div>
        </v-card>
      </v-col>

      <!-- ── Tabela de usuários ── -->
      <v-col cols="12" md="8">
        <v-card class="section-card" elevation="3">
          <div class="section-header">
            <div class="section-icon">
              <v-icon size="16" color="white">mdi-account-group-outline</v-icon>
            </div>
            <div>
              <p class="section-title">Usuários cadastrados</p>
              <p class="section-subtitle">Gerencie aprovações e permissões</p>
            </div>
            <v-chip size="small" variant="tonal" color="white" style="color:white; margin-left:auto;">
              {{ users.length }}
            </v-chip>
          </div>

          <v-card-text class="pa-0">
            <v-data-table
              :headers="userHeaders"
              :items="users"
              density="comfortable"
              class="elevation-0"
              no-data-text="Nenhum usuário encontrado"
            >
              <template #item.name="{ item }">
                <div class="d-flex align-center py-1" style="gap: 15px;">
                  <v-avatar size="32" :color="item.is_staff || item.is_superuser ? 'primary' : 'grey-lighten-2'">
                    <v-icon size="16" :color="item.is_staff || item.is_superuser ? 'white' : 'grey-darken-1'">
                      mdi-account
                    </v-icon>
                  </v-avatar>
                  <div>
                    <p class="font-weight-medium text-body-2 ma-0">{{ item.name }}</p>
                    <p class="text-caption text-medium-emphasis ma-0">{{ item.email }}</p>
                  </div>
                </div>
              </template>

              <template #item.status="{ item }">
                <v-chip
                  :color="item.is_approved ? 'success' : 'warning'"
                  size="x-small"
                  variant="tonal"
                >{{ item.is_approved ? 'Aprovado' : 'Pendente' }}</v-chip>
              </template>

              <template #item.role="{ item }">
                <v-chip
                  :color="item.is_staff || item.is_superuser ? 'primary' : item.is_juridico ? 'deep-purple' : 'grey'"
                  size="x-small"
                  variant="tonal"
                >{{ item.is_staff || item.is_superuser ? 'Admin' : item.is_juridico ? 'Jurídico' : 'Usuário' }}</v-chip>
              </template>

              <template #item.actions="{ item }">
                <div class="d-flex align-center gap-1 py-1">
                  <v-btn
                    v-if="!item.is_approved"
                    size="x-small" color="success" variant="tonal"
                    @click="updateUserStatus(item.id, true)"
                  >Aprovar</v-btn>
                  <v-btn
                    v-else
                    size="x-small" color="warning" variant="tonal"
                    @click="updateUserStatus(item.id, false)"
                  >Revogar</v-btn>

                  <v-btn
                    size="x-small" variant="tonal"
                    :color="item.is_staff || item.is_superuser ? 'grey' : 'primary'"
                    @click="toggleAdmin(item)"
                  >{{ item.is_staff || item.is_superuser ? 'Remover admin' : 'Tornar admin' }}</v-btn>

                  <v-btn
                    size="x-small" variant="tonal"
                    :color="item.is_juridico ? 'grey' : 'deep-purple'"
                    @click="toggleJuridico(item)"
                  >{{ item.is_juridico ? 'Remover jurídico' : 'Jurídico' }}</v-btn>

                  <v-btn
                    size="x-small" color="error" icon variant="text"
                    @click="confirmDelete(item)"
                  >
                    <v-icon size="16">mdi-delete</v-icon>
                  </v-btn>
                </div>
              </template>
            </v-data-table>
          </v-card-text>
        </v-card>
      </v-col>

    </v-row>

    <!-- ── Dialog: Confirmar exclusão ── -->
    <v-dialog v-model="deleteDialog" max-width="420" persistent>
      <v-card class="overflow-hidden">
        <div class="delete-header">
          <v-icon color="white" size="20" class="mr-2">mdi-alert</v-icon>
          Confirmar exclusão
        </div>
        <v-card-text class="pa-5">
          Tem certeza que deseja excluir o usuário
          <strong>{{ userToDelete?.name }}</strong> ({{ userToDelete?.email }})?
          <br /><br />
          <span class="text-error font-weight-medium">Esta ação não pode ser desfeita.</span>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false" :disabled="isDeleting">Cancelar</v-btn>
          <v-btn color="error" variant="elevated" :loading="isDeleting" @click="deleteUser">
            Excluir definitivamente
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const users = ref([])
const errorMessage = ref('')

const newUser = reactive({ name: '', email: '', password: '' })
const isCreatingUser = ref(false)
const createUserSuccess = ref('')
const createUserError = ref('')

const deleteDialog = ref(false)
const userToDelete = ref(null)
const isDeleting = ref(false)

const userHeaders = [
  { title: 'Usuário',    key: 'name',    sortable: true  },
  { title: 'Status',     key: 'status',  width: 110, sortable: false },
  { title: 'Permissão',  key: 'role',    width: 110, sortable: false },
  { title: 'Ações',      key: 'actions', width: 230, sortable: false },
]

const getToken = () => localStorage.getItem('access_token')

const fetchUsers = async () => {
  errorMessage.value = ''
  try {
    const response = await fetch('/api/admin/users', {
      headers: { Authorization: `Bearer ${getToken()}` },
    })
    if (!response.ok) throw new Error('Erro ao buscar usuários ou permissão negada')
    users.value = await response.json()
  } catch (error) {
    errorMessage.value = error.message
  }
}

const updateUserStatus = async (userId, isApproved) => {
  errorMessage.value = ''
  try {
    const response = await fetch('/api/admin/approve-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
      body: JSON.stringify({ user_id: userId, is_approved: isApproved }),
    })
    if (!response.ok) throw new Error('Erro ao atualizar status do usuário')
    await fetchUsers()
  } catch (error) {
    errorMessage.value = error.message
  }
}

const toggleAdmin = async (user) => {
  errorMessage.value = ''
  try {
    const response = await fetch('/api/admin/set-admin', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
      body: JSON.stringify({ user_id: user.id, make_admin: !(user.is_staff || user.is_superuser) }),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(data.detail || 'Erro ao atualizar permissão')
    await fetchUsers()
  } catch (error) {
    errorMessage.value = error.message
  }
}

const toggleJuridico = async (user) => {
  errorMessage.value = ''
  try {
    const response = await fetch('/api/admin/set-juridico', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
      body: JSON.stringify({ user_id: user.id, is_juridico: !user.is_juridico }),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(data.detail || 'Erro ao atualizar cargo jurídico')
    await fetchUsers()
  } catch (error) {
    errorMessage.value = error.message
  }
}

const confirmDelete = (user) => {
  userToDelete.value = user
  errorMessage.value = ''
  deleteDialog.value = true
}

const deleteUser = async () => {
  if (!userToDelete.value) return
  isDeleting.value = true
  try {
    const response = await fetch('/api/admin/delete-user', {
      method: 'DELETE',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
      body: JSON.stringify({ user_id: userToDelete.value.id }),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) {
      const msg = {
        Cannot_delete_own_account: 'Você não pode excluir sua própria conta.',
        Admin_privileges_required: 'Você não tem permissão para excluir usuários.',
        User_not_found: 'Usuário não encontrado.',
      }
      throw new Error(msg[data.detail] || data.detail || 'Erro ao excluir usuário')
    }
    deleteDialog.value = false
    userToDelete.value = null
    await fetchUsers()
  } catch (error) {
    deleteDialog.value = false
    errorMessage.value = error.message
  } finally {
    isDeleting.value = false
  }
}

const handleCreateUser = async () => {
  isCreatingUser.value = true
  createUserSuccess.value = ''
  createUserError.value = ''
  try {
    const response = await fetch('/api/admin/create-user', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${getToken()}` },
      body: JSON.stringify({ name: newUser.name, email: newUser.email, password: newUser.password }),
    })
    const data = await response.json().catch(() => ({}))
    if (!response.ok) throw new Error(data.detail || 'Erro ao criar usuário')
    createUserSuccess.value = 'Usuário criado com sucesso. Aguarde aprovação.'
    newUser.name = ''; newUser.email = ''; newUser.password = ''
    await fetchUsers()
  } catch (error) {
    createUserError.value = error.message
  } finally {
    isCreatingUser.value = false
  }
}

const goToDashboard = () => router.push('/dashboard')
const logout = () => { localStorage.removeItem('access_token'); router.push('/') }

onMounted(fetchUsers)
</script>

<style scoped>
.page-icon {
  width: 42px; height: 42px; border-radius: 11px;
  background: linear-gradient(135deg, #00a651 0%, #006837 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 12px rgba(0,168,81,0.3); flex-shrink: 0; margin-right: 8px;
}
.page-title    { font-size: 1.2rem; font-weight: 700; line-height: 1.3; margin: 0; }
.page-subtitle { font-size: 0.82rem; opacity: .55; margin: 2px 0 0; }

.section-card { border-radius: 14px !important; overflow: hidden; }

.section-header {
  background: linear-gradient(135deg, #006837 0%, #00a651 100%);
  padding: 14px 18px;
  display: flex; align-items: center; gap: 12px;
}
.section-icon {
  width: 30px; height: 30px; border-radius: 8px;
  background: rgba(255,255,255,0.2);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.section-title    { color: white; font-weight: 600; font-size: 0.9rem; margin: 0; }
.section-subtitle { color: rgba(255,255,255,0.7); font-size: 0.76rem; margin: 2px 0 0; }

.delete-header {
  background: linear-gradient(135deg, #b71c1c 0%, #e53935 100%);
  padding: 16px 20px;
  display: flex; align-items: center;
  color: white; font-weight: 600; font-size: 0.95rem;
}
</style>
