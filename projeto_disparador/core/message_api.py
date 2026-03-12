from ninja import Router, File
from ninja.files import UploadedFile
from ninja.errors import HttpError
from core.auth import JWTAuth
from core.services import process_defaulters_spreadsheet

message_router = Router(auth=JWTAuth())


@message_router.post("/upload-defaulters", response={200: dict})
def upload_defaulters(request, file: UploadedFile = File(...)):
    filename = file.name or ""

    if not (filename.endswith(".csv") or filename.endswith(".xlsx")):
        raise HttpError(400, "Invalid_file_format_expected_csv_or_xlsx")

    try:
        result = process_defaulters_spreadsheet(file, filename)
        return 200, {"message": "Processing_completed", "details": result}
    except ValueError as exc:
        raise HttpError(400, str(exc))
    except UnicodeDecodeError:
        raise HttpError(400, "Invalid_file_encoding")
    except Exception:
        raise HttpError(500, "Internal_processing_error")