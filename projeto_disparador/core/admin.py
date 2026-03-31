from typing import List, Optional
from ninja import Router, Schema
from ninja.errors import HttpError
from core.models import User
from core.auth import JWTAuth
from pydantic import UUID4, EmailStr
from django.http import HttpResponse
from core.superlogica import gerar_relatorio_inadimplentes
import requests

admin_router = Router(auth=JWTAuth())


class UserApprovalIn(Schema):
    user_id: UUID4
    is_approved: bool


class UserCreateIn(Schema):
    name: str
    email: EmailStr
    password: str


class UserOut(Schema):
    id: UUID4
    name: str
    email: str
    is_approved: bool
    is_active: bool
    is_staff: bool
    is_superuser: bool


class AdminRoleIn(Schema):
    user_id: UUID4
    make_admin: bool


@admin_router.get("/users", response=List[UserOut])
def list_users(request):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    return User.objects.all().order_by("-created_at")


@admin_router.post("/approve-user", response={200: dict})
def approve_user(request, payload: UserApprovalIn):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    try:
        user = User.objects.get(id=payload.user_id)
        user.is_approved = payload.is_approved
        user.save()
        return 200, {"message": "User_approval_status_updated"}
    except User.DoesNotExist:
        raise HttpError(404, "User_not_found")


@admin_router.post("/create-user", response={201: dict})
def create_user(request, payload: UserCreateIn):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    if User.objects.filter(email=payload.email).exists():
        raise HttpError(400, "Email_already_registered")

    User.objects.create_user(
        email=payload.email,
        password=payload.password,
        name=payload.name,
    )

    return 201, {"message": "User_created_successfully_pending_approval"}


@admin_router.post("/set-admin", response={200: dict})
def set_admin_role(request, payload: AdminRoleIn):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    try:
        user = User.objects.get(id=payload.user_id)
    except User.DoesNotExist:
        raise HttpError(404, "User_not_found")

    user.is_staff = payload.make_admin
    user.is_superuser = payload.make_admin
    user.save()

    return 200, {"message": "User_admin_role_updated"}


@admin_router.get("/export-defaulters")
def export_defaulters(
    request,
    id_condominio: Optional[int] = None,
    data_posicao: Optional[str] = None,
):
    """
    Gera relatório Excel de inadimplentes.

    Query params opcionais:
      - id_condominio: filtra por condomínio específico (int)
      - data_posicao:  data no formato DD/MM/YYYY (str)
    """
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    try:
        content, filename = gerar_relatorio_inadimplentes(
            id_condominio=id_condominio,
            data_posicao=data_posicao,
        )
    except requests.RequestException as e:
        raise HttpError(502, "External_service_unavailable")
    except Exception as e:
        raise HttpError(500, str(e))

    if not content:
        raise HttpError(204, "No_defaulters_found")

    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response