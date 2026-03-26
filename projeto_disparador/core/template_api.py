from typing import List
from ninja import Router, Schema
from ninja.errors import HttpError
from pydantic import UUID4
from typing import Union
from core.models import MessageTemplate
from core.auth import JWTAuth

template_router = Router(auth=JWTAuth())


# ── Schemas ──────────────────────────────────────────────────────────────────

class TemplateIn(Schema):
    name: str
    body: str


class TemplateOut(Schema):
    id: str
    name: str
    body: str
    created_at: str
    updated_at: str


def serialize_template(obj: MessageTemplate) -> dict:
    return {
        "id": str(obj.id),
        "name": obj.name,
        "body": obj.body,
        "created_at": obj.created_at.strftime("%d/%m/%Y %H:%M"),
        "updated_at": obj.updated_at.strftime("%d/%m/%Y %H:%M"),
    }


# ── Endpoints ─────────────────────────────────────────────────────────────────

@template_router.get("", response=List[TemplateOut])
def list_templates(request):
    """Lista todos os templates disponíveis."""
    templates = MessageTemplate.objects.all()
    return [serialize_template(t) for t in templates]


@template_router.post("", response={201: TemplateOut})
def create_template(request, payload: TemplateIn):
    """Cria um novo template. Restrito a administradores."""
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    if not payload.name.strip():
        raise HttpError(400, "Template_name_cannot_be_empty")

    if not payload.body.strip():
        raise HttpError(400, "Template_body_cannot_be_empty")

    if MessageTemplate.objects.filter(name=payload.name).exists():
        raise HttpError(400, "Template_name_already_exists")

    template = MessageTemplate.objects.create(
        name=payload.name.strip(),
        body=payload.body.strip(),
    )
    return 201, serialize_template(template)


@template_router.get("/{template_id}", response=TemplateOut)
def get_template(request, template_id: str):
    """Retorna um template pelo ID."""
    try:
        template = MessageTemplate.objects.get(id=template_id)
    except MessageTemplate.DoesNotExist:
        raise HttpError(404, "Template_not_found")
    return serialize_template(template)


@template_router.put("/{template_id}", response=TemplateOut)
def update_template(request, template_id: str, payload: TemplateIn):
    """Atualiza um template existente. Restrito a administradores."""
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    try:
        template = MessageTemplate.objects.get(id=template_id)
    except MessageTemplate.DoesNotExist:
        raise HttpError(404, "Template_not_found")

    if not payload.name.strip():
        raise HttpError(400, "Template_name_cannot_be_empty")

    if not payload.body.strip():
        raise HttpError(400, "Template_body_cannot_be_empty")

    # Verifica duplicidade de nome (excluindo o próprio registro)
    if (
        MessageTemplate.objects.filter(name=payload.name)
        .exclude(id=template_id)
        .exists()
    ):
        raise HttpError(400, "Template_name_already_exists")

    template.name = payload.name.strip()
    template.body = payload.body.strip()
    template.save()
    return serialize_template(template)


@template_router.delete("/{template_id}", response={200: dict})
def delete_template(request, template_id: str):
    """Exclui um template. Restrito a administradores."""
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    try:
        template = MessageTemplate.objects.get(id=template_id)
    except MessageTemplate.DoesNotExist:
        raise HttpError(404, "Template_not_found")

    template.delete()
    return 200, {"message": "Template_deleted_successfully"}