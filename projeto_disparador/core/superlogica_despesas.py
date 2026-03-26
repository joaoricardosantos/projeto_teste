"""
Serviço de integração com Superlógica — módulo de Despesas.
Endpoint: GET /despesas/index
"""

from datetime import datetime, date
from decimal import Decimal, InvalidOperation
from typing import Optional

import requests
from django.conf import settings


def _get_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "app_token": settings.SUPERLOGICA_APP_TOKEN,
        "access_token": settings.SUPERLOGICA_ACCESS_TOKEN,
    }


def _para_decimal(valor) -> Decimal:
    if valor is None:
        return Decimal("0")
    try:
        return Decimal(str(valor).strip())
    except InvalidOperation:
        return Decimal("0")


def _formatar_data_br(valor: str) -> str:
    """Converte MM/DD/YYYY ou YYYY-MM-DD para DD/MM/YYYY."""
    if not valor:
        return ""
    for fmt in ("%m/%d/%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(valor.strip(), fmt).strftime("%d/%m/%Y")
        except ValueError:
            continue
    return valor


def _para_formato_api(data_br: str) -> str:
    """Converte DD/MM/YYYY para M/D/Y (formato esperado pela API Superlógica)."""
    try:
        return datetime.strptime(data_br.strip(), "%d/%m/%Y").strftime("%-m/%-d/%Y")
    except ValueError:
        return data_br


def buscar_despesas(
    id_condominio: int,
    dt_inicio: str,
    dt_fim: str,
    com_status: str = "todas",
    filtrar_por: str = "vencimento",
    contas: Optional[list] = None,
    pagina: int = 1,
    itens_por_pagina: int = 50,
) -> dict:
    """
    Busca despesas no Superlógica para um condomínio e período.

    Parâmetros:
        id_condominio : ID do condomínio
        dt_inicio     : Data início no formato DD/MM/YYYY
        dt_fim        : Data fim no formato DD/MM/YYYY
        com_status    : "pendentes" | "liquidadas" | "todas"
        filtrar_por   : "vencimento" | "liquidacao" | "competencia" | "criacao"
        contas        : Lista de contas (ex: ["2.1.1", "2.3.2"]) — opcional
        pagina        : Página atual
        itens_por_pagina : Itens por página (máx 50)

    Retorna dict com chaves: despesas, total, pagina, total_paginas
    """
    params = {
        "idCondominio": id_condominio,
        "comStatus": com_status,
        "dtInicio": _para_formato_api(dt_inicio),
        "dtFim": _para_formato_api(dt_fim),
        "filtrarpor": filtrar_por,
        "pagina": pagina,
        "itensPorPagina": min(itens_por_pagina, 50),
    }

    if contas:
        for i, conta in enumerate(contas):
            params[f"CONTAS[{i}]"] = conta

    response = requests.get(
        f"{settings.SUPERLOGICA_BASE_URL}/despesas",
        headers=_get_headers(),
        params=params,
        timeout=30,
    )

    if response.status_code != 200:
        raise Exception(f"Erro Superlógica ({response.status_code}): {response.text[:200]}")

    data = response.json()

    # A API retorna lista diretamente ou dict com semaphore
    if isinstance(data, list):
        itens = data
        total = len(data)
    elif isinstance(data, dict):
        itens = data.get("data", data.get("despesas", []))
        total = data.get("totalDeItens", len(itens))
    else:
        itens = []
        total = 0

    despesas = []
    for item in itens:
        valor = _para_decimal(item.get("vl_valor_pdes") or item.get("vl_valorbruto_pdes") or 0)
        valor_pago = _para_decimal(item.get("vl_valor_pdes") if item.get("fl_liquidado_pdes") == "1" else 0)

        # Descrição vem da apropriação (lista)
        apropriacao = item.get("apropriacao") or []
        descricao = apropriacao[0].get("st_descricao_cont", "").strip() if apropriacao else ""
        conta = apropriacao[0].get("st_conta_cont", "") if apropriacao else ""
        categoria = descricao  # usa descrição da conta como categoria

        despesas.append({
            "id": str(item.get("id_despesa_des", "")),
            "descricao": item.get("st_complemento_pdes", "") or descricao,
            "fornecedor": item.get("st_nome_con") or item.get("st_fantasia_con", ""),
            "conta": conta,
            "categoria": categoria,
            "valor": float(valor),
            "valor_pago": float(valor_pago),
            "vencimento": _formatar_data_br((item.get("dt_vencimento_pdes") or "")[:10]),
            "liquidacao": _formatar_data_br((item.get("dt_liquidacao_pdes") or "")[:10]),
            "competencia": _formatar_data_br((item.get("dt_despesa_des") or "")[:10]),
            "status": "liquidada" if item.get("fl_liquidado_pdes") == "1" else "pendente",
        })

    total_paginas = max(1, -(-total // itens_por_pagina))  # ceil division

    return {
        "despesas": despesas,
        "total": total,
        "pagina": pagina,
        "total_paginas": total_paginas,
    }


def buscar_todas_despesas(
    id_condominio: int,
    dt_inicio: str,
    dt_fim: str,
    com_status: str = "todas",
    filtrar_por: str = "vencimento",
    contas: Optional[list] = None,
) -> list:
    """Busca todas as páginas de despesas e retorna lista completa."""
    todas = []
    pagina = 1
    itens_por_pagina = 50

    while True:
        resultado = buscar_despesas(
            id_condominio, dt_inicio, dt_fim,
            com_status=com_status, filtrar_por=filtrar_por,
            contas=contas, pagina=pagina,
            itens_por_pagina=itens_por_pagina,
        )
        lote = resultado["despesas"]
        todas.extend(lote)

        # Para quando a página retornar menos itens que o máximo (última página)
        if len(lote) < itens_por_pagina:
            break

        pagina += 1

    return todas


def resumo_despesas(despesas: list) -> dict:
    """Calcula totais e agrupamentos a partir da lista de despesas."""
    total_geral = sum(d["valor"] for d in despesas)
    total_pago = sum(d["valor_pago"] for d in despesas)
    total_pendente = sum(d["valor"] for d in despesas if d["status"] == "pendente")
    total_liquidado = sum(d["valor"] for d in despesas if d["status"] == "liquidada")

    # Por categoria
    por_categoria: dict = {}
    for d in despesas:
        cat = d["categoria"] or d["conta"] or "Sem categoria"
        if cat not in por_categoria:
            por_categoria[cat] = {"categoria": cat, "total": 0.0, "quantidade": 0}
        por_categoria[cat]["total"] = round(por_categoria[cat]["total"] + d["valor"], 2)
        por_categoria[cat]["quantidade"] += 1

    por_categoria_lista = sorted(
        por_categoria.values(), key=lambda x: x["total"], reverse=True
    )

    # Por fornecedor (top 10)
    por_fornecedor: dict = {}
    for d in despesas:
        forn = d["fornecedor"] or "Sem fornecedor"
        por_fornecedor[forn] = round(por_fornecedor.get(forn, 0.0) + d["valor"], 2)

    por_fornecedor_lista = sorted(
        [{"fornecedor": k, "total": v} for k, v in por_fornecedor.items()],
        key=lambda x: x["total"], reverse=True,
    )[:10]

    # Por mês de vencimento
    por_mes: dict = {}
    for d in despesas:
        venc = d["vencimento"]
        if venc and len(venc) == 10:
            mes_key = venc[3:]  # MM/YYYY
        else:
            mes_key = "Sem data"
        if mes_key not in por_mes:
            por_mes[mes_key] = {"mes": mes_key, "total": 0.0, "quantidade": 0}
        por_mes[mes_key]["total"] = round(por_mes[mes_key]["total"] + d["valor"], 2)
        por_mes[mes_key]["quantidade"] += 1

    por_mes_lista = sorted(por_mes.values(), key=lambda x: x["mes"])

    return {
        "total_geral": round(total_geral, 2),
        "total_pago": round(total_pago, 2),
        "total_pendente": round(total_pendente, 2),
        "total_liquidado": round(total_liquidado, 2),
        "quantidade": len(despesas),
        "por_categoria": por_categoria_lista,
        "por_fornecedor": por_fornecedor_lista,
        "por_mes": por_mes_lista,
    }
