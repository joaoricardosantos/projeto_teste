import csv
import openpyxl
import requests
from io import StringIO, BytesIO
from django.conf import settings
from core.evolution_service import send_whatsapp_bulk


def _render_template(body: str, condo_name: str, contact: str, debt_amount: str, vencimento: str = "", competencia: str = "") -> str:
    return (
        body
        .replace("{{nome}}", contact)
        .replace("{{condominio}}", condo_name)
        .replace("{{valor}}", debt_amount)
        .replace("{{vencimento}}", vencimento)
        .replace("{{competencia}}", competencia)
    )


def _build_default_message(condo_name: str, debt_amount: str) -> str:
    return f"Prezado condomínio {condo_name}, consta um débito de {debt_amount}."


def _read_spreadsheet_rows(file_obj) -> list[dict]:
    """
    Lê CSV ou XLSX e retorna lista de dicts com as colunas.
    Detecta o formato pelo atributo .name do arquivo.
    """
    filename = getattr(file_obj, "name", "").lower()

    if filename.endswith(".xlsx"):
        wb = openpyxl.load_workbook(BytesIO(file_obj.read()))
        ws = wb.active
        headers = [str(cell.value).strip() if cell.value else "" for cell in ws[1]]
        rows = []
        for row in ws.iter_rows(min_row=2, values_only=True):
            rows.append({headers[i]: (str(v).strip() if v is not None else "") for i, v in enumerate(row)})
        return rows
    else:
        decoded = file_obj.read().decode("utf-8")
        return list(csv.DictReader(StringIO(decoded)))


def process_defaulters_spreadsheet(file_obj):
    """Processa CSV ou XLSX com mensagem padrão e envia via WhatsApp."""
    contacts = []
    error_count = 0

    for row in _read_spreadsheet_rows(file_obj):
        condo_name  = (row.get("condominio") or "").strip()
        contact     = (row.get("contato") or "").strip()
        debt_amount = (row.get("valor_debito") or "").strip()

        if condo_name and contact and debt_amount:
            message = _build_default_message(condo_name, debt_amount)
            contacts.append({"phone": contact, "message": message})
        else:
            error_count += 1

    result = send_whatsapp_bulk(contacts)
    result["errors"] += error_count
    return result


def process_defaulters_with_template(file_obj, template_id: str):
    """Processa CSV ou XLSX com template específico e envia via WhatsApp."""
    from core.models import MessageTemplate

    try:
        template = MessageTemplate.objects.get(id=template_id)
    except MessageTemplate.DoesNotExist:
        raise ValueError("Template_not_found")

    contacts = []
    error_count = 0

    for row in _read_spreadsheet_rows(file_obj):
        condo_name  = (row.get("condominio") or "").strip()
        contact     = (row.get("contato") or "").strip()
        debt_amount = (row.get("valor_debito") or "").strip()

        if condo_name and contact and debt_amount:
            message = _render_template(template.body, condo_name, contact, debt_amount)
            contacts.append({"phone": contact, "message": message})
        else:
            error_count += 1

    result = send_whatsapp_bulk(contacts)
    result["errors"] += error_count
    return result


def process_excel_report_dispatch(file_obj, template_id: str = None):
    """
    Lê CSV ou XLSX do relatório (aba Resumo ou primeira aba) e envia WhatsApp
    para cada número da coluna 'Telefones'.
    Colunas esperadas: Condomínio | Unidade | Telefones | Total
    """
    from core.models import MessageTemplate

    template_body = None
    if template_id:
        try:
            t = MessageTemplate.objects.get(id=template_id)
            template_body = t.body
        except MessageTemplate.DoesNotExist:
            raise ValueError("Template_not_found")

    filename = getattr(file_obj, "name", "").lower()

    if filename.endswith(".csv"):
        decoded = file_obj.read().decode("utf-8")
        raw_rows = list(csv.DictReader(StringIO(decoded)))
        # Normaliza para o mesmo formato usado pelo loop abaixo
        headers = list(raw_rows[0].keys()) if raw_rows else []

        def get_col(row, name):
            return row.get(name, "") or ""

        rows_iter = raw_rows
        use_dict = True
    else:
        wb = openpyxl.load_workbook(file_obj)
        ws = wb["Resumo"] if "Resumo" in wb.sheetnames else wb.active
        headers = [str(cell.value).strip() if cell.value else "" for cell in ws[1]]
        rows_iter = list(ws.iter_rows(min_row=2, values_only=True))
        use_dict = False

    def col_idx(name):
        try:
            return headers.index(name)
        except ValueError:
            return None

    idx_condo       = col_idx("Condomínio")
    idx_unidade     = col_idx("Unidade")
    idx_telefones   = col_idx("Telefones")
    idx_vencimento  = col_idx("Vencimento")
    idx_competencia = col_idx("Competência")
    idx_total       = col_idx("Total")

    if idx_telefones is None:
        raise ValueError("Coluna_Telefones_nao_encontrada")

    contacts = []
    error_count = 0

    for row in rows_iter:
        if use_dict:
            telefones_raw = row.get("Telefones", "")
            condo_name    = str(row.get("Condomínio", "") or "")
            unidade       = str(row.get("Unidade", "") or "")
            vencimento    = str(row.get("Vencimento", "") or "")
            competencia   = str(row.get("Competência", "") or "")
            total         = str(row.get("Total", "") or "")
        else:
            telefones_raw = row[idx_telefones]  if idx_telefones  is not None else None
            condo_name    = str(row[idx_condo])       if idx_condo      is not None and row[idx_condo]      else ""
            unidade       = str(row[idx_unidade])     if idx_unidade    is not None and row[idx_unidade]    else ""
            vencimento    = str(row[idx_vencimento])  if idx_vencimento  is not None and row[idx_vencimento]  else ""
            competencia   = str(row[idx_competencia]) if idx_competencia is not None and row[idx_competencia] else ""
            total         = str(row[idx_total])       if idx_total      is not None and row[idx_total]      else ""

        if not telefones_raw:
            error_count += 1
            continue

        telefones = [t.strip() for t in str(telefones_raw).split("|") if t.strip()]
        if not telefones:
            error_count += 1
            continue

        try:
            valor_fmt = f"R$ {float(total):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            valor_fmt = total

        if template_body:
            message = _render_template(template_body, condo_name, unidade, valor_fmt, vencimento, competencia)
        else:
            message = (
                f"Olá! Identificamos débito em aberto referente à unidade *{unidade}* "
                f"do condomínio *{condo_name}*.\n"
                f"Vencimento: *{vencimento}* | Competência: *{competencia}*\n"
                f"Valor total com encargos: *{valor_fmt}*.\n"
                f"Entre em contato para regularização."
            )

        for phone in telefones:
            contacts.append({"phone": phone, "message": message})

    result = send_whatsapp_bulk(contacts)
    result["errors"] += error_count
    return result