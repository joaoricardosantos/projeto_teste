import { createRouter, createWebHistory } from 'vue-router'
import AuthView from '../views/AuthView.vue'
import DashboardView from '../views/DashboardView.vue'
import PainelView from '../views/PainelView.vue'
import AdminView from '../views/AdminView.vue'
import ReportsView from '../views/ReportsView.vue'
import TemplatesView from '../views/TemplatesView.vue'
import ResetPasswordView from '../views/ResetPasswordView.vue'

const routes = [
    { path: '/', name: 'Auth', component: AuthView },
    { path: '/reset-password', name: 'ResetPassword', component: ResetPasswordView },
    { path: '/dashboard', name: 'Dashboard', component: DashboardView, meta: { requiresAuth: true } },
    { path: '/painel', name: 'Painel', component: PainelView, meta: { requiresAuth: true } },
    { path: '/admin', name: 'Admin', component: AdminView, meta: { requiresAuth: true } },
    { path: '/relatorios', name: 'Reports', component: ReportsView, meta: { requiresAuth: true, requiresAdmin: true } },
    { path: '/templates', name: 'Templates', component: TemplatesView, meta: { requiresAuth: true } },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
    const isAuthenticated = !!localStorage.getItem('access_token')
    const isAdmin = localStorage.getItem('is_admin') === 'true'

    if (to.meta.requiresAuth && !isAuthenticated) return next('/')
    if (to.meta.requiresAdmin && !isAdmin) return next('/dashboard')
    next()
})

export default router