<template>
  <v-container>
    <v-row class="mb-4" align="center" justify="space-between">
      <v-col cols="12" sm="6">
        <h1 class="text-h5 font-weight-bold">Administração de Usuários</h1>
      </v-col>
      <v-col cols="12" sm="6" class="text-sm-right text-left">
        <v-btn
          color="primary"
          class="mr-4 mb-2"
          :loading="isExporting"
          @click="exportDefaulters"
        >
          Exportar inadimplentes (Excel)
        </v-btn>
        <v-btn variant="text" class="mr-2" @click="goToDashboard">
          Dashboard
        </v-btn>
        <v-btn icon @click="logout">
          <v-icon>mdi-logout</v-icon>
        </v-btn>
      </v-col>
    </v-row>

    <v-row class="mb-6">
      <v-col cols="12" md="6">
        <v-card elevation="4" class="pa-4">
          <h2 class="text-subtitle-1 font-weight-bold mb-4">
            Novo usuário
          </h2>
          <v-form @submit.prevent="handleCreateUser">
            <v-text-field
              v-model="newUser.name"
              label="Nome completo"
              required
              variant="outlined"
              class="mb-3"
            />
            <v-text-field
              v-model="newUser.email"
              label="E-mail"
              type="email"
              required
              variant="outlined"
              class="mb-3"
            />
            <v-text-field
              v-model="newUser.password"
              label="Senha"
              type="password"
              required
              variant="outlined"
              class="mb-3"
            />
            <v-alert
              v-if="createUserSuccess"
              type="success"
              class="mb-3"
              dense
            >
              {{ createUserSuccess }}
            </v-alert>
            <v-alert
              v-if="createUserError"
              type="error"
              class="mb-3"
              dense
            >
              {{ createUserError }}
            </v-alert>
            <v-btn
              type="submit"
              color="primary"
              :loading="isCreatingUser"
            >
              Criar usuário
            </v-btn>
          </v-form>
        </v-card>
      </v-col>
    </v-row>

    <v-alert v-if="errorMessage" type="error" class="mb-4" dense>
      {{ errorMessage }}
    </v-alert>

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
              <v-chip
                :color="user.is_approved ? 'success' : 'warning'"
                text-color="white"
                size="small"
              >
                {{ user.is_approved ? 'Aprovado' : 'Pendente' }}
              </v-chip>
            </td>
            <td class="text-center">
              <v-chip
                :color="user.is_staff || user.is_superuser ? 'primary' : 'grey'"
                text-color="white"
                size="small"
              >
                {{ user.is_staff || user.is_superuser ? 'Admin' : 'Usuário' }}
              </v-chip>
            </td>
            <td class="text-center">
              <v-btn
                v-if="!user.is_approved"
                color="success"
                size="small"
                @click="updateUserStatus(user.id, true)"
              >
                Aprovar
              </v-btn>
              <v-btn
                v-else
                color="error"
                size="small"
                @click="updateUserStatus(user.id, false)"
              >
                Revogar
              </v-btn>
              <v-btn
                class="ml-2"
                size="small"
                :color="user.is_staff || user.is_superuser ? 'secondary' : 'primary'"
                @click="toggleAdmin(user)"
              >
                {{ user.is_staff || user.is_superuser ? 'Remover admin' : 'Tornar admin' }}
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
import { useRouter } from 'vue-router'

const router = useRouter()
const users = ref([])
const errorMessage = ref('')
const newUser = reactive({
  name: '',
  email: '',
  password: '',
})
const isCreatingUser = ref(false)
const isExporting = ref(false)
const createUserSuccess = ref('')
const createUserError = ref('')

const fetchUsers = async () => {
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('/api/admin/users', {
      headers: { 'Authorization': `Bearer ${token}` }
    })
    if (!response.ok) {
      throw new Error('Erro ao buscar usuários ou permissão negada')
    }
    users.value = await response.json()
  } catch (error) {
    errorMessage.value = error.message
  }
}

const updateUserStatus = async (userId, isApproved) => {
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('/api/admin/approve-user', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      },
      body: JSON.stringify({ user_id: userId, is_approved: isApproved })
    })
    if (!response.ok) {
      throw new Error('Erro ao atualizar status do usuário')
    }
    await fetchUsers()
  } catch (error) {
    errorMessage.value = error.message
  }
}

const toggleAdmin = async (user) => {
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('/api/admin/set-admin', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        user_id: user.id,
        make_admin: !(user.is_staff || user.is_superuser),
      }),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(data.detail || 'Erro ao atualizar permissão')
    }

    await fetchUsers()
  } catch (error) {
    errorMessage.value = error.message
  }
}

const exportDefaulters = async () => {
  isExporting.value = true
  errorMessage.value = ''
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('/api/admin/export-defaulters', {
      method: 'GET',
      headers: {
        Authorization: `Bearer ${token}`,
      },
    })

    if (response.status === 204) {
      throw new Error('Nenhum inadimplente encontrado para exportar')
    }

    if (!response.ok) {
      const data = await response.json().catch(() => ({}))
      throw new Error(data.detail || 'Erro ao exportar inadimplentes')
    }

    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'inadimplentes_condominios.xlsx'
    document.body.appendChild(a)
    a.click()
    a.remove()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    isExporting.value = false
  }
}

const handleCreateUser = async () => {
  isCreatingUser.value = true
  createUserSuccess.value = ''
  createUserError.value = ''
  try {
    const token = localStorage.getItem('access_token')
    const response = await fetch('/api/admin/create-user', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`,
      },
      body: JSON.stringify({
        name: newUser.name,
        email: newUser.email,
        password: newUser.password,
      }),
    })

    const data = await response.json().catch(() => ({}))

    if (!response.ok) {
      throw new Error(data.detail || 'Erro ao criar usuário')
    }

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

const goToDashboard = () => {
  router.push('/dashboard')
}

const logout = () => {
  localStorage.removeItem('access_token')
  router.push('/')
}

onMounted(fetchUsers)
</script>