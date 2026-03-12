from typing import List, Optional
from ninja import Router, Schema
from ninja.errors import HttpError
from core.models import User, MessageTemplate
from core.auth import JWTAuth
from pydantic import UUID4, EmailStr
from django.http import HttpResponse
from core.superlogica import gerar_relatorio_inadimplentes
import requests

admin_router = Router(auth=JWTAuth())


# ─────────────────────────────────────────────
# Schemas – Usuários
# ─────────────────────────────────────────────

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


# ─────────────────────────────────────────────
# Schemas – Templates
# ─────────────────────────────────────────────

class TemplateIn(Schema):
    name: str
    body: str
    is_active: bool = False


class TemplateOut(Schema):
    id: UUID4
    name: str
    body: str
    is_active: bool


# ─────────────────────────────────────────────
# Endpoints – Usuários
# ─────────────────────────────────────────────

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
def export_defaulters(request):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")
    try:
        content, filename = gerar_relatorio_inadimplentes()
    except requests.RequestException:
        raise HttpError(502, "External_service_unavailable")
    if not content:
        raise HttpError(204, "No_defaulters_found")
    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ─────────────────────────────────────────────
# Endpoints – Templates de mensagem
# ─────────────────────────────────────────────

@admin_router.get("/templates", response=List[TemplateOut])
def list_templates(request):
    """Lista todos os templates cadastrados."""
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")
    return list(MessageTemplate.objects.all())


@admin_router.get("/templates/active", response=TemplateOut)
def get_active_template(request):
    """Retorna o template atualmente ativo."""
    try:
        return MessageTemplate.objects.get(is_active=True)
    except MessageTemplate.DoesNotExist:
        raise HttpError(404, "No_active_template")


@admin_router.post("/templates", response={201: TemplateOut})
def create_template(request, payload: TemplateIn):
    """Cria um novo template. Se is_active=True, desativa os demais."""
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    if payload.is_active:
        MessageTemplate.objects.filter(is_active=True).update(is_active=False)

    template = MessageTemplate.objects.create(
        name=payload.name,
        body=payload.body,
        is_active=payload.is_active,
    )
    return 201, template


@admin_router.put("/templates/{template_id}", response=TemplateOut)
def update_template(request, template_id: UUID4, payload: TemplateIn):
    """Atualiza um template existente."""
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    try:
        template = MessageTemplate.objects.get(id=template_id)
    except MessageTemplate.DoesNotExist:
        raise HttpError(404, "Template_not_found")

    if payload.is_active:
        MessageTemplate.objects.exclude(id=template_id).filter(is_active=True).update(
            is_active=False
        )

    template.name = payload.name
    template.body = payload.body
    template.is_active = payload.is_active
    template.save()
    return template


@admin_router.post("/templates/{template_id}/activate", response=TemplateOut)
def activate_template(request, template_id: UUID4):
    """Ativa um template e desativa todos os outros."""
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    try:
        template = MessageTemplate.objects.get(id=template_id)
    except MessageTemplate.DoesNotExist:
        raise HttpError(404, "Template_not_found")

    MessageTemplate.objects.exclude(id=template_id).update(is_active=False)
    template.is_active = True
    template.save()
    return template


@admin_router.delete("/templates/{template_id}", response={200: dict})
def delete_template(request, template_id: UUID4):
    """Remove um template."""
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    try:
        template = MessageTemplate.objects.get(id=template_id)
    except MessageTemplate.DoesNotExist:
        raise HttpError(404, "Template_not_found")

    template.delete()
    return 200, {"message": "Template_deleted"}