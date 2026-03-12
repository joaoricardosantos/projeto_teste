import csv
from io import StringIO, BytesIO

import openpyxl
import requests

from core.evolution_service import send_whatsapp_message
from core.models import MessageTemplate


_FALLBACK_TEMPLATE = (
    "Olá, {nome}! 👋\n\n"
    "Identificamos um débito em aberto referente ao condomínio *{condominio}*.\n"
    "📅 Data de atraso: *{data_atraso}*\n"
    "💰 Valor: *R$ {valor}*\n\n"
    "Entre em contato com a administração para regularizar sua situação.\n"
    "Agradecemos sua atenção!"
)


def _render_message(*, nome, condominio, valor, data_atraso):
    try:
        template = MessageTemplate.objects.get(is_active=True)
        return template.render(nome=nome, condominio=condominio, valor=valor, data_atraso=data_atraso)
    except MessageTemplate.DoesNotExist:
        return _FALLBACK_TEMPLATE.format(nome=nome, condominio=condominio, valor=valor, data_atraso=data_atraso)


def _send_to_contact(condo_name, name, phone, debt_amount, due_date):
    message = _render_message(nome=name, condominio=condo_name, valor=debt_amount, data_atraso=due_date)
    send_whatsapp_message(phone, message)


def process_csv(file_obj):
    decoded = file_obj.read().decode("utf-8")
    reader = csv.DictReader(StringIO(decoded))
    success, errors = 0, 0
    for row in reader:
        try:
            condo    = row.get("condominio", "").strip()
            name     = row.get("nome", "").strip()
            phone    = row.get("telefone", "").strip()
            debt     = row.get("valor_debito", "").strip()
            due_date = row.get("data_atraso", "").strip()
            if condo and name and phone and debt:
                _send_to_contact(condo, name, phone, debt, due_date or "N/A")
                success += 1
            else:
                errors += 1
        except Exception:
            errors += 1
    return {"success": success, "errors": errors}


def process_xlsx(file_obj):
    content = file_obj.read()
    wb = openpyxl.load_workbook(BytesIO(content), read_only=True, data_only=True)
    ws = wb.active
    rows = list(ws.iter_rows(values_only=True))
    if not rows:
        return {"success": 0, "errors": 0}

    raw_headers = [str(h).strip().lower() if h else "" for h in rows[0]]

    def _col(candidates):
        for c in candidates:
            if c in raw_headers:
                return raw_headers.index(c)
        return None

    idx_condo    = _col(["condomínio", "condominio"])
    idx_name     = _col(["nome"])
    idx_phone    = _col(["telefones", "telefone"])
    idx_debt     = _col(["valor da dívida com juros", "valor_debito", "valor da divida com juros"])
    idx_due_date = _col(["data de atraso", "data_atraso", "data atraso"])

    if None in (idx_condo, idx_name, idx_phone, idx_debt):
        raise ValueError("Cabeçalhos não reconhecidos. Esperado: Condomínio, Nome, Telefones, Valor da dívida com juros, Data de atraso")

    success, errors = 0, 0
    for row in rows[1:]:
        try:
            condo      = str(row[idx_condo] or "").strip()
            name       = str(row[idx_name]  or "").strip()
            raw_phones = str(row[idx_phone] or "").strip()
            debt       = str(row[idx_debt]  or "").strip()
            due_date   = str(row[idx_due_date] if idx_due_date is not None else "").strip() or "N/A"
            if not (condo and name and raw_phones and debt):
                errors += 1
                continue
            phones = [p.strip() for p in raw_phones.split("|") if p.strip()]
            sent = False
            for phone in phones:
                try:
                    _send_to_contact(condo, name, phone, debt, due_date)
                    sent = True
                    break
                except requests.RequestException:
                    continue
            if sent:
                success += 1
            else:
                errors += 1
        except Exception:
            errors += 1
    wb.close()
    return {"success": success, "errors": errors}


def process_defaulters_spreadsheet(file_obj, filename):
    name_lower = filename.lower()
    if name_lower.endswith(".xlsx"):
        return process_xlsx(file_obj)
    elif name_lower.endswith(".csv"):
        return process_csv(file_obj)
    else:
        raise ValueError("Formato não suportado. Envie um arquivo .csv ou .xlsx")
