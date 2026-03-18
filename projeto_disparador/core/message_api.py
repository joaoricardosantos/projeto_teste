from ninja import Router, File, Schema
from ninja.files import UploadedFile
from ninja.errors import HttpError
from typing import Optional
from pydantic import UUID4
from core.auth import JWTAuth
from core.services import (
    process_defaulters_spreadsheet,
    process_defaulters_with_template,
    process_excel_report_dispatch,
)

message_router = Router(auth=JWTAuth())

ALLOWED_EXTENSIONS = (".csv", ".xlsx")


def _check_extension(filename: str):
    if not any(filename.lower().endswith(ext) for ext in ALLOWED_EXTENSIONS):
        raise HttpError(400, "Invalid_file_format_expected_csv_or_xlsx")


@message_router.post("/upload-defaulters", response={200: dict})
def upload_defaulters(request, file: UploadedFile = File(...)):
    """Upload de CSV ou XLSX com mensagem padrão."""
    _check_extension(file.name)
    try:
        result = process_defaulters_spreadsheet(file)
        return 200, {"message": "Processing_completed", "details": result}
    except UnicodeDecodeError:
        raise HttpError(400, "Invalid_file_encoding")
    except Exception as e:
        raise HttpError(500, str(e))


@message_router.post("/upload-defaulters-template", response={200: dict})
def upload_defaulters_with_template(
    request,
    template_id: UUID4,
    file: UploadedFile = File(...),
):
    """Upload de CSV ou XLSX usando template de mensagem específico."""
    _check_extension(file.name)
    try:
        result = process_defaulters_with_template(file, str(template_id))
        return 200, {"message": "Processing_completed", "details": result}
    except ValueError as e:
        raise HttpError(404, str(e))
    except UnicodeDecodeError:
        raise HttpError(400, "Invalid_file_encoding")
    except Exception as e:
        raise HttpError(500, str(e))


@message_router.post("/dispatch-excel", response={200: dict})
def dispatch_excel(
    request,
    file: UploadedFile = File(...),
    template_id: Optional[UUID4] = None,
):
    """
    Recebe CSV ou XLSX do relatório de inadimplentes e envia WhatsApp
    para todos os números da coluna 'Telefones'.
    Colunas esperadas: Condomínio | Unidade | Telefones | Total

    Query param opcional:
      - template_id: UUID do template de mensagem
    """
    _check_extension(file.name)
    try:
        result = process_excel_report_dispatch(
            file,
            template_id=str(template_id) if template_id else None,
        )
        return 200, {"message": "Dispatch_completed", "details": result}
    except ValueError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        raise HttpError(500, str(e))

@message_router.get("/unidades-inadimplentes", response={200: list})
def get_unidades_inadimplentes(request, id_condominio: int):
    """
    Retorna lista de unidades inadimplentes de um condomínio
    sem enviar mensagens — usado para seleção na UI.
    """
    try:
        from core.condominio_service import get_unidades_inadimplentes
        unidades = get_unidades_inadimplentes(id_condominio)
        return 200, unidades
    except ValueError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        raise HttpError(500, str(e))


@message_router.post("/send-selected", response={200: dict})
def send_selected(
    request,
    id_condominio: int,
    template_id: Optional[int] = None,
    unidades_ids: str = "",
):
    """
    Envia mensagens para unidades selecionadas.
    unidades_ids: IDs separados por vírgula
    """
    try:
        from core.condominio_service import send_messages_by_condominio
        ids = [u.strip() for u in unidades_ids.split(",") if u.strip()] if unidades_ids else None
        result = send_messages_by_condominio(
            id_condominio=id_condominio,
            template_id=str(template_id) if template_id else None,
            unidades_ids=ids,
        )
        return 200, {"message": "Dispatch_completed", "details": result}
    except ValueError as e:
        raise HttpError(400, str(e))
    except Exception as e:
        raise HttpError(500, str(e))


class RelatorioEnvioIn(Schema):
    condominio_nome: str
    template_nome: str = ""
    enviados: list
    falhas: list
    sem_numero: list


from django.http import HttpResponse as DjangoHttpResponse

@message_router.post("/relatorio-envio-pdf")
def relatorio_envio_pdf(request, payload: RelatorioEnvioIn):
    """Gera PDF do relatório de envio de mensagens."""
    try:
        from core.relatorio_envio import gerar_pdf_relatorio_envio
        content = gerar_pdf_relatorio_envio(
            condominio_nome=payload.condominio_nome,
            template_nome=payload.template_nome,
            enviados=payload.enviados,
            falhas=payload.falhas,
            sem_numero=payload.sem_numero,
        )
        from datetime import datetime
        filename = f"relatorio_envio_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        response = DjangoHttpResponse(content, content_type="application/pdf")
        response["Content-Disposition"] = f'attachment; filename="{filename}"'
        return response
    except Exception as e:
        raise HttpError(500, str(e))