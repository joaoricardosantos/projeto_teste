"""
Endpoints para gerenciamento de campanhas e reenvio de mensagens.
"""
import logging
from typing import List, Optional
from ninja import Router, Schema
from ninja.errors import HttpError
from pydantic import UUID4
from core.auth import JWTAuth

logger = logging.getLogger(__name__)
campanha_router = Router(auth=JWTAuth())


def _fmt(dt):
    """Formata datetime para fuso America/Sao_Paulo."""
    if not dt:
        return None
    from django.utils import timezone as tz
    import zoneinfo
    sp = zoneinfo.ZoneInfo("America/Sao_Paulo")
    local = dt.astimezone(sp)
    return local.strftime("%d/%m/%Y %H:%M")


@campanha_router.get("/", response={200: list})
def listar_campanhas(request):
    """Lista todas as campanhas ordenadas por data."""
    from core.models import Campanha, MensagemEnviada
    campanhas = Campanha.objects.all()
    resultado = []
    for c in campanhas:
        respondidos = c.mensagens.filter(status="respondido").count()
        enviados    = c.mensagens.filter(status="enviado").count()
        erros       = c.mensagens.filter(status="erro").count()
        resultado.append({
            "id":              str(c.id),
            "nome":            c.nome,
            "criada_em":       _fmt(c.criada_em),
            "total_enviados":  c.total_enviados,
            "total_erros":     c.total_erros,
            "total_sem_numero":c.total_sem_numero,
            "respondidos":     respondidos,
            "aguardando":      enviados,
            "erros_envio":     erros,
        })
    return 200, resultado


@campanha_router.get("/{campanha_id}/mensagens", response={200: list})
def listar_mensagens(
    request,
    campanha_id: UUID4,
    status: Optional[str] = None,
):
    """Lista mensagens de uma campanha, filtrando por status se informado."""
    from core.models import Campanha, MensagemEnviada
    try:
        campanha = Campanha.objects.get(id=campanha_id)
    except Campanha.DoesNotExist:
        raise HttpError(404, "Campanha_not_found")

    qs = campanha.mensagens.all()
    if status:
        qs = qs.filter(status=status)

    return 200, [
        {
            "id":           str(m.id),
            "condominio":   m.condominio,
            "unidade":      m.unidade,
            "nome":         m.nome,
            "telefone":     m.telefone,
            "status":       m.status,
            "enviada_em":   _fmt(m.enviada_em),
            "respondida_em":_fmt(m.respondida_em),
            "resposta":     m.resposta,
        }
        for m in qs
    ]


@campanha_router.delete("/{campanha_id}", response={200: dict})
def deletar_campanha(request, campanha_id: UUID4):
    """Remove uma campanha e todas as mensagens associadas."""
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")
    from core.models import Campanha
    try:
        campanha = Campanha.objects.get(id=campanha_id)
        campanha.delete()
        return 200, {"message": "Campanha removida com sucesso"}
    except Campanha.DoesNotExist:
        raise HttpError(404, "Campanha_not_found")


class ReenviarIn(Schema):
    ids: List[str]
    template_id: Optional[str] = None


@campanha_router.post("/{campanha_id}/reenviar", response={200: dict})
def reenviar_mensagens(request, campanha_id: UUID4, payload: ReenviarIn):
    """
    Reenvia mensagens para IDs específicos.
    Body: { "ids": ["uuid1", "uuid2", ...], "template_id": "uuid" (opcional) }
    """
    from core.models import Campanha, MensagemEnviada, MessageTemplate
    from core.evolution_service import send_whatsapp_bulk
    from core.services import _render_template

    try:
        campanha = Campanha.objects.get(id=campanha_id)
    except Campanha.DoesNotExist:
        raise HttpError(404, "Campanha_not_found")

    ids = payload.ids
    template_id = payload.template_id

    if not ids:
        raise HttpError(400, "Nenhum_ID_informado")

    # Busca mensagens
    mensagens = MensagemEnviada.objects.filter(
        id__in=ids,
        campanha=campanha,
    )

    if not mensagens:
        raise HttpError(404, "Mensagens_not_found")

    # Template opcional
    template_body = None
    if template_id:
        try:
            t = MessageTemplate.objects.get(id=template_id)
            template_body = t.body
        except MessageTemplate.DoesNotExist:
            raise HttpError(404, "Template_not_found")

    contacts = []
    for m in mensagens:
        if template_body:
            msg = _render_template(
                template_body,
                condo_name=m.condominio,
                unidade=m.unidade,
                nome=m.nome,
            )
        else:
            msg = m.mensagem  # reenvia mensagem original

        contacts.append({"phone": m.telefone, "message": msg, "_id": str(m.id)})

    result = send_whatsapp_bulk(contacts)

    # Atualiza status das mensagens reenviadas
    from django.utils import timezone
    MensagemEnviada.objects.filter(id__in=ids).update(
        status=MensagemEnviada.STATUS_ENVIADO,
        enviada_em=timezone.now(),
        respondida_em=None,
        resposta="",
    )

    return 200, {
        "success":  result.get("success", 0),
        "errors":   result.get("errors", 0),
        "failures": result.get("failures", []),
    }