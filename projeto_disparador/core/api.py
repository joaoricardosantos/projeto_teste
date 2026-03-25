from ninja import Router
from django.contrib.auth import authenticate
from core.models import User
from core.schemas import RegisterIn, LoginIn, TokenOut
from core.security import create_access_token
from ninja.errors import HttpError

auth_router = Router()


@auth_router.post("/register", response={403: dict})
def register(request, payload: RegisterIn):
    raise HttpError(403, "Registration_disabled_use_admin_panel")


@auth_router.post("/login", response={200: dict, 401: dict, 403: dict})
def login(request, payload: LoginIn):
    try:
        user = authenticate(request, email=payload.email, password=payload.password)
        if not user:
            raise HttpError(401, "Invalid_credentials")
        if not user.is_approved:
            raise HttpError(403, "Account_pending_approval")
        if not user.is_active:
            raise HttpError(403, "Account_disabled")
        token = create_access_token(user.id)
        return 200, {
            "access_token": token,
            "token_type":   "bearer",
            "is_admin":      user.is_staff or user.is_superuser,
            "is_juridico":   user.is_juridico,
            "is_financeiro": user.is_financeiro,
            "name":         user.name,
        }
    except HttpError:
        raise
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Login erro inesperado: {e}", exc_info=True)
        raise HttpError(500, "Internal_server_error")
