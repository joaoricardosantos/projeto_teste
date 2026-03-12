from ninja import Router, File
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


@message_router.post("/upload-defaulters", response={200: dict})
def upload_defaulters(request, file: UploadedFile = File(...)):
    """Upload de CSV com mensagem padrão."""
    if not file.name.endswith(".csv"):
        raise HttpError(400, "Invalid_file_format_expected_csv")
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
    """Upload de CSV usando template de mensagem específico."""
    if not file.name.endswith(".csv"):
        raise HttpError(400, "Invalid_file_format_expected_csv")
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
    Recebe o Excel do relatório de inadimplentes e envia WhatsApp
    para todos os números da coluna 'Telefones' da aba Resumo.

    Query param opcional:
      - template_id: UUID do template de mensagem
    """
    if not file.name.endswith(".xlsx"):
        raise HttpError(400, "Invalid_file_format_expected_xlsx")
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