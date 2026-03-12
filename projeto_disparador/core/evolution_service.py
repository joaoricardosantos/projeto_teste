import re
import time
import requests
from django.conf import settings


def _format_phone(phone: str) -> str:
    """
    Normaliza o número para o formato da Evolution API:
    apenas dígitos com DDI 55 (Brasil).
    Ex: "(84) 99999-1234" → "5584999991234"
    """
    digits = re.sub(r"\D", "", phone)
    if digits.startswith("55") and len(digits) > 11:
        digits = digits[2:]
    return "55" + digits


def send_whatsapp_message(phone: str, message: str, sleep_seconds: float = 5.0) -> dict:
    """
    Envia mensagem de texto via Evolution API.
    Aguarda sleep_seconds antes de enviar (padrão: 5s).
    Lança requests.HTTPError em caso de falha HTTP.
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
    response.raise_for_status()
    return response.json()


def send_whatsapp_bulk(contacts: list, delay_between: float = 5.0) -> list:
    """
    Envia mensagens em lote.
    contacts: lista de dicts com 'phone' e 'message'.
    Aguarda delay_between segundos entre cada envio.
    Retorna lista de resultados com status de cada envio.
    """
    results = []
    for contact in contacts:
        phone = contact.get("phone", "")
        message = contact.get("message", "")
        try:
            response = send_whatsapp_message(phone, message, sleep_seconds=delay_between)
            results.append({"phone": phone, "status": "success", "response": response})
        except Exception as e:
            results.append({"phone": phone, "status": "error", "error": str(e)})
    return results