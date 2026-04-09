import { ref } from 'vue'

// Cache compartilhado entre todas as views — persiste enquanto o app estiver aberto
const _cache       = ref([])      // lista já formatada: [{ id, label }]
const _loading     = ref(false)
const _carregado   = ref(false)
const _promise     = ref(null)    // evita chamadas paralelas simultâneas

const _authHeader = () => ({
  Authorization: `Bearer ${localStorage.getItem('access_token')}`,
})

export function useCondominios() {
  const carregar = async (forcar = false) => {
    if (_carregado.value && !forcar) return

    // Se já há uma requisição em andamento, aguarda ela terminar
    if (_promise.value) return _promise.value

    _loading.value = true
    _promise.value = fetch('/api/admin/condominios', { headers: _authHeader() })
      .then(res => res.ok ? res.json() : [])
      .then(lista => {
        _cache.value = lista
          .map(c => ({ id: c.id, nome: c.nome, label: `[${c.id}] ${c.nome}` }))
          .sort((a, b) => a.id - b.id)
        _carregado.value = true
      })
      .catch(() => {})
      .finally(() => {
        _loading.value = false
        _promise.value = null
      })

    return _promise.value
  }

  const invalidar = () => {
    _carregado.value = false
    _cache.value     = []
  }

  return {
    condominios:         _cache,
    loadingCondominios:  _loading,
    carregarCondominios: carregar,
    invalidarCondominios: invalidar,
  }
}
