from typing import List
from ninja import Router, Schema
from ninja.errors import HttpError
from pydantic import UUID4
from core.auth import JWTAuth
from core.models import MessageTemplate

template_router = Router(auth=JWTAuth())


class TemplateIn(Schema):
    name: str
    body: str
    is_active: bool = False


class TemplateOut(Schema):
    id: UUID4
    name: str
    body: str
    is_active: bool


class ActivateTemplateIn(Schema):
    template_id: UUID4


def _check_admin(request):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")


@template_router.get("/", response=List[TemplateOut])
def list_templates(request):
    _check_admin(request)
    return MessageTemplate.objects.all().order_by("-created_at")


@template_router.post("/", response={201: dict})
def create_template(request, payload: TemplateIn):
    _check_admin(request)
    if payload.is_active:
        MessageTemplate.objects.filter(is_active=True).update(is_active=False)
    template = MessageTemplate.objects.create(
        name=payload.name,
        body=payload.body,
        is_active=payload.is_active,
    )
    return 201, {"message": "Template_created_successfully", "id": str(template.id)}


@template_router.post("/activate", response={200: dict})
def activate_template(request, payload: ActivateTemplateIn):
    _check_admin(request)
    try:
        template = MessageTemplate.objects.get(id=payload.template_id)
    except MessageTemplate.DoesNotExist:
        raise HttpError(404, "Template_not_found")

    MessageTemplate.objects.filter(is_active=True).update(is_active=False)
    template.is_active = True
    template.save()
    return 200, {"message": "Template_activated_successfully"}


@template_router.delete("/{template_id}", response={200: dict})
def delete_template(request, template_id: UUID4):
    _check_admin(request)
    try:
        template = MessageTemplate.objects.get(id=template_id)
    except MessageTemplate.DoesNotExist:
        raise HttpError(404, "Template_not_found")
    template.delete()
    return 200, {"message": "Template_deleted_successfully"}