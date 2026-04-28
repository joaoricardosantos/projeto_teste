"""
Serviço de integração com Google Drive para buscar pastas de modelos por condomínio.

Estrutura esperada no Drive:
    {DRIVE_EXECUCOES_FOLDER_ID}/
    ├── 18 - JANGADAS/
    │   └── 01 - Modelos/   ← arquivos aqui
    ├── 19 - OUTRO/
    │   └── 01 - Modelos/
    └── ...
"""

import io
import os
import re
import unicodedata
from typing import List, Dict, Any, Optional, Tuple

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload


SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
]

FOLDER_MIME = "application/vnd.google-apps.folder"
GOOGLE_DOC_MIME = "application/vnd.google-apps.document"
GOOGLE_SHEET_MIME = "application/vnd.google-apps.spreadsheet"
GOOGLE_SLIDE_MIME = "application/vnd.google-apps.presentation"

# Nome (parcial) da subpasta de modelos dentro da pasta do condomínio
_SUBPASTA_MODELOS_HINTS = ("modelo", "modelos")


def _get_credentials() -> Optional[Credentials]:
    creds_file = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_FILE")
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    if creds_file and os.path.exists(creds_file):
        return Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    if creds_json:
        import json
        return Credentials.from_service_account_info(json.loads(creds_json), scopes=SCOPES)
    return None


def _get_drive_service():
    creds = _get_credentials()
    if not creds:
        raise RuntimeError("Credenciais do Google Drive não configuradas")
    return build("drive", "v3", credentials=creds, cache_discovery=False)


def _slug(s: str) -> str:
    """Normaliza string para comparação (remove acentos, lower, só alfanum)."""
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", s.lower())


def listar_subpastas(parent_id: str) -> List[Dict[str, str]]:
    """Lista subpastas imediatas de uma pasta."""
    service = _get_drive_service()
    q = f"'{parent_id}' in parents and mimeType='{FOLDER_MIME}' and trashed=false"
    results = []
    page_token = None
    while True:
        resp = service.files().list(
            q=q,
            fields="nextPageToken, files(id, name)",
            pageSize=200,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="allDrives",
        ).execute()
        results.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return results


def listar_arquivos(folder_id: str) -> List[Dict[str, Any]]:
    """Lista arquivos (não-pastas) de uma pasta, não-recursivo."""
    service = _get_drive_service()
    q = f"'{folder_id}' in parents and mimeType != '{FOLDER_MIME}' and trashed=false"
    results = []
    page_token = None
    while True:
        resp = service.files().list(
            q=q,
            fields="nextPageToken, files(id, name, mimeType, size)",
            pageSize=200,
            pageToken=page_token,
            supportsAllDrives=True,
            includeItemsFromAllDrives=True,
            corpora="allDrives",
        ).execute()
        results.extend(resp.get("files", []))
        page_token = resp.get("nextPageToken")
        if not page_token:
            break
    return results


def _export_mime_for(google_mime: str) -> Tuple[str, str]:
    """Retorna (mime_export, extensao) para um Google Doc/Sheet/Slide."""
    if google_mime == GOOGLE_DOC_MIME:
        return (
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            ".docx",
        )
    if google_mime == GOOGLE_SHEET_MIME:
        return (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            ".xlsx",
        )
    if google_mime == GOOGLE_SLIDE_MIME:
        return (
            "application/vnd.openxmlformats-officedocument.presentationml.presentation",
            ".pptx",
        )
    return ("application/pdf", ".pdf")


def baixar_arquivo(file_id: str, mime_type: str) -> bytes:
    """Baixa o conteúdo de um arquivo. Exporta Google Docs/Sheets/Slides como Office."""
    service = _get_drive_service()
    if mime_type.startswith("application/vnd.google-apps"):
        export_mime, _ = _export_mime_for(mime_type)
        req = service.files().export_media(fileId=file_id, mimeType=export_mime)
    else:
        req = service.files().get_media(fileId=file_id, supportsAllDrives=True)
    buf = io.BytesIO()
    downloader = MediaIoBaseDownload(buf, req)
    done = False
    while not done:
        _, done = downloader.next_chunk()
    return buf.getvalue()


def baixar_pasta_como_dict(folder_id: str) -> Dict[str, bytes]:
    """
    Baixa todos os arquivos de uma pasta (não-recursivo).
    Retorna {nome_arquivo_com_extensao: bytes}.
    """
    arquivos = listar_arquivos(folder_id)
    out: Dict[str, bytes] = {}
    for f in arquivos:
        mime = f["mimeType"]
        nome = f["name"]
        if mime.startswith("application/vnd.google-apps"):
            _, ext = _export_mime_for(mime)
            if not nome.lower().endswith(ext):
                nome = nome + ext
        try:
            out[nome] = baixar_arquivo(f["id"], mime)
        except Exception:
            # Ignora arquivos que não podem ser baixados (atalhos, etc.)
            continue
    return out


def buscar_pasta_condominio(
    parent_id: str,
    nome_condominio: str,
) -> Tuple[Optional[Dict[str, str]], List[Dict[str, str]]]:
    """
    Tenta encontrar a pasta do condomínio dentro de `parent_id` (ex: "01 - EXECUÇÕES").
    Retorna (pasta_modelos_encontrada, candidatos).

    - Se houver match único: retorna (pasta_modelos, [pasta_condo])
    - Se múltiplas pastas fizerem match, retorna (None, lista de candidatos)
    - Se nenhuma: retorna (None, [])
    """
    if not parent_id or not nome_condominio:
        return None, []

    subpastas = listar_subpastas(parent_id)
    alvo = _slug(nome_condominio)

    # Match por slug contido no nome (ignora prefixo "18 - ")
    candidatos = [p for p in subpastas if alvo and alvo in _slug(p["name"])]

    if len(candidatos) != 1:
        return None, candidatos

    pasta_condo = candidatos[0]
    # Dentro da pasta do condomínio, procura subpasta "Modelos"
    sub = listar_subpastas(pasta_condo["id"])
    pasta_modelos = None
    for s in sub:
        s_slug = _slug(s["name"])
        if any(h in s_slug for h in _SUBPASTA_MODELOS_HINTS):
            pasta_modelos = s
            break
    # Se não achar subpasta de modelos, usa a própria pasta do condomínio
    return (pasta_modelos or pasta_condo), [pasta_condo]


def info_pasta(folder_id: str) -> Optional[Dict[str, str]]:
    """Retorna {id, name} da pasta, ou None se não existir."""
    try:
        service = _get_drive_service()
        f = service.files().get(
            fileId=folder_id,
            fields="id, name, mimeType",
            supportsAllDrives=True,
        ).execute()
        if f.get("mimeType") != FOLDER_MIME:
            return None
        return {"id": f["id"], "name": f["name"]}
    except Exception:
        return None
