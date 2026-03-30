"""
Management command para reprocessar respostas recebidas da Evolution API
e marcar as MensagemEnviada correspondentes como respondidas.

Uso:
    python manage.py reprocessar_respostas
    python manage.py reprocessar_respostas --dias 30
    python manage.py reprocessar_respostas --limite 500
"""
import re
import time
import logging
from datetime import timedelta

import requests
from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from core.models import MensagemEnviada

logger = logging.getLogger(__name__)


def _phone_variations(phone: str) -> set:
    """Gera todas as variações de formato de um número de telefone."""
    digits = re.sub(r"\D", "", phone)
    variants = {digits}

    if not digits.startswith("55"):
        com55 = "55" + digits
    else:
        com55 = digits
    variants.add(com55)
    sem55 = com55[2:]
    variants.add(sem55)

    if len(sem55) == 11 and sem55[2] == "9":
        sem9 = sem55[:2] + sem55[3:]
        variants.add(sem9)
        variants.add("55" + sem9)
    elif len(sem55) == 10:
        com9 = sem55[:2] + "9" + sem55[2:]
        variants.add(com9)
        variants.add("55" + com9)

    return variants


def _fetch_messages(instance: str, base_url: str, api_key: str, phone_jid: str, count: int = 50) -> list:
    """Busca o histórico de mensagens recebidas (fromMe=false) de um chat via Evolution API."""
    url = f"{base_url}/chat/findMessages/{instance}"
    try:
        resp = requests.post(
            url,
            json={
                "where": {
                    "key": {"remoteJid": phone_jid},
                    "fromMe": False,
                },
                "limit": count,
            },
            headers={"apikey": api_key},
            timeout=15,
        )
        if resp.ok:
            data = resp.json()
            records = []
            if isinstance(data, dict) and "messages" in data:
                records = data["messages"].get("records", [])
            elif isinstance(data, list):
                records = data
            # Filtra só mensagens recebidas (fromMe=false) e ordena pela mais recente
            records = [m for m in records if not m.get("key", {}).get("fromMe", True)]
            records.sort(key=lambda m: m.get("messageTimestamp", 0), reverse=True)
            return records
    except Exception as e:
        logger.warning(f"_fetch_messages erro para {phone_jid}: {e}")
    return []


def _fetch_chats(instance: str, base_url: str, api_key: str, count: int = 200) -> list:
    """Lista os chats da instância para descobrir quem respondeu."""
    url = f"{base_url}/chat/findChats/{instance}"
    try:
        resp = requests.post(
            url,
            json={"where": {}, "limit": count},
            headers={"apikey": api_key},
            timeout=20,
        )
        if resp.ok:
            data = resp.json()
            if isinstance(data, list):
                return data
            if isinstance(data, dict):
                return data.get("chats", [])
    except Exception as e:
        logger.warning(f"_fetch_chats erro: {e}")
    return []


class Command(BaseCommand):
    help = "Reprocessa respostas recebidas e marca mensagens como respondidas"

    def add_arguments(self, parser):
        parser.add_argument(
            "--dias",
            type=int,
            default=60,
            help="Quantos dias atrás buscar mensagens enviadas (padrão: 60)",
        )
        parser.add_argument(
            "--limite",
            type=int,
            default=200,
            help="Máximo de chats a consultar na Evolution API (padrão: 200)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Apenas mostra o que seria atualizado, sem salvar",
        )
        parser.add_argument(
            "--refazer",
            action="store_true",
            help="Reprocessa também mensagens já marcadas como respondidas (corrige respostas erradas)",
        )

    def handle(self, *args, **options):
        dias = options["dias"]
        limite = options["limite"]
        dry_run = options["dry_run"]
        refazer = options["refazer"]

        instance = getattr(settings, "EVOLUTION_INSTANCE", "")
        base_url = getattr(settings, "EVOLUTION_BASE_URL", "").rstrip("/")
        api_key  = getattr(settings, "EVOLUTION_API_KEY", "")

        if not all([instance, base_url, api_key]):
            self.stderr.write(self.style.ERROR(
                "Configure EVOLUTION_INSTANCE, EVOLUTION_BASE_URL e EVOLUTION_API_KEY no settings."
            ))
            return

        desde = timezone.now() - timedelta(days=dias)
        self.stdout.write(f"Buscando mensagens enviadas nos últimos {dias} dias (desde {desde.strftime('%d/%m/%Y')})...")

        # Pega mensagens pendentes (ou todas se --refazer)
        qs = MensagemEnviada.objects.filter(enviada_em__gte=desde)
        if not refazer:
            qs = qs.exclude(status=MensagemEnviada.STATUS_RESPONDIDO)
        pendentes = qs.values("telefone").distinct()

        telefones_pendentes = {row["telefone"] for row in pendentes}
        self.stdout.write(f"  {len(telefones_pendentes)} números com mensagens pendentes.")

        if not telefones_pendentes:
            self.stdout.write(self.style.SUCCESS("Nada a reprocessar."))
            return

        # Busca chats da Evolution API
        self.stdout.write(f"\nBuscando chats na Evolution API (limite={limite})...")
        chats = _fetch_chats(instance, base_url, api_key, count=limite)
        self.stdout.write(f"  {len(chats)} chats encontrados.")

        if not chats:
            self.stderr.write(self.style.WARNING(
                "Nenhum chat retornado pela Evolution API. "
                "Verifique se o endpoint /chat/findChats está disponível."
            ))
            return

        marcados = 0
        verificados = 0

        for chat in chats:
            remote_jid = chat.get("remoteJid", "") or chat.get("id", "")

            # Ignora grupos
            if "@g.us" in remote_jid or "@broadcast" in remote_jid:
                continue

            # Extrai número do JID
            if "@lid" in remote_jid:
                # Para @lid, não temos o número diretamente — pula
                # (esses eram os casos que o webhook já não resolvia)
                continue

            raw_phone = remote_jid.replace("@s.whatsapp.net", "").replace("@c.us", "")
            variants = _phone_variations(raw_phone)

            # Verifica se alguma variação bate com um número pendente
            match = variants & telefones_pendentes
            if not match:
                # Tenta pelo sufixo (últimos 8 dígitos)
                sufixo = re.sub(r"\D", "", raw_phone)[-8:]
                match_sufixo = {t for t in telefones_pendentes if t.endswith(sufixo)}
                if not match_sufixo:
                    continue
                match = match_sufixo

            verificados += 1

            # Busca mensagens recebidas desse chat
            msgs_api = _fetch_messages(instance, base_url, api_key, remote_jid, count=20)
            if not msgs_api:
                continue

            # Pega o texto da resposta mais recente
            resposta_texto = ""
            for m in msgs_api:
                msg_content = m.get("message", {})
                texto = (
                    msg_content.get("conversation")
                    or msg_content.get("extendedTextMessage", {}).get("text")
                    or ""
                )
                if texto:
                    resposta_texto = texto
                    break

            if not resposta_texto:
                resposta_texto = "[mídia ou resposta sem texto]"

            # Busca as mensagens no banco para marcar
            qs_banco = MensagemEnviada.objects.filter(
                telefone__in=list(variants | match),
                enviada_em__gte=desde,
            )
            if not refazer:
                qs_banco = qs_banco.exclude(status=MensagemEnviada.STATUS_RESPONDIDO)
            msgs_banco = qs_banco.order_by("-enviada_em")[:10]

            if not msgs_banco:
                sufixo = re.sub(r"\D", "", raw_phone)[-8:]
                qs_banco2 = MensagemEnviada.objects.filter(
                    telefone__endswith=sufixo,
                    enviada_em__gte=desde,
                )
                if not refazer:
                    qs_banco2 = qs_banco2.exclude(status=MensagemEnviada.STATUS_RESPONDIDO)
                msgs_banco = qs_banco2.order_by("-enviada_em")[:10]

            if msgs_banco:
                nome_contato = msgs_banco[0].nome or raw_phone
                self.stdout.write(
                    f"  {'[DRY-RUN] ' if dry_run else ''}Marcando {len(msgs_banco)} msg(s) de {nome_contato} ({raw_phone}) → \"{resposta_texto[:60]}\""
                )
                if not dry_run:
                    for msg in msgs_banco:
                        msg.status        = MensagemEnviada.STATUS_RESPONDIDO
                        msg.respondida_em = timezone.now()
                        msg.resposta      = resposta_texto
                        msg.save()
                    marcados += len(msgs_banco)

            # Pequena pausa para não sobrecarregar a API
            time.sleep(0.3)

        self.stdout.write("")
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f"[DRY-RUN] {verificados} números verificados. Nenhuma alteração salva."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Concluído: {verificados} números verificados, {marcados} mensagem(ns) marcada(s) como respondida."
            ))
