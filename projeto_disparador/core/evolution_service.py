import re
import time
import requests
from django.conf import settings


def _format_phone(phone: str) -> str:
    """
    Normaliza o número para o formato da Evolution API.
    Pega apenas o primeiro número se houver múltiplos separados por ; ou ,
    """
    # Pega apenas o primeiro número se houver múltiplos
    phone = phone.split(";")[0].split(",")[0].strip()
    digits = re.sub(r"\D", "", phone)
    # Remove DDI duplicado (5555...)
    while digits.startswith("55") and len(digits) > 13:
        digits = digits[2:]
    # Remove DDI simples se sobrar mais de 11 dígitos
    if digits.startswith("55") and len(digits) > 11:
        digits = digits[2:]
    # Garante 11 dígitos (com 9 na frente para celular)
    if len(digits) == 10:
        digits = digits[:2] + "9" + digits[2:]
    return "55" + digits


def send_whatsapp_message(phone: str, message: str, sleep_seconds: float = 5.0) -> dict:
    """
    Envia mensagem de texto via Evolution API.
    Aguarda sleep_seconds antes de enviar (padrão: 5s).
    """
    time.sleep(sleep_seconds)
    instance = settings.EVOLUTION_INSTANCE
    api_key  = settings.EVOLUTION_API_KEY
    base_url = settings.EVOLUTION_BASE_URL.rstrip("/")
    url = f"{base_url}/message/sendText/{instance}"
    headers = {
        "Content-Type": "application/json",
        "apikey": api_key,
    }
    payload = {
        "number": _format_phone(phone),
        "textMessage": {"text": message},
    }
    response = requests.post(url, json=payload, headers=headers, timeout=15)
    if not response.ok:
        print(f"[EVOLUTION ERROR] status={response.status_code} body={response.text}")
    response.raise_for_status()


def send_whatsapp_bulk(contacts: list, delay_between: float = 5.0) -> list:
    """
    Envia mensagens em lote.
    contacts: lista de dicts com 'phone' e 'message'.
    """
    results = []
    for contact in contacts:
        phone   = contact.get("phone", "")
        message = contact.get("message", "")
        try:
            send_whatsapp_message(phone, message, sleep_seconds=delay_between)
            results.append({"phone": phone, "status": "success"})
        except Exception as e:
            results.append({"phone": phone, "status": "error", "error": str(e)})
    return results