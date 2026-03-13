import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from io import BytesIO
from typing import Optional

import requests
from django.conf import settings
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side


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
    # Retry até 3 vezes em caso de erro temporário
    for tentativa in range(3):
        try:
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
            if response.status_code == 200:
                break
            if tentativa < 2:
                time.sleep(1)
        except requests.RequestException:
            if tentativa < 2:
                time.sleep(1)
            else:
                return None, None
    else:
        return None, None

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


# Número de threads paralelas por condomínio.
# 8 é um bom equilíbrio: rápido sem sobrecarregar a API Superlógica.
_MAX_WORKERS_UNIDADES = 12
# Número de condomínios processados em paralelo.
_MAX_WORKERS_CONDOMINIOS = 6


def buscar_inadimplentes_condominio(id_condominio: int, data_posicao: str, mapa_unidades: dict):
    """
    Estratégia em 2 etapas com paralelismo:
    1. /index  → descobre quais unidades são inadimplentes (rápido)
    2. /avancada por unidade → busca valores exatos em paralelo (rápido + preciso)
    """
    unidades_ids = _descobrir_unidades_inadimplentes(id_condominio, data_posicao)
    if not unidades_ids:
        return {}, []

    resumo_total    = {}
    detalhado_total = []

    # Busca todos os valores em paralelo com pool de threads
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS_UNIDADES) as executor:
        futures = {
            executor.submit(_buscar_valores_unidade, id_condominio, id_uni, mapa_unidades): id_uni
            for id_uni in unidades_ids
        }
        for future in as_completed(futures):
            id_uni = futures[future]
            try:
                resumo_uni, det_uni = future.result()
                if resumo_uni:
                    resumo_total[id_uni] = resumo_uni
                if det_uni:
                    detalhado_total.extend(det_uni)
            except Exception:
                pass  # unidade com erro é ignorada silenciosamente

    return resumo_total, detalhado_total


# Borda fina para grade
_BORDA = Border(
    left=Side(style="thin", color="CCCCCC"),
    right=Side(style="thin", color="CCCCCC"),
    top=Side(style="thin", color="CCCCCC"),
    bottom=Side(style="thin", color="CCCCCC"),
)
_FILL_PAR   = PatternFill(start_color="F2F2F2", end_color="F2F2F2", fill_type="solid")  # cinza claro
_FILL_IMPAR = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")  # branco


# Larguras fixas por nome de coluna (caracteres)
_LARGURAS_FIXAS = {
    "Condomínio":  55,
    "Unidade":     18,
    "Nome":        45,
    "Telefone 1":  22,
    "Telefone 2":  22,
    "Vencimento":  16,
    "Competência": 16,
    "Principal":   16,
    "Juros":       16,
    "Multa":       12,
    "Atualização": 16,
    "Honorários":  16,
    "Total":       16,
    "Código":      14,
}


def _ajustar_larguras(ws):
    """Aplica larguras fixas por coluna e altura padrão nas linhas."""
    # Lê cabeçalhos da linha 1
    headers = [ws.cell(row=1, column=col_idx).value for col_idx in range(1, ws.max_column + 1)]
    for idx, header in enumerate(headers, start=1):
        col_letter = ws.cell(row=1, column=idx).column_letter
        largura = _LARGURAS_FIXAS.get(header, 20)
        ws.column_dimensions[col_letter].width = largura
    for row in ws.iter_rows():
        ws.row_dimensions[row[0].row].height = 30


def _aplicar_grade_e_zebra(ws):
    """Aplica borda em todas as células e alterna cores por linha (zebra)."""
    max_row = ws.max_row
    max_col = ws.max_column
    for row_idx in range(2, max_row + 1):  # pula cabeçalho (linha 1)
        fill = _FILL_PAR if row_idx % 2 == 0 else _FILL_IMPAR
        for col_idx in range(1, max_col + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.border = _BORDA
            cell.alignment = Alignment(vertical="center", wrap_text=False)
            # Ativa quebra de texto nas colunas de texto longas (col 1=Condomínio, col 3=Nome)
            if col_idx in (1, 3):
                cell.alignment = Alignment(vertical="center", wrap_text=True)
            # Não sobrescreve a cor da linha de totais (última linha)
            if row_idx < max_row:
                cell.fill = fill
    # Borda também no cabeçalho
    for cell in ws[1]:
        cell.border = _BORDA


def _estilizar_cabecalho(ws):
    header_fill = PatternFill(start_color="006837", end_color="006837", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")


def _aplicar_formato_contabil(ws, headers):
    """Aplica formato contábil R$ nas colunas numéricas."""
    cols_numericas = {"Principal", "Juros", "Multa", "Atualização", "Honorários", "Total"}
    fmt = r'R$ #,##0.00'
    for col_idx, header in enumerate(headers, start=1):
        if header in cols_numericas:
            for row_idx in range(2, ws.max_row + 1):
                cell = ws.cell(row=row_idx, column=col_idx)
                if isinstance(cell.value, (int, float)):
                    cell.number_format = fmt


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

    def _processar_condominio(condo_id):
        """Processa um condomínio completo e retorna (linhas_resumo, linhas_detalhado)."""
        acesso, nome_condominio = verificar_condominio(condo_id)
        if not acesso:
            return [], []
        mapa_unidades = buscar_unidades(condo_id)
        if not mapa_unidades:
            return [], []
        resumo, detalhado = buscar_inadimplentes_condominio(condo_id, data_posicao, mapa_unidades)
        if not resumo:
            return [], []

        linhas_resumo = []
        for unidade_id, valores in resumo.items():
            telefones = valores.get("telefones", [])
            dados_uni = mapa_unidades.get(unidade_id, {})
            tel1 = telefones[0] if len(telefones) > 0 else "s/n"
            tel2 = telefones[1] if len(telefones) > 1 else "s/n"
            linhas_resumo.append({
                "Condomínio":  nome_condominio,
                "Unidade":     dados_uni.get("unidade") or valores["nome_pdf"],
                "Nome":        dados_uni.get("sacado", ""),
                "Telefone 1":  tel1,
                "Telefone 2":  tel2,
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

        return linhas_resumo, detalhado

    # Processa condomínios em paralelo
    with ThreadPoolExecutor(max_workers=_MAX_WORKERS_CONDOMINIOS) as executor:
        futures = {executor.submit(_processar_condominio, cid): cid for cid in ids_range}
        for future in as_completed(futures):
            try:
                linhas_r, linhas_d = future.result()
                todas_resumo.extend(linhas_r)
                todo_detalhado.extend(linhas_d)
            except Exception:
                pass

    if not todas_resumo:
        return None, None

    todas_resumo.sort(key=lambda r: (r["Condomínio"] or "", r["Unidade"] or ""))
    todo_detalhado.sort(key=lambda r: (r["Condomínio"] or "", r["Unidade"] or ""))

    wb = Workbook()

    # ── Aba Resumo ──────────────────────────────────────────────────────────
    ws_resumo = wb.active
    ws_resumo.title = "Resumo"
    headers_resumo = ["Condomínio", "Unidade", "Nome", "Telefone 1", "Telefone 2", "Vencimento", "Competência",
                      "Principal", "Juros", "Multa", "Atualização", "Honorários", "Total"]
    ws_resumo.append(headers_resumo)
    for row in todas_resumo:
        ws_resumo.append([row[h] for h in headers_resumo])

    # Linha de totais
    num_rows = len(todas_resumo)
    totais_resumo = ["TOTAL GERAL", "", "", "", "", "", ""]
    cols_num = ["Principal", "Juros", "Multa", "Atualização", "Honorários", "Total"]
    for col in cols_num:
        totais_resumo.append(round(sum(r[col] for r in todas_resumo), 2))
    ws_resumo.append(totais_resumo)

    # Estilo da linha de totais
    total_row_idx = num_rows + 2
    total_fill = PatternFill(start_color="004225", end_color="004225", fill_type="solid")
    total_font = Font(color="FFFFFF", bold=True)
    for cell in ws_resumo[total_row_idx]:
        cell.fill = total_fill
        cell.font = total_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    _estilizar_cabecalho(ws_resumo)
    _ajustar_larguras(ws_resumo)
    _aplicar_grade_e_zebra(ws_resumo)
    _aplicar_formato_contabil(ws_resumo, headers_resumo)

    # ── Aba Detalhado ────────────────────────────────────────────────────────
    ws_det = wb.create_sheet("Detalhado")
    headers_det = ["Condomínio", "Unidade", "Código", "Vencimento", "Competência",
                   "Principal", "Juros", "Multa", "Atualização", "Honorários", "Total"]
    ws_det.append(headers_det)
    for row in todo_detalhado:
        ws_det.append([row.get(h, "") for h in headers_det])

    # Linha de totais detalhado
    num_rows_det = len(todo_detalhado)
    totais_det = ["TOTAL GERAL", "", "", "", ""]
    cols_num_det = ["Principal", "Juros", "Multa", "Atualização", "Honorários", "Total"]
    for col in cols_num_det:
        totais_det.append(round(sum(r.get(col, 0) for r in todo_detalhado), 2))
    ws_det.append(totais_det)

    total_row_det = num_rows_det + 2
    for cell in ws_det[total_row_det]:
        cell.fill = total_fill
        cell.font = total_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    _estilizar_cabecalho(ws_det)
    _ajustar_larguras(ws_det)
    _aplicar_grade_e_zebra(ws_det)
    _aplicar_formato_contabil(ws_det, headers_det)

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    suffix = f"_condo{id_condominio}" if id_condominio else "_todos"
    filename = f"inadimplentes{suffix}_{timestamp}.xlsx"

    return buffer.getvalue(), filename