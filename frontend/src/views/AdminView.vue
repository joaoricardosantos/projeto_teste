<template>
  <v-app>
    <v-app-bar color="primary" dark>
      <v-toolbar-title>Administração de Usuários</v-toolbar-title>
      <v-spacer></v-spacer>
      <v-btn variant="text" @click="goToDashboard">Dashboard</v-btn>
      <v-btn icon @click="logout">
        <v-icon>mdi-logout</v-icon>
      </v-btn>
    </v-app-bar>

    <v-main>
      <v-container>
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
    </v-main>
  </v-app>
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