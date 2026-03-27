import { createRouter, createWebHistory } from 'vue-router'
import AuthView from '../views/AuthView.vue'
import DashboardView from '../views/DashboardView.vue'
import PainelView from '../views/PainelView.vue'
import AdminView from '../views/AdminView.vue'
import ReportsView from '../views/ReportsView.vue'
import TemplatesView from '../views/TemplatesView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'
import SheetsView from '../views/SheetsView.vue'  // ← NOVA INTEGRAÇÃO
import LevantamentoView from '../views/LevantamentoView.vue'
import FinanceiroView from '../views/FinanceiroView.vue'
import PjeView from '../views/PjeView.vue'

const routes = [
    { path: '/', name: 'Auth', component: AuthView },
    { path: '/reset-password', name: 'ResetPassword', component: ResetPasswordView },
    { path: '/dashboard', name: 'Dashboard', component: DashboardView, meta: { requiresAuth: true } },
    { path: '/painel', name: 'Painel', component: PainelView, meta: { requiresAuth: true } },
    { path: '/admin', name: 'Admin', component: AdminView, meta: { requiresAuth: true } },
    { path: '/relatorios', name: 'Reports', component: ReportsView, meta: { requiresAuth: true, requiresAdminOrJuridico: true } },
    { path: '/templates', name: 'Templates', component: TemplatesView, meta: { requiresAuth: true } },
    { path: '/sheets',       name: 'Sheets',       component: SheetsView,       meta: { requiresAuth: true } },  // ← NOVA INTEGRAÇÃO
    { path: '/levantamento', name: 'Levantamento', component: LevantamentoView, meta: { requiresAuth: true } },
    { path: '/financeiro',   name: 'Financeiro',   component: FinanceiroView,   meta: { requiresAuth: true } },
    { path: '/pje',          name: 'Pje',          component: PjeView,          meta: { requiresAuth: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
    const isAuthenticated = !!localStorage.getItem('access_token')
    const isAdmin = localStorage.getItem('is_admin') === 'true'
    const isJuridico = localStorage.getItem('is_juridico') === 'true'
    const isFinanceiro = localStorage.getItem('is_financeiro') === 'true'

    if (to.meta.requiresAuth && !isAuthenticated) return next('/')
    if (to.meta.requiresAdmin && !isAdmin) return next('/dashboard')
    if (to.meta.requiresAdminOrJuridico && !isAdmin && !isJuridico) return next('/dashboard')
    // Bloqueia jurídico de acessar rotas não permitidas
    if (isJuridico && !isAdmin && !['/dashboard', '/relatorios', '/pje'].includes(to.path)) return next('/dashboard')
    // Bloqueia financeiro de acessar rotas não permitidas
    if (isFinanceiro && !isAdmin && !['/dashboard', '/sheets', '/financeiro'].includes(to.path)) return next('/dashboard')
    next()
})

export default router