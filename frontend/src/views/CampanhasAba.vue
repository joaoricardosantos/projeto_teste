<template>
  <div>

    <!-- Lista de campanhas -->
    <v-card elevation="4" class="mb-4">
      <v-card-title class="pa-4 pb-2 d-flex align-center">
        <v-icon class="mr-2" color="primary">mdi-bullhorn</v-icon>
        Campanhas de Disparo
        <v-spacer />
        <v-btn size="small" variant="text" prepend-icon="mdi-refresh" @click="carregarCampanhas">
          Atualizar
        </v-btn>
      </v-card-title>
      <v-card-text class="pa-0">
        <v-progress-linear v-if="loadingCampanhas" indeterminate color="primary" />
        <v-data-table
          :headers="headersCampanhas"
          :items="campanhas"
          :items-per-page="10"
          density="comfortable"
          class="elevation-0"
          no-data-text="Nenhuma campanha encontrada. Faça um disparo pela aba Relatórios."
        >
          <!-- Coluna nome: exibe o nome + botão de editar inline -->
          <template #item.nome="{ item }">
            <div class="d-flex align-center gap-2">
              <template v-if="editando.id === item.id">
                <v-text-field
                  v-model="editando.nome"
                  density="compact"
                  variant="outlined"
                  hide-details
                  autofocus
                  style="min-width: 220px; max-width: 340px;"
                  @keyup.enter="salvarNome(item)"
                  @keyup.esc="cancelarEdicao"
                />
                <v-btn
                  icon size="small" color="primary" variant="tonal"
                  :loading="editando.loading"
                  @click="salvarNome(item)"
                >
                  <v-icon size="16">mdi-check</v-icon>
                </v-btn>
                <v-btn icon size="small" variant="text" @click="cancelarEdicao">
                  <v-icon size="16">mdi-close</v-icon>
                </v-btn>
              </template>
              <template v-else>
                <span>{{ item.nome }}</span>
                <v-btn
                  icon size="x-small" variant="text"
                  class="ml-1 edit-nome-btn"
                  title="Renomear campanha"
                  @click="iniciarEdicao(item)"
                >
                  <v-icon size="14" color="grey">mdi-pencil-outline</v-icon>
                </v-btn>
              </template>
            </div>
          </template>

          <template #item.respondidos="{ item }">
            <v-chip size="x-small" color="success" variant="tonal">{{ item.respondidos }}</v-chip>
          </template>
          <template #item.aguardando="{ item }">
            <v-chip size="x-small" color="warning" variant="tonal">{{ item.aguardando }}</v-chip>
          </template>
          <template #item.acoes="{ item }">
            <div class="d-flex gap-1">
              <v-btn size="small" color="primary" variant="tonal" @click="abrirCampanha(item)">
                <v-icon size="16" class="mr-1">mdi-eye</v-icon>Detalhes
              </v-btn>
              <v-btn v-if="isAdmin" size="small" color="error" variant="tonal" @click="confirmarDeletar(item)">
                <v-icon size="16" class="mr-1">mdi-delete</v-icon>Apagar
              </v-btn>
            </div>
          </template>
        </v-data-table>
      </v-card-text>
    </v-card>

    <!-- ── Dialog: Detalhes da campanha ── -->
    <v-dialog v-model="dialogCampanha" max-width="1000" scrollable>
      <v-card v-if="campanhaAtiva">
        <v-card-title class="pa-4 d-flex align-center flex-wrap gap-2">
          <v-icon class="mr-2" color="primary">mdi-bullhorn</v-icon>
          {{ campanhaAtiva.nome }}
          <v-spacer />
          <v-chip size="small" color="success" variant="tonal">✅ {{ campanhaAtiva.respondidos }} responderam</v-chip>
          <v-chip size="small" color="warning" variant="tonal">⏳ {{ campanhaAtiva.aguardando }} aguardando</v-chip>
        </v-card-title>
        <v-divider />

        <v-card-text class="pa-0">
          <div class="pa-4 d-flex align-center gap-3 flex-wrap">
            <v-btn-toggle v-model="filtroStatus" mandatory density="compact" color="primary">
              <v-btn value="">Todos</v-btn>
              <v-btn value="enviado">Aguardando</v-btn>
              <v-btn value="respondido">Respondidos</v-btn>
            </v-btn-toggle>

            <v-text-field
              v-model="buscaMensagem"
              placeholder="Buscar..."
              variant="outlined"
              density="compact"
              hide-details
              clearable
              prepend-inner-icon="mdi-magnify"
              style="max-width: 220px"
            />

            <v-spacer />

            <v-btn
              v-if="selecionados.length > 0"
              color="success"
              prepend-icon="mdi-whatsapp"
              :loading="reenviando"
              @click="dialogReenviar = true"
            >
              Reenviar ({{ selecionados.length }})
            </v-btn>
          </div>

          <v-data-table
            v-model="selecionados"
            :headers="headersMensagens"
            :items="mensagensFiltradas"
            :items-per-page="15"
            density="comfortable"
            class="elevation-0"
            show-select
            item-value="id"
            no-data-text="Nenhuma mensagem encontrada"
            :loading="loadingMensagens"
          >
            <template #item.status="{ item }">
              <v-chip
                size="x-small"
                :color="item.status === 'respondido' ? 'success' : item.status === 'erro' ? 'error' : 'warning'"
                variant="tonal"
              >
                {{ item.status === 'respondido' ? '✅ Respondido' : item.status === 'erro' ? '❌ Erro' : '⏳ Aguardando' }}
              </v-chip>
            </template>
            <template #item.resposta="{ item }">
              <span class="text-caption text-medium-emphasis">{{ item.resposta || '—' }}</span>
            </template>
          </v-data-table>

          <div class="pa-4 pt-2 d-flex gap-2">
            <v-btn size="small" color="success" variant="tonal" prepend-icon="mdi-check-all" @click="selecionarTodosAguardando">
              Selecionar todos aguardando ({{ mensagensAguardando.length }})
            </v-btn>
            <v-btn size="small" variant="text" color="error" @click="selecionados = []">
              Limpar seleção
            </v-btn>
          </div>
        </v-card-text>

        <v-divider />
        <v-card-actions class="pa-4">
          <v-spacer />
          <v-btn variant="text" @click="dialogCampanha = false">Fechar</v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ── Dialog: Confirmar reenvio ── -->
    <v-dialog v-model="dialogReenviar" max-width="500">
      <v-card>
        <v-card-title class="pa-4">
          <v-icon class="mr-2" color="success">mdi-whatsapp</v-icon>
          Confirmar reenvio
        </v-card-title>
        <v-card-text class="pa-4 pt-0">
          Deseja reenviar a mensagem para <strong>{{ selecionados.length }}</strong> contato(s)?
          <v-select
            v-model="templateReenvio"
            :items="templates"
            item-title="name"
            item-value="id"
            label="Template (opcional — deixe vazio para usar a mensagem original)"
            variant="outlined"
            density="comfortable"
            clearable
            class="mt-4"
            hide-details
          />
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="dialogReenviar = false">Cancelar</v-btn>
          <v-btn color="success" :loading="reenviando" @click="reenviar">
            Reenviar agora
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- ── Dialog: Confirmar deletar ── -->
    <v-dialog v-model="dialogDeletar.open" max-width="420">
      <v-card>
        <v-card-title class="pa-4">
          <v-icon class="mr-2" color="error">mdi-delete</v-icon>
          Remover campanha
        </v-card-title>
        <v-card-text class="pa-4 pt-0">
          Tem certeza que deseja remover a campanha
          <strong>"{{ dialogDeletar.campanha?.nome }}"</strong>?<br/>
          <span class="text-caption text-error">Todas as mensagens serão apagadas permanentemente.</span>
        </v-card-text>
        <v-card-actions class="pa-4 pt-0">
          <v-spacer />
          <v-btn variant="text" @click="dialogDeletar.open = false">Cancelar</v-btn>
          <v-btn color="error" :loading="dialogDeletar.loading" @click="deletarCampanha">
            Remover
          </v-btn>
        </v-card-actions>
      </v-card>
    </v-dialog>

    <!-- Snackbar -->
    <v-snackbar v-model="snackbar.show" :color="snackbar.color" timeout="4000">
      {{ snackbar.text }}
    </v-snackbar>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'

const campanhas        = ref([])
const campanhaAtiva    = ref(null)
const mensagens        = ref([])
const selecionados     = ref([])
const filtroStatus     = ref('')
const buscaMensagem    = ref('')
const templates        = ref([])
const templateReenvio  = ref(null)
const loadingCampanhas = ref(false)
const loadingMensagens = ref(false)
const reenviando       = ref(false)
const dialogCampanha   = ref(false)
const dialogReenviar   = ref(false)
const snackbar         = ref({ show: false, text: '', color: 'success' })
const dialogDeletar    = ref({ open: false, campanha: null, loading: false })
const isAdmin          = localStorage.getItem('is_admin') === '1'

// ── Edição de nome inline ─────────────────────────────────────────────────────
const editando = ref({ id: null, nome: '', loading: false })

const iniciarEdicao = (campanha) => {
  editando.value = { id: campanha.id, nome: campanha.nome, loading: false }
}

const cancelarEdicao = () => {
  editando.value = { id: null, nome: '', loading: false }
}

const salvarNome = async (campanha) => {
  const nome = editando.value.nome.trim()
  if (!nome || nome === campanha.nome) { cancelarEdicao(); return }
  editando.value.loading = true
  try {
    const res = await fetch(`/api/campanhas/${campanha.id}/renomear`, {
      method:  'PATCH',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body:    JSON.stringify({ nome }),
    })
    const text = await res.text()
    let data = {}
    try { data = JSON.parse(text) } catch (_) {}
    if (!res.ok) throw new Error(data.detail || 'Erro ao renomear')
    // Atualiza localmente sem recarregar tudo
    const idx = campanhas.value.findIndex(c => c.id === campanha.id)
    if (idx !== -1) campanhas.value[idx] = { ...campanhas.value[idx], nome: data.nome }
    snackbar.value = { show: true, text: 'Nome atualizado!', color: 'success' }
    cancelarEdicao()
  } catch (e) {
    snackbar.value = { show: true, text: e.message, color: 'error' }
    editando.value.loading = false
  }
}

// ── Auth ──────────────────────────────────────────────────────────────────────
const authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

// ── Headers ───────────────────────────────────────────────────────────────────
const headersCampanhas = [
  { title: 'Campanha',      key: 'nome',           sortable: true             },
  { title: 'Data',          key: 'criada_em',       width: 120                 },
  { title: 'Enviados',      key: 'total_enviados',  width: 100                 },
  { title: '✅ Responderam', key: 'respondidos',     width: 130                 },
  { title: '⏳ Aguardando',  key: 'aguardando',      width: 130                 },
  { title: '',              key: 'acoes',           width: 170, sortable: false },
]

const headersMensagens = [
  { title: 'Condomínio', key: 'condominio', sortable: true  },
  { title: 'Unidade',    key: 'unidade',    width: 110      },
  { title: 'Nome',       key: 'nome',       sortable: false },
  { title: 'Telefone',   key: 'telefone',   width: 150      },
  { title: 'Status',     key: 'status',     width: 140      },
  { title: 'Resposta',   key: 'resposta',   sortable: false },
]

// ── Computed ──────────────────────────────────────────────────────────────────
const mensagensFiltradas = computed(() => {
  let lista = mensagens.value
  if (filtroStatus.value) lista = lista.filter(m => m.status === filtroStatus.value)
  const q = buscaMensagem.value.toLowerCase().trim()
  if (q) lista = lista.filter(m =>
    m.condominio.toLowerCase().includes(q) ||
    m.unidade.toLowerCase().includes(q) ||
    (m.nome || '').toLowerCase().includes(q) ||
    m.telefone.includes(q)
  )
  return lista
})

const mensagensAguardando = computed(() =>
  mensagens.value.filter(m => m.status === 'enviado')
)

// ── Funções ───────────────────────────────────────────────────────────────────
const carregarCampanhas = async () => {
  loadingCampanhas.value = true
  try {
    const res = await fetch('/api/campanhas/', { headers: authHeader() })
    if (res.ok) campanhas.value = await res.json()
  } catch (_) {}
  finally { loadingCampanhas.value = false }
}

const carregarTemplates = async () => {
  try {
    const res = await fetch('/api/templates', { headers: authHeader() })
    if (res.ok) templates.value = await res.json()
  } catch (_) {}
}

const abrirCampanha = async (campanha) => {
  campanhaAtiva.value = campanha
  selecionados.value  = []
  filtroStatus.value  = ''
  buscaMensagem.value = ''
  dialogCampanha.value = true
  await carregarMensagens(campanha.id)
}

const carregarMensagens = async (campanhaId) => {
  loadingMensagens.value = true
  try {
    const res = await fetch(`/api/campanhas/${campanhaId}/mensagens`, { headers: authHeader() })
    if (res.ok) mensagens.value = await res.json()
  } catch (_) {}
  finally { loadingMensagens.value = false }
}

const selecionarTodosAguardando = () => {
  selecionados.value = mensagensAguardando.value.map(m => m.id)
}

const reenviar = async () => {
  reenviando.value = true
  try {
    const res = await fetch(`/api/campanhas/${campanhaAtiva.value.id}/reenviar`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json', ...authHeader() },
      body:    JSON.stringify({
        ids:         selecionados.value,
        template_id: templateReenvio.value || null,
      }),
    })
    const text = await res.text()
    let data = {}
    try { data = JSON.parse(text) } catch (_) {
      data = { detail: `Resposta inválida do servidor (HTTP ${res.status})` }
    }
    if (!res.ok) throw new Error(data.detail || 'Erro ao reenviar')

    snackbar.value = {
      show:  true,
      text:  `Reenvio concluído! ✅ ${data.success} enviados, ❌ ${data.errors} erros`,
      color: data.errors > 0 ? 'warning' : 'success',
    }
    dialogReenviar.value  = false
    selecionados.value    = []
    templateReenvio.value = null
    await carregarMensagens(campanhaAtiva.value.id)
    await carregarCampanhas()
  } catch (e) {
    snackbar.value = { show: true, text: e.message, color: 'error' }
  } finally {
    reenviando.value = false
  }
}

watch(mensagens, (novas) => {
  if (campanhaAtiva.value) {
    campanhaAtiva.value = {
      ...campanhaAtiva.value,
      respondidos: novas.filter(m => m.status === 'respondido').length,
      aguardando:  novas.filter(m => m.status === 'enviado').length,
    }
  }
})

const confirmarDeletar = (campanha) => {
  dialogDeletar.value = { open: true, campanha, loading: false }
}

const deletarCampanha = async () => {
  dialogDeletar.value.loading = true
  try {
    const res = await fetch(`/api/campanhas/${dialogDeletar.value.campanha.id}`, {
      method:  'DELETE',
      headers: authHeader(),
    })
    if (!res.ok) throw new Error('Erro ao remover campanha')
    snackbar.value = { show: true, text: 'Campanha removida com sucesso!', color: 'success' }
    dialogDeletar.value.open = false
    await carregarCampanhas()
  } catch (e) {
    snackbar.value = { show: true, text: e.message, color: 'error' }
  } finally {
    dialogDeletar.value.loading = false
  }
}

onMounted(() => {
  carregarCampanhas()
  carregarTemplates()
})
</script>

<style scoped>
/* Botão de editar fica visível só no hover da linha */
.edit-nome-btn {
  opacity: 0;
  transition: opacity 0.15s;
}
tr:hover .edit-nome-btn {
  opacity: 1;
}
</style>