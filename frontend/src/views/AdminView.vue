<template>
  <v-container>
    <v-row class="mb-4" align="center" justify="space-between">
      <v-col cols="12" sm="6">
        <h1 class="text-h5 font-weight-bold">Administração de Usuários</h1>
      </v-col>
      <v-col cols="12" sm="6" class="text-sm-right text-left">
        <v-btn variant="text" class="mr-2" @click="goToDashboard">
          Dashboard
        </v-btn>
        <v-btn icon @click="logout">
          <v-icon>mdi-logout</v-icon>
        </v-btn>
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
            </td>
          </tr>
        </tbody>
      </v-table>
    </v-card>
  </v-container>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const users = ref([])
const errorMessage = ref('')

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

const goToDashboard = () => {
  router.push('/dashboard')
}

const logout = () => {
  localStorage.removeItem('access_token')
  router.push('/')
}

onMounted(fetchUsers)
</script>