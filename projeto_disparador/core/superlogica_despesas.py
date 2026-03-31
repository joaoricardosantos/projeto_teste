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
        # Campos de parcela podem vir aninhados em item["parcelas"][0] ou na raiz
        parcelas = item.get("parcelas") or []
        parcela = parcelas[0] if parcelas else {}

        def _pdes(key, fallback=""):
            """Busca campo de parcela: primeiro na parcela, depois na raiz do item."""
            v = parcela.get(key)
            if v is None or v == "":
                v = item.get(key)
            return v if v is not None else fallback

        valor = _para_decimal(_pdes("vl_valor_pdes") or item.get("vl_valorbruto_pdes") or 0)
        liquidado = str(_pdes("fl_liquidado_pdes", "0")) == "1"
        valor_pago = _para_decimal(_pdes("vl_valor_pdes") if liquidado else 0)

        # Descrição vem da apropriação (lista)
        apropriacao = item.get("apropriacao") or []
        descricao = apropriacao[0].get("st_descricao_cont", "").strip() if apropriacao else ""
        conta = apropriacao[0].get("st_conta_cont", "") if apropriacao else ""
        categoria = descricao  # usa descrição da conta como categoria

        despesas.append({
            "id":           str(item.get("id_despesa_des", "")),
            "id_parcela":   str(_pdes("id_parcela_pdes", "") or ""),
            "id_contato":   str(_pdes("id_contato_con", "") or ""),
            "descricao":    _pdes("st_complemento_pdes", "") or descricao,
            "fornecedor":   item.get("st_nome_con") or item.get("st_fantasia_con", ""),
            "conta":        conta,
            "categoria":    categoria,
            "valor":        float(valor),
            "valor_pago":   float(valor_pago),
            "vencimento":   _formatar_data_br((_pdes("dt_vencimento_pdes", "") or "")[:10]),
            "liquidacao":   _formatar_data_br((_pdes("dt_liquidacao_pdes", "") or "")[:10]),
            "competencia":  _formatar_data_br((item.get("dt_despesa_des") or "")[:10]),
            "status":       "liquidada" if liquidado else "pendente",
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
    """Busca todas as páginas de despesas em paralelo e retorna lista completa."""
    from concurrent.futures import ThreadPoolExecutor, as_completed

    itens_por_pagina = 50

    # Busca a primeira página para saber o total
    primeira = buscar_despesas(
        id_condominio, dt_inicio, dt_fim,
        com_status=com_status, filtrar_por=filtrar_por,
        contas=contas, pagina=1,
        itens_por_pagina=itens_por_pagina,
    )

    todas = list(primeira["despesas"])
    total_paginas = primeira["total_paginas"]

    if total_paginas <= 1:
        return todas

    # Busca as páginas restantes em paralelo
    def _buscar_pagina(p):
        return buscar_despesas(
            id_condominio, dt_inicio, dt_fim,
            com_status=com_status, filtrar_por=filtrar_por,
            contas=contas, pagina=p,
            itens_por_pagina=itens_por_pagina,
        )["despesas"]

    with ThreadPoolExecutor(max_workers=5) as executor:
        futuros = {executor.submit(_buscar_pagina, p): p for p in range(2, total_paginas + 1)}
        resultados = {}
        for futuro in as_completed(futuros):
            resultados[futuros[futuro]] = futuro.result()

    # Mantém ordem das páginas
    for p in range(2, total_paginas + 1):
        todas.extend(resultados.get(p, []))

    return todas


def liquidar_despesa(payload: dict) -> dict:
    """
    Liquidar uma despesa no Superlógica.
    PUT /v2/condor/despesas/liquidar
    """
    headers = {
        "app_token":    settings.SUPERLOGICA_APP_TOKEN,
        "access_token": settings.SUPERLOGICA_ACCESS_TOKEN,
        "Content-Type": "application/x-www-form-urlencoded",
    }
    response = requests.put(
        f"{settings.SUPERLOGICA_BASE_URL}/despesas/liquidar",
        headers=headers,
        data=payload,
        timeout=30,
    )
    if response.status_code not in (200, 201):
        raise Exception(f"Erro Superlógica ({response.status_code}): {response.text[:300]}")
    return response.json() if response.text else {"ok": True}


def _proximos_vencimentos(dt_inicio_br: str, qt: int) -> list:
    """
    Retorna lista de datas no formato DD/MM/YYYY para `qt` parcelas,
    incrementando mês a mês a partir de dt_inicio_br (DD/MM/YYYY).
    """
    from calendar import monthrange
    try:
        d = datetime.strptime(dt_inicio_br.strip(), "%d/%m/%Y").date()
    except ValueError:
        d = datetime.today().date()

    datas = []
    dia = d.day
    mes, ano = d.month, d.year
    for _ in range(qt):
        ultimo_dia = monthrange(ano, mes)[1]
        dia_corrigido = min(dia, ultimo_dia)
        datas.append(date(ano, mes, dia_corrigido).strftime("%d/%m/%Y"))
        mes += 1
        if mes > 12:
            mes = 1
            ano += 1
    return datas


def criar_despesa_superlogica(payload: dict, qt_parcelas: int = 1) -> dict:
    """
    Criar uma despesa (parcelada ou não) no Superlógica.
    POST /v2/condor/despesas

    Estrutura correta conforme documentação:
      - Campos planos no topo: ID_CONDOMINIO_COND, ST_NOME_CON, NM_PARCELAS, etc.
      - Parcelas: DESPESA_PARCELA[i][DT_VENCIMENTO_PDES], DESPESA_PARCELA[i][VL_VALOR_PDES]
      - Complemento: RETENCOES[0][ST_COMPLEMENTO_PDES]
    """
    from urllib.parse import quote as _quote

    headers = {
        "app_token":    settings.SUPERLOGICA_APP_TOKEN,
        "access_token": settings.SUPERLOGICA_ACCESS_TOKEN,
        "Content-Type": "application/x-www-form-urlencoded",
    }

    qt = max(1, int(qt_parcelas))
    vl_total   = float(payload.get("VL_VALOR_PDES", 0))
    dt_venc_br = str(payload.get("DT_VENCIMENTO_PDES", ""))   # DD/MM/YYYY

    # Valor por parcela (última absorve diferença de centavos)
    vl_parcela = round(vl_total / qt, 2)
    vl_ultima  = round(vl_total - vl_parcela * (qt - 1), 2)
    vencimentos = _proximos_vencimentos(dt_venc_br, qt)        # lista DD/MM/YYYY

    # ── Campos planos (cabeçalho) ──────────────────────────────────────────────
    dados: dict = {
        "ID_CONDOMINIO_COND":          payload.get("ID_CONDOMINIO_COND", ""),
        "ST_NOME_CON":                 payload.get("ST_NOME_CON", ""),
        "ID_CONTATO_CON":              payload.get("ID_CONTATO_CON", ""),
        "NM_PARCELAS":                 qt,
        "DT_VENCIMENTOPRIMEIRAPARCELA": _para_formato_api(dt_venc_br),
        "ID_FORMA_PAG":                payload.get("ID_FORMA_PAG", 0),
        "ID_CONTABANCO_CB":            payload.get("ID_CONTABANCO_CB", 0),
    }

    # Observação geral
    if payload.get("ST_OBS_DES"):
        dados["ST_OBS_DES"] = payload["ST_OBS_DES"]

    # ── Complemento / descrição via RETENCOES ──────────────────────────────────
    dados["RETENCOES[0][ST_COMPLEMENTO_PDES]"] = payload.get("ST_COMPLEMENTO_PDES", "")

    # ── Parcelas ───────────────────────────────────────────────────────────────
    nome_fav = payload.get("ST_NOME_CON", "")
    id_fav   = payload.get("ID_CONTATO_CON", "")

    for i, dt_br in enumerate(vencimentos):
        vl = vl_ultima if i == qt - 1 else vl_parcela
        dados[f"DESPESA_PARCELA[{i}][DT_VENCIMENTO_PDES]"]    = _para_formato_api(dt_br)
        dados[f"DESPESA_PARCELA[{i}][VL_VALOR_PDES]"]         = vl
        dados[f"DESPESA_PARCELA[{i}][ST_NOMERECEBEDOR_FAV]"]  = nome_fav
        dados[f"DESPESA_PARCELA[{i}][ID_FAVORECIDO_CON]"]     = id_fav

    # ── Liquidação da 1ª parcela (opcional) ───────────────────────────────────
    if payload.get("FL_LIQUIDADO_PDES"):
        dados["DT_LIQUIDACAO_PDES"] = _para_formato_api(
            payload.get("DT_LIQUIDACAO_PDES", dt_venc_br)
        )
        dados["VL_PAGO"] = payload.get("VL_PAGO", vl_total)

    # ── Envio: colchetes nas chaves devem ser literais, não %5B%5D ─────────────
    body = "&".join(f"{k}={_quote(str(v), safe='')}" for k, v in dados.items())

    response = requests.post(
        f"{settings.SUPERLOGICA_BASE_URL}/despesas",
        headers=headers,
        data=body,
        timeout=30,
    )

    # Superlógica retorna 206 com JSON de erro em alguns casos
    result = response.json() if response.text else {"ok": True}
    if isinstance(result, list) and result and str(result[0].get("status")) == "500":
        raise Exception(f"Erro Superlógica (206): {response.text[:400]}")
    if response.status_code not in (200, 201, 206):
        raise Exception(f"Erro Superlógica ({response.status_code}): {response.text[:300]}")
    return result


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
