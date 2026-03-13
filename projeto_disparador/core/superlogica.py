import time
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from io import BytesIO
from typing import Optional

import requests
from django.conf import settings
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment


def _get_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "app_token": settings.SUPERLOGICA_APP_TOKEN,
        "access_token": settings.SUPERLOGICA_ACCESS_TOKEN,
    }


def verificar_condominio(id_condominio: int):
    response = requests.get(
        f"{settings.SUPERLOGICA_BASE_URL}/unidades",
        headers=_get_headers(),
        params={"idCondominio": id_condominio, "pagina": 1, "itensPorPagina": 1},
        timeout=20,
    )
    if response.status_code != 200:
        return False, None
    dados = response.json()
    nome_condominio = None
    if dados and isinstance(dados, list):
        nome_condominio = dados[0].get("st_nome_cond")
    return True, nome_condominio


def buscar_unidades(id_condominio: int):
    mapa = {}
    pagina = 1
    while True:
        response = requests.get(
            f"{settings.SUPERLOGICA_BASE_URL}/unidades",
            headers=_get_headers(),
            params={"idCondominio": id_condominio, "pagina": pagina, "itensPorPagina": 50},
            timeout=30,
        )
        if response.status_code != 200:
            return None
        dados = response.json()
        if not dados:
            break
        for unidade in dados:
            unidade_id = unidade.get("id_unidade_uni")
            codigo_unidade = (unidade.get("st_unidade_uni") or "").strip()
            sacado = (
                unidade.get("st_sacado_uni") or unidade.get("nome_proprietario") or ""
            ).strip()
            nome_pdf = f"{codigo_unidade} - {sacado}".strip(" -")
            telefones = []
            for campo in ["telefone_proprietario", "celular_proprietario"]:
                numero = unidade.get(campo)
                if numero and str(numero).strip():
                    telefones.append(str(numero).strip())
            mapa[unidade_id] = {
                "unidade": codigo_unidade,
                "sacado": sacado,
                "nome_pdf": nome_pdf,
                "telefones": list(dict.fromkeys(telefones)),
            }
        pagina += 1
    return mapa


def _formatar_data(valor) -> str:
    if not valor:
        return ""
    texto = str(valor).strip()
    if len(texto) >= 10 and texto[2] == "/" and texto[5] == "/":
        return texto[:10]
    if len(texto) >= 10 and texto[4] == "-" and texto[7] == "-":
        partes = texto[:10].split("-")
        return f"{partes[2]}/{partes[1]}/{partes[0]}"
    return texto


def _para_decimal(valor) -> Decimal:
    if valor in (None, "", "null"):
        return Decimal("0")
    texto = str(valor).strip()
    try:
        return Decimal(texto)
    except InvalidOperation:
        pass
    try:
        return Decimal(texto.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return Decimal("0")


def _d2f(valor: Decimal) -> float:
    return float(valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def _descobrir_unidades_inadimplentes(id_condominio: int, data_posicao: str) -> set:
    """
    Usa /index (rápido) para descobrir quais unidades têm inadimplência.
    Retorna um set de id_unidade_uni.
    """
    unidades = set()
    pagina = 1
    processados = set()

    while True:
        response = requests.get(
            f"{settings.SUPERLOGICA_BASE_URL}/inadimplencia/index",
            headers=_get_headers(),
            params={
                "idCondominio":      id_condominio,
                "pagina":            pagina,
                "itensPorPagina":    50,
                "posicaoEm":         data_posicao,
                "comValoresAtualizados": 1,
            },
            timeout=30,
        )
        if response.status_code != 200:
            break
        dados = response.json()
        if not dados:
            break
        for item in dados:
            if not isinstance(item, dict):
                continue
            for receb in item.get("recebimento", []):
                if not isinstance(receb, dict):
                    continue
                if receb.get("fl_status_recb") != "0":
                    continue
                id_r = receb.get("id_recebimento_recb")
                if id_r in processados:
                    continue
                processados.add(id_r)
                unidades.add(receb.get("id_unidade_uni"))
        pagina += 1

    return unidades


def _buscar_valores_unidade(id_condominio: int, id_unidade: str, mapa_unidades: dict):
    """
    Usa /avancada filtrando por unidade para obter valores exatos
    com índice de correção monetária atualizado.
    """
    response = requests.get(
        f"{settings.SUPERLOGICA_BASE_URL}/inadimplencia/avancada",
        headers=_get_headers(),
        params={
            "idCondominio":           id_condominio,
            "idUnidades":             id_unidade,
            "itensPorPagina":         500,
            "comEncargos":            "true",
            "comHonorarios":          "true",
            "comAtualizacaoMonetaria": "true",
        },
        timeout=60,
    )

    if response.status_code != 200:
        return None, None

    dados = response.json()
    if not dados:
        return None, None

    dados_unidade = mapa_unidades.get(id_unidade, {})
    nome_pdf  = dados_unidade.get("nome_pdf", f"Unidade {id_unidade}")
    telefones = dados_unidade.get("telefones", [])

    resumo = {
        "nome_pdf":    nome_pdf,
        "telefones":   telefones,
        "vencimento":  "",
        "competencia": "",
        "principal":   Decimal("0"),
        "juros":       Decimal("0"),
        "multa":       Decimal("0"),
        "atualizacao": Decimal("0"),
        "honorarios":  Decimal("0"),
        "total":       Decimal("0"),
    }
    detalhado = []

    for receb in dados:
        if not isinstance(receb, dict):
            continue

        vencimento  = receb.get("dt_vencimento_recb", "")
        competencia = receb.get("dt_competencia_recb", "")
        id_receb    = receb.get("id_recebimento_recb")

        if not resumo["vencimento"]:
            resumo["vencimento"]  = _formatar_data(vencimento)
            resumo["competencia"] = _formatar_data(competencia)

        det = receb.get("detalhes", {}) or {}
        p = _para_decimal(receb.get("total_receita") or receb.get("vl_emitido_recb") or 0)
        j = _para_decimal(det.get("juros",      0))
        m = _para_decimal(det.get("multa",      0))
        h = _para_decimal(det.get("honorarios", 0))
        a = _para_decimal(det.get("atualizacaomonetaria") or det.get("atualizacao") or 0)
        total_receb = p + j + m + a + h

        resumo["principal"]   += p
        resumo["juros"]       += j
        resumo["multa"]       += m
        resumo["atualizacao"] += a
        resumo["honorarios"]  += h
        resumo["total"]       += total_receb

        detalhado.append({
            "Condomínio":  None,
            "Unidade":     nome_pdf,
            "Código":      id_receb,
            "Vencimento":  _formatar_data(vencimento),
            "Competência": _formatar_data(competencia),
            "Principal":   _d2f(p),
            "Juros":       _d2f(j),
            "Multa":       _d2f(m),
            "Atualização": _d2f(a),
            "Honorários":  _d2f(h),
            "Total":       _d2f(total_receb),
        })

    # Converte resumo para float
    for campo in ("principal", "juros", "multa", "atualizacao", "honorarios", "total"):
        resumo[campo] = _d2f(resumo[campo])

    return resumo, detalhado


def buscar_inadimplentes_condominio(id_condominio: int, data_posicao: str, mapa_unidades: dict):
    """
    Estratégia em 2 etapas:
    1. /index  → descobre quais unidades são inadimplentes (rápido)
    2. /avancada por unidade → busca valores exatos com índice atualizado (preciso)
    """
    unidades_ids = _descobrir_unidades_inadimplentes(id_condominio, data_posicao)
    if not unidades_ids:
        return {}, []

    resumo_total = {}
    detalhado_total = []

    for id_unidade in unidades_ids:
        resumo_uni, det_uni = _buscar_valores_unidade(id_condominio, id_unidade, mapa_unidades)
        if resumo_uni:
            resumo_total[id_unidade] = resumo_uni
        if det_uni:
            detalhado_total.extend(det_uni)
        time.sleep(0.1)  # pausa pequena para não sobrecarregar a API

    return resumo_total, detalhado_total


def _estilizar_cabecalho(ws):
    header_fill = PatternFill(start_color="006837", end_color="006837", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")


def gerar_relatorio_inadimplentes(
    id_condominio: Optional[int] = None,
    data_posicao: Optional[str] = None,
) -> tuple:
    if not data_posicao:
        data_posicao = datetime.today().strftime("%m/%d/%Y")
    else:
        partes = data_posicao.split("/")
        if len(partes) == 3:
            data_posicao = f"{partes[1]}/{partes[0]}/{partes[2]}"

    ids_range = [id_condominio] if id_condominio else range(1, getattr(settings, "SUPERLOGICA_MAX_ID", 100) + 1)

    todas_resumo = []
    todo_detalhado = []

    for condo_id in ids_range:
        acesso, nome_condominio = verificar_condominio(condo_id)
        if not acesso:
            continue
        mapa_unidades = buscar_unidades(condo_id)
        if not mapa_unidades:
            continue
        resumo, detalhado = buscar_inadimplentes_condominio(condo_id, data_posicao, mapa_unidades)
        if not resumo:
            continue

        for unidade_id, valores in resumo.items():
            telefones = valores.get("telefones", [])
            todas_resumo.append({
                "Condomínio":  nome_condominio,
                "Unidade":     valores["nome_pdf"],
                "Telefones":   " | ".join(telefones) if telefones else "",
                "Vencimento":  valores.get("vencimento", ""),
                "Competência": valores.get("competencia", ""),
                "Principal":   valores["principal"],
                "Juros":       valores["juros"],
                "Multa":       valores["multa"],
                "Atualização": valores["atualizacao"],
                "Honorários":  valores["honorarios"],
                "Total":       valores["total"],
            })

        for row in detalhado:
            row["Condomínio"] = nome_condominio
            todo_detalhado.append(row)

        if len(list(ids_range)) > 1:
            time.sleep(0.3)

    if not todas_resumo:
        return None, None

    todas_resumo.sort(key=lambda r: (r["Condomínio"] or "", r["Unidade"] or ""))
    todo_detalhado.sort(key=lambda r: (r["Condomínio"] or "", r["Unidade"] or ""))

    wb = Workbook()

    ws_resumo = wb.active
    ws_resumo.title = "Resumo"
    headers_resumo = ["Condomínio", "Unidade", "Telefones", "Vencimento", "Competência",
                      "Principal", "Juros", "Multa", "Atualização", "Honorários", "Total"]
    ws_resumo.append(headers_resumo)
    for row in todas_resumo:
        ws_resumo.append([row[h] for h in headers_resumo])
    _estilizar_cabecalho(ws_resumo)

    ws_det = wb.create_sheet("Detalhado")
    headers_det = ["Condomínio", "Unidade", "Código", "Vencimento", "Competência",
                   "Principal", "Juros", "Multa", "Atualização", "Honorários", "Total"]
    ws_det.append(headers_det)
    for row in todo_detalhado:
        ws_det.append([row.get(h, "") for h in headers_det])
    _estilizar_cabecalho(ws_det)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_condo{id_condominio}" if id_condominio else "_todos"
    filename = f"inadimplentes{suffix}_{timestamp}.xlsx"

    return buffer.getvalue(), filename