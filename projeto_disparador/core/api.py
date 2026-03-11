from ninja import Router
from django.contrib.auth import authenticate
from core.models import User
from core.schemas import RegisterIn, LoginIn, TokenOut
from core.security import create_access_token
from ninja.errors import HttpError

auth_router = Router()


@auth_router.post("/register", response={403: dict})
def register(request, payload: RegisterIn):
    """
    Registro público desabilitado: novos usuários devem ser criados via painel admin.
    """
    raise HttpError(403, "Registration_disabled_use_admin_panel")


@auth_router.post("/login", response=TokenOut)
def login(request, payload: LoginIn):
    user = authenticate(request, email=payload.email, password=payload.password)

    if not user:
        raise HttpError(401, "Invalid_credentials")

    if not user.is_approved:
        raise HttpError(403, "Account_pending_approval")

    if not user.is_active:
        raise HttpError(403, "Account_disabled")

    token = create_access_token(user.id)
    return {"access_token": token, "token_type": "bearer"}