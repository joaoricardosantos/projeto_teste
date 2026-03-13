import threading
import uuid
import os
import tempfile
from datetime import datetime
from typing import List, Optional

import requests
from django.http import HttpResponse, FileResponse
from ninja import Router, Schema
from ninja.errors import HttpError
from pydantic import UUID4, EmailStr

from core.auth import JWTAuth
from core.models import User
from core.superlogica import gerar_relatorio_inadimplentes

admin_router = Router(auth=JWTAuth())

# ── Job store em memória ──────────────────────────────────────────────────────
# { job_id: { "status": "pending"|"running"|"done"|"error", "file": path, "filename": str, "error": str } }
_JOBS: dict = {}
_JOBS_LOCK = threading.Lock()


def _run_job(job_id: str, id_condominio, data_posicao):
    with _JOBS_LOCK:
        _JOBS[job_id]["status"] = "running"
    try:
        content, filename = gerar_relatorio_inadimplentes(
            id_condominio=id_condominio,
            data_posicao=data_posicao,
        )
        if not content:
            with _JOBS_LOCK:
                _JOBS[job_id]["status"] = "empty"
            return

        # Salva em arquivo temporário
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        tmp.write(content)
        tmp.close()

        with _JOBS_LOCK:
            _JOBS[job_id]["status"] = "done"
            _JOBS[job_id]["file"] = tmp.name
            _JOBS[job_id]["filename"] = filename

    except Exception as e:
        with _JOBS_LOCK:
            _JOBS[job_id]["status"] = "error"
            _JOBS[job_id]["error"] = str(e)


# ── Schemas ───────────────────────────────────────────────────────────────────
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

class UserDeleteIn(Schema):
    user_id: UUID4


# ── Endpoints de usuários ─────────────────────────────────────────────────────
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


@admin_router.delete("/delete-user", response={200: dict})
def delete_user(request, payload: UserDeleteIn):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")
    if str(request.auth.id) == str(payload.user_id):
        raise HttpError(400, "Cannot_delete_own_account")
    try:
        user = User.objects.get(id=payload.user_id)
        user.delete()
        return 200, {"message": "User_deleted_successfully"}
    except User.DoesNotExist:
        raise HttpError(404, "User_not_found")


# ── Endpoints de relatório (background job) ───────────────────────────────────
@admin_router.post("/export-defaulters/start", response={202: dict})
def start_export(
    request,
    id_condominio: Optional[int] = None,
    data_posicao: Optional[str] = None,
):
    """
    Inicia a geração do relatório em background.
    Retorna um job_id para consultar o status.
    """
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    job_id = str(uuid.uuid4())
    with _JOBS_LOCK:
        _JOBS[job_id] = {"status": "pending", "file": None, "filename": None, "error": None}

    t = threading.Thread(
        target=_run_job,
        args=(job_id, id_condominio, data_posicao),
        daemon=True,
    )
    t.start()

    return 202, {"job_id": job_id}


@admin_router.get("/export-defaulters/status/{job_id}", response={200: dict})
def job_status(request, job_id: str):
    """
    Consulta o status de um job de exportação.
    Status possíveis: pending, running, done, empty, error
    """
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    with _JOBS_LOCK:
        job = _JOBS.get(job_id)

    if not job:
        raise HttpError(404, "Job_not_found")

    return 200, {
        "status": job["status"],
        "filename": job.get("filename"),
        "error": job.get("error"),
    }


@admin_router.get("/export-defaulters/download/{job_id}")
def download_export(request, job_id: str):
    """
    Faz o download do arquivo gerado pelo job.
    Só disponível quando status == done.
    """
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    with _JOBS_LOCK:
        job = _JOBS.get(job_id)

    if not job:
        raise HttpError(404, "Job_not_found")
    if job["status"] != "done":
        raise HttpError(400, "Job_not_ready")

    filepath = job["file"]
    filename = job["filename"]

    if not filepath or not os.path.exists(filepath):
        raise HttpError(404, "File_not_found")

    with open(filepath, "rb") as f:
        content = f.read()

    # Remove arquivo temporário após download
    try:
        os.unlink(filepath)
    except Exception:
        pass
    with _JOBS_LOCK:
        _JOBS.pop(job_id, None)

    response = HttpResponse(
        content,
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ── Endpoint legado (compatibilidade - só para condomínio específico) ─────────
@admin_router.get("/export-defaulters")
def export_defaulters(
    request,
    id_condominio: Optional[int] = None,
    data_posicao: Optional[str] = None,
):
    """
    Exportação síncrona — use apenas para um condomínio específico.
    Para todos os condomínios, use /export-defaulters/start.
    """
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    if not id_condominio:
        raise HttpError(400, "Use_async_endpoint_for_all_condominios")

    try:
        content, filename = gerar_relatorio_inadimplentes(
            id_condominio=id_condominio,
            data_posicao=data_posicao,
        )
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