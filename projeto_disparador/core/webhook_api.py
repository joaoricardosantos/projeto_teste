"""
Webhook da Evolution API — recebe notificações de mensagens recebidas
e marca as mensagens como respondidas no banco.
"""
import logging
from ninja import Router
from django.http import HttpResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)
webhook_router = Router()


@webhook_router.post("/evolution", auth=None)
def evolution_webhook(request):
    """
    Recebe eventos da Evolution API.
    Eventos tratados: messages.upsert (mensagem recebida)
    """
    try:
        import json
        body = json.loads(request.body)
        event = body.get("event", "")

        # Log completo para debug
        logger.warning(f"WEBHOOK recebido | event={event} | body={json.dumps(body)[:800]}")

        if event != "messages.upsert":
            return {"status": "ignored"}

        # v2: data é sempre objeto; v1 legacy: podia ser lista
        raw_data = body.get("data", {})
        if isinstance(raw_data, list):
            if not raw_data:
                return {"status": "ignored"}
            data = raw_data[0]
        elif isinstance(raw_data, dict):
            # v2 encapsula em {"messages": [...]} ou diretamente no objeto
            if "messages" in raw_data:
                msgs_list = raw_data["messages"]
                if not msgs_list:
                    return {"status": "ignored"}
                data = msgs_list[0]
            else:
                data = raw_data
        else:
            return {"status": "ignored"}

        key = data.get("key", {})

        # Ignora mensagens enviadas por nós
        if key.get("fromMe"):
            return {"status": "ignored"}

        # Extrai o número que respondeu
        remote_jid = key.get("remoteJid", "")
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

        # Normaliza: remove tudo que não é dígito
        import re
        phone_digits = re.sub(r"\D", "", phone)

        # Gera variações para busca
        numeros_busca = set()
        numeros_busca.add(phone_digits)
        if phone_digits.startswith("55") and len(phone_digits) > 11:
            numeros_busca.add(phone_digits[2:])   # sem DDI
        if not phone_digits.startswith("55"):
            numeros_busca.add("55" + phone_digits) # com DDI

        # Marca mensagens mais recentes desse número como respondida
        from core.models import MensagemEnviada
        msgs = MensagemEnviada.objects.filter(
            telefone__in=list(numeros_busca),
            status=MensagemEnviada.STATUS_ENVIADO,
        ).order_by("-enviada_em")[:5]

        if msgs:
            for msg in msgs:
                msg.status = MensagemEnviada.STATUS_RESPONDIDO
                msg.respondida_em = timezone.now()
                msg.resposta = resposta
                msg.save()
            logger.info(f"Webhook: {phone} respondeu — {len(msgs)} mensagem(ns) marcada(s)")

        return {"status": "ok"}

    except Exception as e:
        logger.error(f"Webhook erro: {e}", exc_info=True)
        return {"status": "error", "detail": str(e)}