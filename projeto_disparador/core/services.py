import csv
import openpyxl
import requests
from io import StringIO
from django.conf import settings
from core.evolution_service import send_whatsapp_bulk


def _render_template(body: str, condo_name: str, contact: str, debt_amount: str) -> str:
    """Substitui variáveis {{nome}}, {{condominio}}, {{valor}} no corpo do template."""
    return (
        body
        .replace("{{nome}}", contact)
        .replace("{{condominio}}", condo_name)
        .replace("{{valor}}", debt_amount)
    )


def _build_default_message(condo_name: str, debt_amount: str) -> str:
    return f"Prezado condomínio {condo_name}, consta um débito de {debt_amount}."


def process_defaulters_spreadsheet(file_obj):
    """Processa CSV com mensagem padrão e envia via WhatsApp."""
    decoded_file = file_obj.read().decode("utf-8")
    csv_reader = csv.DictReader(StringIO(decoded_file))

    contacts = []
    error_count = 0

    for row in csv_reader:
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
    """Processa CSV com template específico e envia via WhatsApp."""
    from core.models import MessageTemplate

    try:
        template = MessageTemplate.objects.get(id=template_id)
    except MessageTemplate.DoesNotExist:
        raise ValueError("Template_not_found")

    decoded_file = file_obj.read().decode("utf-8")
    csv_reader = csv.DictReader(StringIO(decoded_file))

    contacts = []
    error_count = 0

    for row in csv_reader:
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
    Lê o Excel gerado pelo relatório (aba Resumo) e envia WhatsApp
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

    wb = openpyxl.load_workbook(file_obj)
    ws = wb["Resumo"] if "Resumo" in wb.sheetnames else wb.active

    headers = [str(cell.value).strip() if cell.value else "" for cell in ws[1]]

    def col(name):
        try:
            return headers.index(name)
        except ValueError:
            return None

    idx_condo     = col("Condomínio")
    idx_unidade   = col("Unidade")
    idx_telefones = col("Telefones")
    idx_total     = col("Total")

    if idx_telefones is None:
        raise ValueError("Coluna_Telefones_nao_encontrada")

    contacts = []
    error_count = 0

    for row in ws.iter_rows(min_row=2, values_only=True):
        telefones_raw = row[idx_telefones] if idx_telefones is not None else None
        condo_name    = str(row[idx_condo])   if idx_condo   is not None and row[idx_condo]   else ""
        unidade       = str(row[idx_unidade]) if idx_unidade is not None and row[idx_unidade] else ""
        total         = str(row[idx_total])   if idx_total   is not None and row[idx_total]   else ""

        if not telefones_raw:
            error_count += 1
            continue

        telefones = [t.strip() for t in str(telefones_raw).split("|") if t.strip()]
        if not telefones:
            error_count += 1
            continue

        # Formata valor BRL
        try:
            valor_fmt = f"R$ {float(total):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            valor_fmt = total

        # Mensagem
        if template_body:
            message = _render_template(template_body, condo_name, unidade, valor_fmt)
        else:
            message = (
                f"Olá! Identificamos débito em aberto referente à unidade *{unidade}* "
                f"do condomínio *{condo_name}*.\n"
                f"Valor total com encargos: *{valor_fmt}*.\n"
                f"Entre em contato para regularização."
            )

        for phone in telefones:
            contacts.append({"phone": phone, "message": message})

    result = send_whatsapp_bulk(contacts)
    result["errors"] += error_count
    return result