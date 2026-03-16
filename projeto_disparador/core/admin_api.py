import threading
import uuid
import os
import tempfile
from datetime import datetime, timedelta
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
_JOBS: dict = {}
_JOBS_LOCK = threading.Lock()

# ── Cache do dashboard ────────────────────────────────────────────────────────
_DASHBOARD_CACHE: dict = {}
_CACHE_LOCK = threading.Lock()
_CACHE_TTL_MINUTES = 30


def _run_job(job_id: str, id_condominio, data_posicao, data_inicio=None, ordenar_desc=False):
    with _JOBS_LOCK:
        _JOBS[job_id]["status"] = "running"
    try:
        try:
            content, filename = gerar_relatorio_inadimplentes(
                id_condominio=id_condominio,
                data_posicao=data_posicao,
                data_inicio=data_inicio,
                ordenar_desc=ordenar_desc,
            )
        except TypeError:
            content, filename = gerar_relatorio_inadimplentes(
                id_condominio=id_condominio,
                data_posicao=data_posicao,
            )
        if not content:
            with _JOBS_LOCK:
                _JOBS[job_id]["status"] = "empty"
            return

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx")
        tmp.write(content)
        tmp.close()

        with _JOBS_LOCK:
            _JOBS[job_id]["status"]   = "done"
            _JOBS[job_id]["file"]     = tmp.name
            _JOBS[job_id]["filename"] = filename

    except Exception as e:
        with _JOBS_LOCK:
            _JOBS[job_id]["status"] = "error"
            _JOBS[job_id]["error"]  = str(e)


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
    ultimos_5_anos: bool = False,
    ordenar_desc: bool = False,
):
    """
    Inicia a geração do relatório em background.
    ultimos_5_anos=true filtra vencimentos dos últimos 5 anos.
    ordenar_desc=true ordena por Total decrescente.
    """
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    data_inicio = None
    if ultimos_5_anos:
        data_inicio = (datetime.now() - timedelta(days=5 * 365)).strftime("%d/%m/%Y")

    job_id = str(uuid.uuid4())
    with _JOBS_LOCK:
        _JOBS[job_id] = {"status": "pending", "file": None, "filename": None, "error": None}

    t = threading.Thread(
        target=_run_job,
        args=(job_id, id_condominio, data_posicao, data_inicio, ordenar_desc),
        daemon=True,
    )
    t.start()

    return 202, {"job_id": job_id}


@admin_router.get("/export-defaulters/status/{job_id}", response={200: dict})
def job_status(request, job_id: str):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
    if not job:
        raise HttpError(404, "Job_not_found")
    return 200, {
        "status":   job["status"],
        "filename": job.get("filename"),
        "error":    job.get("error"),
    }


@admin_router.get("/export-defaulters/download/{job_id}")
def download_export(request, job_id: str):
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


# ── Endpoint legado (compatibilidade) ─────────────────────────────────────────
@admin_router.get("/export-defaulters")
def export_defaulters(
    request,
    id_condominio: Optional[int] = None,
    data_posicao: Optional[str] = None,
):
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


# ── Limpar cache do dashboard ─────────────────────────────────────────────────
@admin_router.post("/dashboard/clear-cache", response={200: dict})
def clear_dashboard_cache(request):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")
    with _CACHE_LOCK:
        _DASHBOARD_CACHE.clear()
    return 200, {"message": "Cache limpo com sucesso"}


# ── Endpoints de PDF (background job) ────────────────────────────────────────
@admin_router.post("/export-pdf/start", response={202: dict})
def start_export_pdf(
    request,
    id_condominio: Optional[int] = None,
    data_posicao: Optional[str] = None,
    ultimos_5_anos: bool = False,
    ordenar_desc: bool = False,
):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    from core.superlogica import gerar_pdf_inadimplentes

    data_inicio = None
    if ultimos_5_anos:
        data_inicio = (datetime.now() - timedelta(days=5 * 365)).strftime("%d/%m/%Y")

    job_id = str(uuid.uuid4())
    with _JOBS_LOCK:
        _JOBS[job_id] = {"status": "pending", "file": None, "filename": None, "error": None}

    def _run():
        with _JOBS_LOCK:
            _JOBS[job_id]["status"] = "running"
        try:
            try:
                content, filename = gerar_pdf_inadimplentes(
                    id_condominio=id_condominio,
                    data_posicao=data_posicao,
                    data_inicio=data_inicio,
                    ordenar_desc=ordenar_desc,
                )
            except TypeError:
                content, filename = gerar_pdf_inadimplentes(
                    id_condominio=id_condominio,
                    data_posicao=data_posicao,
                )
            if not content:
                with _JOBS_LOCK:
                    _JOBS[job_id]["status"] = "empty"
                return
            tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            tmp.write(content)
            tmp.close()
            with _JOBS_LOCK:
                _JOBS[job_id]["status"]   = "done"
                _JOBS[job_id]["file"]     = tmp.name
                _JOBS[job_id]["filename"] = filename
        except Exception as e:
            with _JOBS_LOCK:
                _JOBS[job_id]["status"] = "error"
                _JOBS[job_id]["error"]  = str(e)

    threading.Thread(target=_run, daemon=True).start()
    return 202, {"job_id": job_id}


@admin_router.get("/export-pdf/status/{job_id}", response={200: dict})
def pdf_job_status(request, job_id: str):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")
    with _JOBS_LOCK:
        job = _JOBS.get(job_id)
    if not job:
        raise HttpError(404, "Job_not_found")
    return 200, {"status": job["status"], "filename": job.get("filename"), "error": job.get("error")}


@admin_router.get("/export-pdf/download/{job_id}")
def download_pdf(request, job_id: str):
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
    try:
        os.unlink(filepath)
    except Exception:
        pass
    with _JOBS_LOCK:
        _JOBS.pop(job_id, None)
    response = HttpResponse(content, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


# ── Endpoint de Dashboard ─────────────────────────────────────────────────────
@admin_router.get("/dashboard", response={200: dict})
def get_dashboard(
    request,
    id_condominio: Optional[int] = None,
    data_posicao: Optional[str] = None,
    ultimos_5_anos: bool = False,
):
    """
    Retorna dados resumidos para o dashboard.
    ultimos_5_anos=true filtra vencimentos dos últimos 5 anos.
    """
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    from core.superlogica import (
        verificar_condominio,
        buscar_unidades,
        buscar_inadimplentes_condominio,
        _MAX_WORKERS_CONDOMINIOS,
    )
    from django.conf import settings
    from decimal import Decimal
    from concurrent.futures import ThreadPoolExecutor, as_completed

    if not data_posicao:
        data_posicao_fmt   = datetime.today().strftime("%m/%d/%Y")
        data_posicao_label = datetime.today().strftime("%d/%m/%Y")
    else:
        partes = data_posicao.split("/")
        if len(partes) == 3:
            data_posicao_fmt = f"{partes[1]}/{partes[0]}/{partes[2]}"
        else:
            data_posicao_fmt = data_posicao
        data_posicao_label = data_posicao

    # Calcula data_inicio se filtro de 5 anos estiver ativo
    data_inicio = None
    if ultimos_5_anos:
        data_inicio = (datetime.now() - timedelta(days=5 * 365)).strftime("%d/%m/%Y")

    # Cache key inclui o flag de 5 anos
    cache_key = f"{id_condominio or 'todos'}_{data_posicao_label}_{'5a' if ultimos_5_anos else 'all'}"

    with _CACHE_LOCK:
        cached = _DASHBOARD_CACHE.get(cache_key)
        if cached and cached["expires_at"] > datetime.now():
            return 200, cached["data"]

    ids_range    = [id_condominio] if id_condominio else range(1, getattr(settings, "SUPERLOGICA_MAX_ID", 100) + 1)
    total_geral  = Decimal("0")
    condo_valores = {}
    sem_numero   = []
    total_unidades = 0

    def _processar(condo_id):
        acesso, nome = verificar_condominio(condo_id)
        if not acesso:
            return None
        mapa = buscar_unidades(condo_id)
        if not mapa:
            return None
        try:
            resumo, _ = buscar_inadimplentes_condominio(condo_id, data_posicao_fmt, mapa, data_inicio)
        except TypeError:
            # Retrocompatibilidade: superlogica.py ainda sem patch data_inicio
            resumo, _ = buscar_inadimplentes_condominio(condo_id, data_posicao_fmt, mapa)
        if not resumo:
            return None

        condo_total   = Decimal("0")
        sem_num_local = []
        for uid, vals in resumo.items():
            try:
                condo_total += Decimal(str(vals["total"]))
            except Exception:
                pass
            tels     = vals.get("telefones", [])
            t1       = tels[0] if len(tels) > 0 else "s/n"
            t2       = tels[1] if len(tels) > 1 else "s/n"
            dados_uni = mapa.get(uid, {})
            if t1.lower() == "s/n" and t2.lower() == "s/n":
                sem_num_local.append({
                    "condominio": nome or "",
                    "unidade":    dados_uni.get("unidade") or vals.get("nome_pdf", ""),
                    "nome":       dados_uni.get("sacado", ""),
                })

        return nome, float(condo_total.quantize(Decimal("0.01"))), len(resumo), sem_num_local

    with ThreadPoolExecutor(max_workers=_MAX_WORKERS_CONDOMINIOS) as executor:
        futures = {executor.submit(_processar, cid): cid for cid in ids_range}
        for future in as_completed(futures):
            try:
                result = future.result()
                if result:
                    nome_c, val_c, qtd_c, sem_c = result
                    total_geral += Decimal(str(val_c))
                    condo_valores[nome_c] = condo_valores.get(nome_c, 0) + val_c
                    total_unidades += qtd_c
                    sem_numero.extend(sem_c)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Dashboard _processar erro: {e}", exc_info=True)

    maior_condo = max(condo_valores, key=condo_valores.get) if condo_valores else None
    maior_valor = condo_valores.get(maior_condo, 0) if maior_condo else 0

    sem_numero.sort(key=lambda x: (x["condominio"], x["unidade"]))

    condo_ranking = sorted(
        [{"nome": k, "valor": round(v, 2)} for k, v in condo_valores.items()],
        key=lambda x: x["valor"],
        reverse=True,
    )

    resultado = {
        "total_inadimplencia": float(total_geral.quantize(Decimal("0.01"))),
        "total_condominios":   len(condo_valores),
        "total_unidades":      total_unidades,
        "maior_condo_nome":    maior_condo,
        "maior_condo_valor":   round(maior_valor, 2),
        "sem_numero_count":    len(sem_numero),
        "sem_numero":          sem_numero,
        "condo_ranking":       condo_ranking,
        "gerado_em":           datetime.now().strftime("%d/%m/%Y %H:%M"),
        "cache":               False,
    }

    with _CACHE_LOCK:
        _DASHBOARD_CACHE[cache_key] = {
            "data":       {**resultado, "cache": True},
            "expires_at": datetime.now() + timedelta(minutes=_CACHE_TTL_MINUTES),
        }

    return 200, resultado


# ── Endpoint: listar condomínios ──────────────────────────────────────────────
@admin_router.get("/condominios", response={200: list})
def listar_condominios(request):
    if not request.auth.is_staff and not request.auth.is_superuser:
        raise HttpError(403, "Admin_privileges_required")

    from django.conf import settings
    import requests as req

    headers = {
        "app_token":    settings.SUPERLOGICA_APP_TOKEN,
        "access_token": settings.SUPERLOGICA_ACCESS_TOKEN,
    }

    max_id     = getattr(settings, "SUPERLOGICA_MAX_ID", 100)
    condominios = []

    from concurrent.futures import ThreadPoolExecutor, as_completed

    def _checar(cid):
        try:
            r = req.get(
                f"{settings.SUPERLOGICA_BASE_URL}/unidades",
                headers=headers,
                params={"idCondominio": cid, "pagina": 1, "itensPorPagina": 1},
                timeout=15,
            )
            if r.status_code != 200:
                return None
            dados = r.json()
            if not dados:
                return None
            nome = dados[0].get("st_nome_cond", "").strip()
            if nome:
                return {"id": cid, "nome": nome}
        except Exception:
            pass
        return None

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(_checar, cid): cid for cid in range(1, max_id + 1)}
        for future in as_completed(futures):
            result = future.result()
            if result:
                condominios.append(result)

    condominios.sort(key=lambda x: x["nome"])
    return 200, condominios