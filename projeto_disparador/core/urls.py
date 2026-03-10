from django.urls import path
from ninja import NinjaAPI
from core.api import auth_router
from core.admin_api import admin_router
from core.message_api import message_router

api = NinjaAPI(title="Condominium Messaging API", version="1.0.0")

api.add_router("/auth", auth_router)
api.add_router("/admin", admin_router)
api.add_router("/messages", message_router)

urlpatterns = [
        path("api/", api.urls),
]