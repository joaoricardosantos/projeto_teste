from ninja import Router, File, Schema
from ninja.files import UploadedFile
from ninja.errors import HttpError
from typing import Optional
from pydantic import UUID4
from core.auth import JWTAuth
from core.services import process_defaulters_spreadsheet, process_defaulters_with_template

message_router = Router(auth=JWTAuth())


class SendWithTemplateIn(Schema):
    template_id: Optional[UUID4] = None


@message_router.post("/upload-defaulters", response={200: dict})
def upload_defaulters(request, file: UploadedFile = File(...)):
    """Upload de planilha CSV sem template (mensagem padrão)."""
    if not file.name.endswith('.csv'):
        raise HttpError(400, "Invalid_file_format_expected_csv")

    try:
        result = process_defaulters_spreadsheet(file)
        return 200, {"message": "Processing_completed", "details": result}
    except UnicodeDecodeError:
        raise HttpError(400, "Invalid_file_encoding")
    except Exception:
        raise HttpError(500, "Internal_processing_error")


@message_router.post("/upload-defaulters-template", response={200: dict})
def upload_defaulters_with_template(
    request,
    template_id: UUID4,
    file: UploadedFile = File(...),
):
    """
    Upload de planilha CSV usando um template de mensagem específico.
    O template suporta as variáveis: {{nome}}, {{condominio}}, {{valor}}.
    """
    if not file.name.endswith('.csv'):
        raise HttpError(400, "Invalid_file_format_expected_csv")

    try:
        result = process_defaulters_with_template(file, str(template_id))
        return 200, {"message": "Processing_completed", "details": result}
    except ValueError as e:
        raise HttpError(404, str(e))
    except UnicodeDecodeError:
        raise HttpError(400, "Invalid_file_encoding")
    except Exception:
        raise HttpError(500, "Internal_processing_error")