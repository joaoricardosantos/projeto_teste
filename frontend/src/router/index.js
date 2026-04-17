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
import JuridicoView from '../views/JuridicoView.vue'
import AgendaView from '../views/AgendaView.vue'
import SindicosView from '../views/SindicosView.vue'
import ExecucaoView from '../views/ExecucaoView.vue'
import PlanilhasView from '../views/PlanilhasView.vue'

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
    { path: '/juridico',     name: 'Juridico',     component: JuridicoView,     meta: { requiresAuth: true } },
    { path: '/agenda',       name: 'Agenda',       component: AgendaView,       meta: { requiresAuth: true } },
    { path: '/sindicos',     name: 'Sindicos',     component: SindicosView,     meta: { requiresAuth: true } },
    { path: '/execucao',     name: 'Execucao',     component: ExecucaoView,     meta: { requiresAuth: true } },
    { path: '/planilhas',    name: 'Planilhas',    component: PlanilhasView,    meta: { requiresAuth: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
    const isAuthenticated = !!localStorage.getItem('access_token')
    const isAdmin = localStorage.getItem('is_admin') === 'true'
    const isJuridico = localStorage.getItem('is_juridico') === 'true'
    const isFinanceiro = localStorage.getItem('is_financeiro') === 'true'

    const isUsuario = !isAdmin && !isJuridico && !isFinanceiro

    if (to.meta.requiresAuth && !isAuthenticated) return next('/')
    if (to.meta.requiresAdmin && !isAdmin) return next('/agenda')
    if (to.meta.requiresAdminOrJuridico && !isAdmin && !isJuridico) return next('/agenda')
    // Bloqueia usuário comum — apenas /agenda
    if (isUsuario && isAuthenticated && !['/agenda', '/planilhas'].includes(to.path)) return next('/agenda')
    // Bloqueia jurídico de acessar rotas não permitidas
    if (isJuridico && !isAdmin && !['/dashboard', '/relatorios', '/juridico', '/levantamento', '/agenda', '/execucao', '/planilhas'].includes(to.path)) return next('/dashboard')
    // Bloqueia financeiro de acessar rotas não permitidas
    if (isFinanceiro && !isAdmin && !['/dashboard', '/sheets', '/financeiro', '/agenda', '/planilhas'].includes(to.path)) return next('/dashboard')
    next()
})

export default router