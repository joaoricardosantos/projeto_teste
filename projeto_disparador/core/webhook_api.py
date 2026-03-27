"""
Webhook da Evolution API — recebe notificações de mensagens recebidas
e marca as mensagens como respondidas no banco.
"""
import re
import json
import logging
import requests as _requests
from ninja import Router
from django.utils import timezone

logger = logging.getLogger(__name__)
webhook_router = Router()


def _resolve_lid_to_phone(lid: str, instance: str, base_url: str, api_key: str) -> str | None:
    """Resolve um @lid para número de telefone via Evolution API."""
    try:
        lid_id = lid.replace("@lid", "")
        url = f"{base_url}/chat/findContacts/{instance}"
        resp = _requests.post(
            url,
            json={"where": {"id": lid}},
            headers={"apikey": api_key},
            timeout=10,
        )
        if resp.ok:
            data = resp.json()
            contacts = data if isinstance(data, list) else data.get("contacts", [])
            for c in contacts:
                phone = c.get("pushName") and (c.get("id", "").replace("@s.whatsapp.net", ""))
                # tenta pegar o número do campo 'id' em formato @s.whatsapp.net
                jid = c.get("id", "")
                if "@s.whatsapp.net" in jid:
                    return jid.replace("@s.whatsapp.net", "")
    except Exception as e:
        logger.warning(f"_resolve_lid_to_phone erro: {e}")
    return None


@webhook_router.post("/evolution", auth=None, response={200: dict})
def evolution_webhook(request):
    """
    Recebe eventos da Evolution API.
    Eventos tratados: messages.upsert (mensagem recebida)
    """
    try:
        raw = request.body
        if isinstance(raw, (bytes, bytearray)):
            raw = raw.decode("utf-8", errors="replace")
        body = json.loads(raw.strip())
        event = body.get("event", "")

        if event != "messages.upsert":
            return {"status": "ignored"}

        data = body.get("data", {})
        if isinstance(data, list):
            data = data[0] if data else {}
        elif isinstance(data, dict) and "messages" in data:
            msgs_list = data["messages"]
            data = msgs_list[0] if msgs_list else {}

        key = data.get("key", {})

        # Ignora mensagens enviadas por nós
        if key.get("fromMe"):
            return {"status": "ignored"}

        remote_jid = key.get("remoteJid", "")
        push_name  = data.get("pushName", "")

        if "@lid" in remote_jid:
            from django.conf import settings
            instance  = body.get("instance", getattr(settings, "EVOLUTION_INSTANCE", ""))
            base_url  = getattr(settings, "EVOLUTION_BASE_URL", "").rstrip("/")
            api_key   = getattr(settings, "EVOLUTION_API_KEY", "")

            # Tenta resolver via API
            phone = _resolve_lid_to_phone(remote_jid, instance, base_url, api_key)

            # Fallback 1: busca pelo sufixo numérico do @lid nos telefones cadastrados
            if not phone:
                lid_digits = re.sub(r"\D", "", remote_jid)
                if lid_digits:
                    from core.models import MensagemEnviada
                    msg_by_lid = MensagemEnviada.objects.filter(
                        telefone__endswith=lid_digits[-8:],
                    ).order_by("-enviada_em").first()
                    if msg_by_lid:
                        phone = msg_by_lid.telefone
                        logger.info(f"Webhook: @lid resolvido via sufixo numérico '{lid_digits[-8:]}' → {phone}")

            # Fallback 2: busca pelo pushName na tabela MensagemEnviada
            if not phone and push_name:
                from core.models import MensagemEnviada
                msg_by_name = MensagemEnviada.objects.filter(
                    nome__icontains=push_name,
                ).order_by("-enviada_em").first()
                if msg_by_name:
                    phone = msg_by_name.telefone
                    logger.info(f"Webhook: @lid resolvido via pushName '{push_name}' → {phone}")

            if not phone:
                logger.warning(f"Webhook: não foi possível resolver @lid {remote_jid} (pushName={push_name})")
                return {"status": "ignored"}
        else:
            phone = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")

        if not phone:
            return {"status": "ignored"}

        # Texto da resposta
        msg_content = data.get("message", {})
        resposta = (
            msg_content.get("conversation")
            or msg_content.get("extendedTextMessage", {}).get("text")
            or "[mídia]"
        )

        # Normaliza e gera variações para busca
        phone_digits = re.sub(r"\D", "", phone)
        numeros_busca = {phone_digits}
        if phone_digits.startswith("55") and len(phone_digits) > 11:
            numeros_busca.add(phone_digits[2:])
        if not phone_digits.startswith("55"):
            numeros_busca.add("55" + phone_digits)

        from core.models import MensagemEnviada
        msgs = MensagemEnviada.objects.filter(
            telefone__in=list(numeros_busca),
        ).exclude(
            status=MensagemEnviada.STATUS_RESPONDIDO,
        ).order_by("-enviada_em")[:5]

        if msgs:
            for msg in msgs:
                msg.status       = MensagemEnviada.STATUS_RESPONDIDO
                msg.respondida_em = timezone.now()
                msg.resposta     = resposta
                msg.save()
            logger.info(f"Webhook: {phone} respondeu — {len(msgs)} mensagem(ns) marcada(s)")
        else:
            logger.warning(f"Webhook: {phone} respondeu mas nenhuma mensagem encontrada no banco")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Webhook erro: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}