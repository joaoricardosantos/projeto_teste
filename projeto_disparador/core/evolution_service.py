import re
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


def send_whatsapp_message(phone: str, message: str) -> dict:
    """
    Envia mensagem de texto via Evolution API.
    Lança requests.HTTPError em caso de falha HTTP.
    """
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
        "text": message,
    }

    response = requests.post(url, json=payload, headers=headers, timeout=15)
    response.raise_for_status()
    return response.json()