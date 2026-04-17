from django.urls import path
from ninja import NinjaAPI
from core.api import auth_router
from core.admin_api import admin_router
from core.message_api import message_router
from core.template_api import template_router
from core.webhook_api import webhook_router
from core.campanha_api import campanha_router
from core.password_reset_api import password_router
from core.sheets_api import sheets_router
from core.financeiro_api import financeiro_router
from core.agenda_api import agenda_router
from core.juridico_api import juridico_router
from core.sindico_api import sindico_router
from core.execucao_api import execucao_router
from core.planilha_funcionario_api import planilha_router

api = NinjaAPI(title="Condominium Messaging API", version="1.0.0")

api.add_router("/auth",      auth_router)
api.add_router("/auth",      password_router)
api.add_router("/admin",     admin_router)
api.add_router("/messages",  message_router)
api.add_router("/templates", template_router)
api.add_router("/webhook",   webhook_router)
api.add_router("/campanhas", campanha_router)
api.add_router("/sheets",     sheets_router)
api.add_router("/financeiro", financeiro_router)
api.add_router("/juridico",   juridico_router)
api.add_router("/agenda",     agenda_router)
api.add_router("/sindicos",   sindico_router)
api.add_router("/execucao",   execucao_router)
api.add_router("/planilhas",  planilha_router)

urlpatterns = [
    path("api/", api.urls),
]