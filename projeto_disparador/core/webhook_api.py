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
        url = f"{base_url}/chat/findContacts/{instance}"
        resp = _requests.post(
            url,
            json={"where": {"remoteJid": lid}},
            headers={"apikey": api_key},
            timeout=10,
        )
        print(f"WEBHOOK_DEBUG findContacts status={resp.status_code} body={resp.text[:500]}", flush=True)
        if resp.ok:
            data = resp.json()
            contacts = data if isinstance(data, list) else []
            for c in contacts:
                jid = c.get("remoteJid", "")
                if "@s.whatsapp.net" in jid:
                    return re.sub(r"\D", "", jid)
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
        print(f"WEBHOOK_DEBUG event={event} body={json.dumps(body)}", flush=True)

        if event != "messages.upsert":
            return {"status": "ignored"}

        data = body.get("data", {})
        # Ignora mensagens de grupos
        key_check = data if isinstance(data, dict) else {}
        if isinstance(data, list):
            key_check = data[0] if data else {}
        rjid_check = key_check.get("key", {}).get("remoteJid", "")
        if "@g.us" in rjid_check:
            return {"status": "ignored"}
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

        # O campo 'sender' no body raiz contém o número real mesmo quando remoteJid é @lid
        sender_raw = body.get("sender", "")
        sender_phone = re.sub(r"\D", "", sender_raw.replace("@s.whatsapp.net", "").replace("@c.us", "")) if sender_raw else ""

        if "@lid" in remote_jid:
            from django.conf import settings
            instance  = body.get("instance", getattr(settings, "EVOLUTION_INSTANCE", ""))
            base_url  = getattr(settings, "EVOLUTION_BASE_URL", "").rstrip("/")
            api_key   = getattr(settings, "EVOLUTION_API_KEY", "")

            # Primeiro: usa o campo 'sender' do payload (número real)
            phone = sender_phone if sender_phone else None

            # Segundo: tenta resolver via API
            if not phone:
                phone = _resolve_lid_to_phone(remote_jid, instance, base_url, api_key)

            # Fallback 1: extrai número do @lid e busca variações no banco
            if not phone:
                lid_digits = re.sub(r"\D", "", remote_jid)
                if lid_digits:
                    from core.models import MensagemEnviada
                    # Gera variações: com/sem 55, com/sem 9 extra
                    candidatos = set()
                    candidatos.add(lid_digits)
                    if lid_digits.startswith("55"):
                        sem55 = lid_digits[2:]
                        candidatos.add(sem55)
                        # Remove 9 extra (ex: 84998... → 8498...)
                        if len(sem55) == 11 and sem55[2] == "9":
                            candidatos.add(sem55[:2] + sem55[3:])
                    else:
                        candidatos.add("55" + lid_digits)
                    # Busca pelos últimos 8 dígitos também
                    candidatos.add(lid_digits[-8:])

                    msg_by_lid = MensagemEnviada.objects.filter(
                        telefone__in=list(candidatos),
                    ).order_by("-enviada_em").first()
                    if not msg_by_lid:
                        msg_by_lid = MensagemEnviada.objects.filter(
                            telefone__endswith=lid_digits[-8:],
                        ).order_by("-enviada_em").first()
                    if msg_by_lid:
                        phone = msg_by_lid.telefone
                        print(f"WEBHOOK_DEBUG @lid resolvido via número '{lid_digits}' → {phone}", flush=True)

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

        # Normaliza e gera variações para busca (com/sem 55, com/sem 9 extra)
        phone_digits = re.sub(r"\D", "", phone)
        numeros_busca = {phone_digits}
        # Garante versão com 55
        if not phone_digits.startswith("55"):
            com55 = "55" + phone_digits
        else:
            com55 = phone_digits
        numeros_busca.add(com55)
        sem55 = com55[2:]
        numeros_busca.add(sem55)
        # Variações com/sem 9 extra (DDD + 9 + número)
        # sem55 deve ter 10 ou 11 dígitos
        if len(sem55) == 11 and sem55[2] == "9":
            # remove o 9 extra: 84 9 98887777 → 84 98887777
            sem9 = sem55[:2] + sem55[3:]
            numeros_busca.add(sem9)
            numeros_busca.add("55" + sem9)
        elif len(sem55) == 10:
            # adiciona o 9 extra
            com9 = sem55[:2] + "9" + sem55[2:]
            numeros_busca.add(com9)
            numeros_busca.add("55" + com9)

        from core.models import MensagemEnviada
        msgs = MensagemEnviada.objects.filter(
            telefone__in=list(numeros_busca),
        ).exclude(
            status=MensagemEnviada.STATUS_RESPONDIDO,
        ).order_by("-enviada_em")[:5]

        # Fallback: busca pelos últimos 8 dígitos
        if not msgs:
            sufixo = phone_digits[-8:]
            msgs = MensagemEnviada.objects.filter(
                telefone__endswith=sufixo,
            ).exclude(
                status=MensagemEnviada.STATUS_RESPONDIDO,
            ).order_by("-enviada_em")[:5]
            if msgs:
                print(f"WEBHOOK_DEBUG sufixo match: {phone_digits} → sufixo {sufixo}", flush=True)

        if msgs:
            for msg in msgs:
                msg.status        = MensagemEnviada.STATUS_RESPONDIDO
                msg.respondida_em = timezone.now()
                msg.resposta      = resposta
                msg.save()
            logger.info(f"Webhook: {phone} respondeu — {len(msgs)} mensagem(ns) marcada(s)")
        else:
            logger.warning(f"Webhook: {phone} respondeu mas nenhuma mensagem encontrada no banco")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Webhook erro: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}