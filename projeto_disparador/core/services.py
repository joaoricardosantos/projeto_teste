import csv
import openpyxl
from io import StringIO
from django.conf import settings
from core.evolution_service import send_whatsapp_bulk


def _render_template(
    body: str,
    condo_name: str = "",
    unidade: str = "",
    nome: str = "",
    qtd_inadimpl: str = "",
    competencia: str = "",
    vencimento: str = "",
    valor: str = "",
) -> str:
    """
    Substitui todas as variáveis disponíveis no corpo do template.
    Variáveis:
      {{condominio}}  → nome do condomínio
      {{unidade}}     → código da unidade (ex: 315 SALA)
      {{nome}}        → nome do proprietário/sacado
      {{qtd}}         → quantidade de inadimplências em aberto
      {{competencia}} → competência da cobrança
      {{vencimento}}  → data de vencimento
      {{valor}}       → valor total devido (R$ formatado)
    """
    return (
        body
        .replace("{{condominio}}",  condo_name)
        .replace("{{unidade}}",     unidade)
        .replace("{{nome}}",        nome)
        .replace("{{qtd}}",         str(qtd_inadimpl))
        .replace("{{competencia}}", competencia)
        .replace("{{vencimento}}",  vencimento)
        .replace("{{valor}}",       valor)
    )


def _build_default_message(
    condo_name: str,
    unidade: str,
    nome: str,
    vencimento: str,
    competencia: str,
    valor: str,
    qtd: str,
) -> str:
    return (
        f"Olá{', ' + nome if nome else ''}! Identificamos débito em aberto referente à unidade "
        f"*{unidade}* do condomínio *{condo_name}*.\n"
        f"Competência: *{competencia}* | Vencimento: *{vencimento}*\n"
        f"Qtd de inadimplências: *{qtd}*\n"
        f"Valor total com encargos: *{valor}*.\n"
        f"Entre em contato para regularização."
    )


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
            message = _build_default_message(condo_name, "", "", "", "", debt_amount, "")
            contacts.append({"phone": contact, "message": message})
        else:
            error_count += 1

    result = send_whatsapp_bulk(contacts)
    result["errors"] += error_count
    result["sem_numero"] = failures_no_phone
    result["failures"] = result.get("failures", []) + [
        {"phone": "—", "error": f"{f['unidade']} ({f['nome']}): {f['motivo']}"}
        for f in failures_no_phone
    ]

    # ── Registra campanha e mensagens no banco ────────────────────────────────
    try:
        from core.models import Campanha, MensagemEnviada
        from django.utils import timezone as tz

        campanha_nome = f"Disparo {tz.now().strftime('%d/%m/%Y %H:%M')}"
        campanha = Campanha.objects.create(
            nome=campanha_nome,
            total_enviados=result.get("success", 0),
            total_erros=result.get("errors", 0),
            total_sem_numero=len(failures_no_phone),
        )
        result["campanha_id"] = str(campanha.id)
        result["campanha_nome"] = campanha_nome

        # Registra cada contato enviado
        objs = []
        import re as _re
        def _norm(p): return _re.sub(r"\D", "", p)
        for c in contacts:
            objs.append(MensagemEnviada(
                campanha=campanha,
                condominio=c.get("condominio", ""),
                unidade=c.get("unidade", ""),
                nome=c.get("nome", ""),
                telefone=_norm(c.get("phone", "")),
                mensagem=c.get("message", ""),
                status=MensagemEnviada.STATUS_ENVIADO,
            ))
        MensagemEnviada.objects.bulk_create(objs)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Erro ao salvar campanha: {e}")

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
            message = _render_template(template.body, condo_name=condo_name, nome=contact, valor=debt_amount)
            contacts.append({"phone": contact, "message": message})
        else:
            error_count += 1

    result = send_whatsapp_bulk(contacts)
    result["errors"] += error_count
    result["sem_numero"] = failures_no_phone
    result["failures"] = result.get("failures", []) + [
        {"phone": "—", "error": f"{f['unidade']} ({f['nome']}): {f['motivo']}"}
        for f in failures_no_phone
    ]

    # ── Registra campanha e mensagens no banco ────────────────────────────────
    try:
        from core.models import Campanha, MensagemEnviada
        from django.utils import timezone as tz

        campanha_nome = f"Disparo {tz.now().strftime('%d/%m/%Y %H:%M')}"
        campanha = Campanha.objects.create(
            nome=campanha_nome,
            total_enviados=result.get("success", 0),
            total_erros=result.get("errors", 0),
            total_sem_numero=len(failures_no_phone),
        )
        result["campanha_id"] = str(campanha.id)
        result["campanha_nome"] = campanha_nome

        # Registra cada contato enviado
        objs = []
        import re as _re
        def _norm(p): return _re.sub(r"\D", "", p)
        for c in contacts:
            objs.append(MensagemEnviada(
                campanha=campanha,
                condominio=c.get("condominio", ""),
                unidade=c.get("unidade", ""),
                nome=c.get("nome", ""),
                telefone=_norm(c.get("phone", "")),
                mensagem=c.get("message", ""),
                status=MensagemEnviada.STATUS_ENVIADO,
            ))
        MensagemEnviada.objects.bulk_create(objs)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Erro ao salvar campanha: {e}")

    return result


def process_excel_report_dispatch(file_obj, template_id: str = None):
    """
    Lê o Excel gerado pelo relatório (aba Resumo) e envia WhatsApp
    para Telefone 1 e Telefone 2 de cada unidade inadimplente.
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

    idx_condo       = col("Condomínio")
    idx_unidade     = col("Unidade")
    idx_nome        = col("Nome")
    idx_tel1        = col("Telefone 1")
    idx_tel2        = col("Telefone 2")
    idx_qtd         = col("Qtd Inadimpl.")
    idx_vencimento  = col("Vencimento")
    idx_competencia = col("Competência")
    idx_total       = col("Total")

    # Fallback para planilhas antigas com coluna "Telefones"
    idx_telefones_legado = col("Telefones")

    if idx_tel1 is None and idx_telefones_legado is None:
        raise ValueError("Coluna_Telefone_nao_encontrada")

    contacts = []
    error_count = 0
    failures_no_phone = []  # unidades sem número cadastrado

    for row in ws.iter_rows(min_row=2, values_only=True):
        # Pula linha de totais
        first_val = str(row[0]).strip() if row[0] else ""
        if first_val.upper() in ("TOTAL GERAL", "TOTAL"):
            continue

        condo_name  = str(row[idx_condo])      if idx_condo      is not None and row[idx_condo]      else ""
        unidade     = str(row[idx_unidade])    if idx_unidade    is not None and row[idx_unidade]    else ""
        nome        = str(row[idx_nome])       if idx_nome       is not None and row[idx_nome]       else ""
        qtd         = str(row[idx_qtd])        if idx_qtd        is not None and row[idx_qtd]        else ""
        vencimento  = str(row[idx_vencimento]) if idx_vencimento is not None and row[idx_vencimento] else ""
        competencia = str(row[idx_competencia])if idx_competencia is not None and row[idx_competencia] else ""
        total_raw   = row[idx_total]           if idx_total      is not None else None

        # Formata valor BRL
        try:
            valor_fmt = f"R$ {float(total_raw):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except (ValueError, TypeError):
            valor_fmt = str(total_raw) if total_raw else ""

        # Monta mensagem
        if template_body:
            message = _render_template(
                template_body,
                condo_name=condo_name,
                unidade=unidade,
                nome=nome,
                qtd_inadimpl=qtd,
                competencia=competencia,
                vencimento=vencimento,
                valor=valor_fmt,
            )
        else:
            message = _build_default_message(
                condo_name, unidade, nome, vencimento, competencia, valor_fmt, qtd
            )

        # Lógica de fallback: tenta tel1, se s/n tenta tel2, se ambos s/n registra sem número
        if idx_tel1 is not None:
            t1 = str(row[idx_tel1]).strip() if row[idx_tel1] else "s/n"
            t2 = str(row[idx_tel2]).strip() if idx_tel2 is not None and row[idx_tel2] else "s/n"

            if t1.lower() != "s/n":
                contacts.append({"phone": t1, "message": message,
                    "condominio": condo_name, "unidade": unidade, "nome": nome})
            elif t2.lower() != "s/n":
                contacts.append({"phone": t2, "message": message,
                    "condominio": condo_name, "unidade": unidade, "nome": nome})
            else:
                # Ambos s/n → registra como erro com informação da unidade
                error_count += 1
                failures_no_phone.append({
                    "unidade": f"{condo_name} - {unidade}",
                    "nome": nome,
                    "motivo": "Nenhum número cadastrado",
                })

        elif idx_telefones_legado is not None:
            # Formato legado com coluna "Telefones"
            raw = row[idx_telefones_legado]
            if raw:
                telefones = [t.strip() for t in str(raw).split("|") if t.strip()]
                for phone in telefones:
                    contacts.append({"phone": phone, "message": message,
                        "condominio": condo_name, "unidade": unidade, "nome": nome})
            else:
                error_count += 1
                failures_no_phone.append({
                    "unidade": f"{condo_name} - {unidade}",
                    "nome": nome,
                    "motivo": "Nenhum número cadastrado",
                })
        else:
            error_count += 1

    result = send_whatsapp_bulk(contacts)
    result["errors"] += error_count
    result["sem_numero"] = failures_no_phone
    result["failures"] = result.get("failures", []) + [
        {"phone": "—", "error": f"{f['unidade']} ({f['nome']}): {f['motivo']}"}
        for f in failures_no_phone
    ]

    # ── Registra campanha e mensagens no banco ────────────────────────────────
    try:
        from core.models import Campanha, MensagemEnviada
        from django.utils import timezone as tz

        campanha_nome = f"Disparo {tz.now().strftime('%d/%m/%Y %H:%M')}"
        campanha = Campanha.objects.create(
            nome=campanha_nome,
            total_enviados=result.get("success", 0),
            total_erros=result.get("errors", 0),
            total_sem_numero=len(failures_no_phone),
        )
        result["campanha_id"] = str(campanha.id)
        result["campanha_nome"] = campanha_nome

        # Registra cada contato enviado
        objs = []
        import re as _re
        def _norm(p): return _re.sub(r"\D", "", p)
        for c in contacts:
            objs.append(MensagemEnviada(
                campanha=campanha,
                condominio=c.get("condominio", ""),
                unidade=c.get("unidade", ""),
                nome=c.get("nome", ""),
                telefone=_norm(c.get("phone", "")),
                mensagem=c.get("message", ""),
                status=MensagemEnviada.STATUS_ENVIADO,
            ))
        MensagemEnviada.objects.bulk_create(objs)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Erro ao salvar campanha: {e}")

    return result