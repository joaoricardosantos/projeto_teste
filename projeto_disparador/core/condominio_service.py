"""
condominio_service.py
Busca inadimplentes de um condomínio direto na Superlógica e envia
mensagens WhatsApp via Evolution API — sem necessidade de planilha.
"""
from datetime import datetime
from typing import Optional, List

from core.superlogica import (
    verificar_condominio,
    buscar_unidades,
    buscar_inadimplentes_condominio,
)
from core.evolution_service import send_whatsapp_bulk


def _render_template(body, condo_name="", unidade="", nome="", qtd_inadimpl="", competencia="", vencimento="", valor=""):
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


def _build_default_message(condo_name, unidade, nome, vencimento, competencia, valor, qtd):
    return (
        f"Olá{', ' + nome if nome else ''}! Identificamos débito em aberto referente à unidade "
        f"*{unidade}* do condomínio *{condo_name}*.\n"
        f"Competência: *{competencia}* | Vencimento: *{vencimento}*\n"
        f"Qtd de inadimplências: *{qtd}*\n"
        f"Valor total com encargos: *{valor}*.\n"
        f"Entre em contato para regularização."
    )


def _agregar_resultado(raw, extra_errors=0, failures_no_phone=None, contacts=None):
    if failures_no_phone is None:
        failures_no_phone = []
    # Mapa phone -> unidade/nome para enriquecer falhas
    phone_map = {}
    if contacts:
        for c in contacts:
            phone_map[c.get("phone", "")] = {"unidade": c.get("unidade", ""), "nome": c.get("nome", "")}
    if isinstance(raw, list):
        success  = sum(1 for r in raw if r.get("status") == "success")
        failures = [
            {
                "phone":   r.get("phone", ""),
                "error":   r.get("error", "Erro desconhecido"),
                "unidade": phone_map.get(r.get("phone", ""), {}).get("unidade", ""),
                "nome":    phone_map.get(r.get("phone", ""), {}).get("nome", ""),
            }
            for r in raw if r.get("status") != "success"
        ]
        errors = len(failures)
        result = {"success": success, "errors": errors + extra_errors, "failures": failures}
    elif isinstance(raw, dict):
        result = raw
        result["errors"] = result.get("errors", 0) + extra_errors
        result.setdefault("failures", [])
    else:
        result = {"success": 0, "errors": extra_errors, "failures": []}
    result["sem_numero"] = failures_no_phone
    result["failures"] = result.get("failures", []) + [
        {"phone": "—", "error": f"{f['unidade']} ({f['nome']}): {f['motivo']}"}
        for f in failures_no_phone
    ]
    return result


def _registrar_campanha(contacts, result, failures_no_phone):
    try:
        from core.models import Campanha, MensagemEnviada
        import re as _re
        campanha_nome = "Novo disparo"
        campanha = Campanha.objects.create(
            nome=campanha_nome,
            total_enviados=result.get("success", 0),
            total_erros=result.get("errors", 0),
            total_sem_numero=len(failures_no_phone),
        )
        result["campanha_id"]   = str(campanha.id)
        result["campanha_nome"] = campanha_nome
        def _norm(p): return _re.sub(r"\D", "", p.split(";")[0].split(",")[0].strip())
        objs = [
            MensagemEnviada(
                campanha=campanha,
                condominio=c.get("condominio", ""),
                unidade=c.get("unidade", ""),
                nome=c.get("nome", ""),
                telefone=_norm(c.get("phone", "")),
                mensagem=c.get("message", ""),
                status=MensagemEnviada.STATUS_ENVIADO,
            )
            for c in contacts
        ]
        MensagemEnviada.objects.bulk_create(objs)
    except Exception as e:
        import logging
        logging.getLogger(__name__).error(f"Erro ao salvar campanha: {e}")


def get_unidades_inadimplentes(id_condominio: int) -> list:
    """
    Retorna lista de unidades inadimplentes do condomínio
    sem enviar mensagens — usado para seleção na UI.
    """
    acesso, nome_condominio = verificar_condominio(id_condominio)
    if not acesso:
        raise ValueError(f"Condomínio {id_condominio} não encontrado.")

    data_posicao  = datetime.today().strftime("%m/%d/%Y")
    mapa_unidades = buscar_unidades(id_condominio)
    if not mapa_unidades:
        return []

    resumo_inadimplentes, detalhado = buscar_inadimplentes_condominio(
        id_condominio, data_posicao, mapa_unidades
    )
    if not resumo_inadimplentes:
        return []

    # Conta inadimplências por unidade a partir do detalhado
    contagem = {}
    for row in (detalhado or []):
        uid = row.get("id_unidade")
        if uid:
            contagem[uid] = contagem.get(uid, 0) + 1

    unidades = []
    for id_unidade, resumo in resumo_inadimplentes.items():
        dados_uni = mapa_unidades.get(id_unidade, {})
        unidade   = dados_uni.get("unidade", "") or resumo.get("nome_pdf", "").split(" - ")[0].strip()
        nome      = dados_uni.get("sacado", "") or resumo.get("nome_pdf", "").split(" - ")[-1].strip()
        telefones = resumo.get("telefones", [])
        total     = resumo.get("total", 0)
        try:
            valor_fmt = f"R$ {float(total):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            valor_fmt = str(total)

        telefone_principal = next((t for t in telefones if t and t.strip()), "")
        unidades.append({
            "id_unidade":         id_unidade,
            "bloco":              dados_uni.get("bloco", ""),
            "unidade":            unidade,
            "nome":               nome,
            "valor":              valor_fmt,
            "tem_numero":         bool(telefones),
            "vencimento":         resumo.get("vencimento", ""),
            "qtd_inadimplencias": contagem.get(id_unidade, 1),
            "telefone":           telefone_principal,
        })

    unidades.sort(key=lambda x: x["unidade"])
    return unidades


def send_messages_by_condominio(
    id_condominio: int,
    template_id: Optional[str] = None,
    unidades_ids: Optional[List[str]] = None,
) -> dict:
    """
    Fluxo principal:
    1. Valida condomínio na Superlógica
    2. Busca unidades e inadimplentes
    3. Filtra por unidades selecionadas (se fornecido)
    4. Para cada unidade inadimplente, monta e envia mensagem WhatsApp
    5. Retorna resumo no mesmo formato dos outros serviços
    """
    # 1. Valida condomínio
    acesso, nome_condominio = verificar_condominio(id_condominio)
    if not acesso:
        raise ValueError(f"Condomínio {id_condominio} não encontrado na Superlógica.")

    # 2. Busca template se fornecido
    template_body = None
    if template_id:
        from core.models import MessageTemplate
        try:
            tmpl = MessageTemplate.objects.get(id=int(template_id), is_active=True)
            template_body = tmpl.body
        except MessageTemplate.DoesNotExist:
            raise ValueError(f"Template {template_id} não encontrado ou inativo.")

    # 3. Busca unidades e inadimplentes
    data_posicao  = datetime.today().strftime("%m/%d/%Y")
    mapa_unidades = buscar_unidades(id_condominio)
    if not mapa_unidades:
        raise ValueError("Nenhuma unidade encontrada para este condomínio.")

    resumo_inadimplentes, _ = buscar_inadimplentes_condominio(
        id_condominio, data_posicao, mapa_unidades
    )

    if not resumo_inadimplentes:
        return {
            "success": 0, "errors": 0, "failures": [],
            "sem_numero": [], "total_processados": 0,
        }

    # 4. Filtra por unidades selecionadas (se fornecido)
    if unidades_ids:
        resumo_inadimplentes = {
            k: v for k, v in resumo_inadimplentes.items()
            if str(k) in [str(u) for u in unidades_ids]
        }

    # 5. Monta lista de contatos para envio
    contacts          = []
    failures_no_phone = []

    for id_unidade, resumo in resumo_inadimplentes.items():
        telefones  = resumo.get("telefones", [])
        dados_uni  = mapa_unidades.get(id_unidade, {})
        unidade    = dados_uni.get("unidade", "") or resumo.get("nome_pdf", "").split(" - ")[0].strip()
        nome       = dados_uni.get("sacado", "") or resumo.get("nome_pdf", "").split(" - ")[-1].strip()
        condo_name = nome_condominio or str(id_condominio)

        total = resumo.get("total", 0)
        try:
            valor_fmt = f"R$ {float(total):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
        except Exception:
            valor_fmt = str(total)

        qtd         = "1"
        vencimento  = resumo.get("vencimento", "")
        competencia = resumo.get("competencia", "")

        if template_body:
            mensagem = _render_template(
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
            mensagem = _build_default_message(
                condo_name, unidade, nome, vencimento, competencia, valor_fmt, qtd
            )

        telefone = next((t for t in telefones if t and t.strip()), None)

        if not telefone:
            failures_no_phone.append({
                "unidade": unidade, "nome": nome, "motivo": "Sem número cadastrado",
            })
            continue

        contacts.append({
            "phone":      telefone,
            "message":    mensagem,
            "condominio": condo_name,
            "unidade":    unidade,
            "nome":       nome,
        })

    raw    = send_whatsapp_bulk(contacts)
    result = _agregar_resultado(raw, extra_errors=0, failures_no_phone=failures_no_phone, contacts=contacts)
    result["total_processados"] = len(resumo_inadimplentes)
    _registrar_campanha(contacts, result, failures_no_phone)
    return result