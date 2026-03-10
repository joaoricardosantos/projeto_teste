from ninja import Router, File
from ninja.files import UploadedFile
from ninja.errors import HttpError
from core.auth import JWTAuth
from core.services import process_defaulters_spreadsheet

message_router = Router(auth=JWTAuth())

@message_router.post("/upload-defaulters", response={200: dict})
def upload_defaulters(request, file: UploadedFile = File(...)):
    if not file.name.endswith('.csv'):
        raise HttpError(400, "Invalid_file_format_expected_csv")
        
    try:
        result = process_defaulters_spreadsheet(file)
        return 200, {"message": "Processing_completed", "details": result}
    except UnicodeDecodeError:
        raise HttpError(400, "Invalid_file_encoding")
    except Exception:
        raise HttpError(500, "Internal_processing_error")