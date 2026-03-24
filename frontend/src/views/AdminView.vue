<template>
  <v-container>
    <v-row class="mb-4" align="center" justify="space-between">
      <v-col cols="12" sm="6">
        <h1 class="text-h5 font-weight-bold">Administração de Usuários</h1>
      </v-col>
      <v-col cols="12" sm="6" class="text-sm-right text-left">
        <v-btn variant="text" class="mr-2" @click="goToDashboard">Dashboard</v-btn>
        <v-btn icon @click="logout"><v-icon>mdi-logout</v-icon></v-btn>
      </v-col>
    </v-row>

    <!-- Criar usuário -->
    <v-row class="mb-6">
      <v-col cols="12" md="6">
        <v-card elevation="4" class="pa-4">
          <h2 class="text-subtitle-1 font-weight-bold mb-4">Novo usuário</h2>
          <v-form @submit.prevent="handleCreateUser">
            <v-text-field v-model="newUser.name" label="Nome completo" required variant="outlined" class="mb-3" />
            <v-text-field v-model="newUser.email" label="E-mail" type="email" required variant="outlined" class="mb-3" />
            <v-text-field v-model="newUser.password" label="Senha" type="password" required variant="outlined" class="mb-3" />
            <v-alert v-if="createUserSuccess" type="success" class="mb-3" dense>{{ createUserSuccess }}</v-alert>
            <v-alert v-if="createUserError" type="error" class="mb-3" dense>{{ createUserError }}</v-alert>
            <v-btn type="submit" color="primary" :loading="isCreatingUser">Criar usuário</v-btn>
          </v-form>
        </v-card>
      </v-col>
    </v-row>

    <v-alert v-if="errorMessage" type="error" class="mb-4" dense>{{ errorMessage }}</v-alert>

    <!-- Tabela de usuários -->
    <v-card elevation="4">
      <v-table>
        <thead>
          <tr>
            <th class="text-left">Nome</th>
            <th class="text-left">E-mail</th>
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
              <v-chip :color="user.is_approved ? 'success' : 'warning'" text-color="white" size="small">
                {{ user.is_approved ? 'Aprovado' : 'Pendente' }}
              </v-chip>
            </td>
            <td class="text-center">
              <v-chip :color="user.is_staff || user.is_superuser ? 'primary' : user.is_juridico ? 'deep-purple' : 'grey'" text-color="white" size="small">
                {{ user.is_staff || user.is_superuser ? 'Admin' : user.is_juridico ? 'Jurídico' : 'Usuário' }}
              </v-chip>
            </td>
            <td class="text-center">
              <v-btn v-if="!user.is_approved" color="success" size="small" class="mr-1" @click="updateUserStatus(user.id, true)">Aprovar</v-btn>
              <v-btn v-else color="warning" size="small" class="mr-1" @click="updateUserStatus(user.id, false)">Revogar</v-btn>
              <v-btn size="small" class="mr-1" :color="user.is_staff || user.is_superuser ? 'secondary' : 'primary'" @click="toggleAdmin(user)">
                {{ user.is_staff || user.is_superuser ? 'Remover admin' : 'Tornar admin' }}
              </v-btn>
              <v-btn size="small" class="mr-1" :color="user.is_juridico ? 'secondary' : 'deep-purple'" @click="toggleJuridico(user)">
                {{ user.is_juridico ? 'Remover jurídico' : 'Jurídico' }}
              </v-btn>
              <v-btn size="small" color="error" icon @click="confirmDelete(user)">
                <v-icon>mdi-delete</v-icon>
              </v-btn>
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>

    <!-- Diálogo de confirmação -->
    <v-dialog v-model="deleteDialog" max-width="420" persistent>
      <v-card>
        <v-card-title class="text-h6 pa-4">Confirmar exclusão</v-card-title>
        <v-card-text class="px-4">
          Tem certeza que deseja excluir o usuário
          <strong>{{ userToDelete?.name }}</strong> ({{ userToDelete?.email }})?
          <br /><br />
          <span class="text-error">Esta ação não pode ser desfeita.</span>
        </v-card-text>
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="deleteDialog = false" :disabled="isDeleting">Cancelar</v-btn>
          <v-btn color="error" variant="elevated" :loading="isDeleting" @click="deleteUser">
            Excluir definitivamente
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>
  </v-container>
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
    newUser.name = ''
    newUser.email = ''
    newUser.password = ''
    await fetchUsers()
  } catch (error) {
    createUserError.value = error.message
  } finally {
    isCreatingUser.value = false
  }
}

const goToDashboard = () => router.push('/dashboard')
const logout = () => {
  localStorage.removeItem('access_token')
  router.push('/')
}

onMounted(fetchUsers)
</script>