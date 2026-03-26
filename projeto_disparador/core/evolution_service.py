import re
import time
import random
import requests
from django.conf import settings


def _format_phone(phone: str) -> str:
    """Normaliza um único número para o formato da Evolution API."""
    digits = re.sub(r"\D", "", phone.strip())
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


def _delay_between_messages():
    """Aguarda um intervalo aleatório entre WA_DELAY_MIN e WA_DELAY_MAX segundos."""
    delay_min = getattr(settings, "WA_DELAY_MIN", 20.0)
    delay_max = getattr(settings, "WA_DELAY_MAX", 45.0)
    wait = random.uniform(delay_min, delay_max)
    print(f"[ANTI-SPAM] Aguardando {wait:.1f}s antes do próximo envio...")
    time.sleep(wait)


def _typing_delay_ms() -> int:
    """Retorna um tempo de digitação aleatório em milissegundos."""
    t_min = getattr(settings, "WA_TYPING_MIN_MS", 3000)
    t_max = getattr(settings, "WA_TYPING_MAX_MS", 8000)
    return random.randint(t_min, t_max)


def send_whatsapp_message(phone: str, message: str, sleep_seconds: float = None) -> dict:
    """
    Envia mensagem de texto via Evolution API.
    - Simula digitação via campo 'delay' da API (aparece como "digitando..." para o destinatário)
    - Usa delay aleatório entre mensagens configurado em WA_DELAY_MIN/MAX
    """
    if sleep_seconds is not None:
        time.sleep(sleep_seconds)
    else:
        _delay_between_messages()

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
        "options": {
            "delay":    _typing_delay_ms(),
            "presence": "composing",
        },
        "text": message,
    }
    response = requests.post(url, json=payload, headers=headers, timeout=90)
    if not response.ok:
        print(f"[EVOLUTION ERROR] status={response.status_code} body={response.text}")
        raise Exception(f"Evolution API {response.status_code}: {response.text}")


def send_whatsapp_bulk(contacts: list, delay_between: float = None) -> list:
    """
    Envia mensagens em lote com proteção anti-spam completa:
    - Delay aleatório entre mensagens (WA_DELAY_MIN a WA_DELAY_MAX segundos)
    - Simulação de digitação antes de cada envio (WA_TYPING_MIN_MS a WA_TYPING_MAX_MS ms)
    - Pausa longa a cada WA_BATCH_SIZE mensagens (WA_BATCH_PAUSE segundos)
    """
    batch_size  = getattr(settings, "WA_BATCH_SIZE",  10)
    batch_pause = getattr(settings, "WA_BATCH_PAUSE", 300.0)
    total       = len(contacts)

    results = []
    for i, contact in enumerate(contacts):
        phone_raw = contact.get("phone", "")
        message   = contact.get("message", "")
        # Suporta múltiplos números separados por ; ou ,
        numeros = [n.strip() for n in re.split(r"[;,]", phone_raw) if n.strip()]
        for phone in numeros:
            try:
                send_whatsapp_message(phone, message, sleep_seconds=delay_between)
                results.append({"phone": phone, "status": "success"})
                print(f"[ENVIO] {i+1}/{total} ✓ {phone}")
            except Exception as e:
                results.append({"phone": phone, "status": "error", "error": str(e)})
                print(f"[ENVIO] {i+1}/{total} ✗ {phone} — {e}")

        # Pausa longa entre lotes (nunca após o último)
        if (i + 1) % batch_size == 0 and (i + 1) < total:
            mins = int(batch_pause // 60)
            secs = int(batch_pause % 60)
            print(f"[ANTI-SPAM] Lote {(i+1)//batch_size} concluído. "
                  f"Pausando {mins}min {secs}s para não ser marcado como spam...")
            time.sleep(batch_pause)

    return results