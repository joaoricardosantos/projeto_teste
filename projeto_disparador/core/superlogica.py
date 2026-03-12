import time
from datetime import datetime
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
        params={
            "idCondominio": id_condominio,
            "pagina": 1,
            "itensPorPagina": 1,
        },
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
            params={
                "idCondominio": id_condominio,
                "pagina": pagina,
                "itensPorPagina": 50,
            },
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
                unidade.get("st_sacado_uni")
                or unidade.get("nome_proprietario")
                or ""
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
    """
    Formata datas retornadas pela Superlógica para DD/MM/YYYY.
    Aceita: 'DD/MM/YYYY HH:MM:SS', 'DD/MM/YYYY', 'YYYY-MM-DD', etc.
    """
    if not valor:
        return ""
    texto = str(valor).strip()

    # Formato DD/MM/YYYY HH:MM:SS (padrão da Superlógica)
    if len(texto) >= 10 and texto[2] == "/" and texto[5] == "/":
        return texto[:10]

    # Formato YYYY-MM-DD (ISO)
    if len(texto) >= 10 and texto[4] == "-" and texto[7] == "-":
        partes = texto[:10].split("-")
        return f"{partes[2]}/{partes[1]}/{partes[0]}"

    return texto


def _para_float(valor) -> float:
    if valor in (None, "", "null"):
        return 0.0
    texto = str(valor).strip()
    try:
        return float(texto)
    except ValueError:
        pass
    try:
        return float(texto.replace(".", "").replace(",", "."))
    except ValueError:
        return 0.0


def extrair_componentes(receb: dict) -> dict:
    """
    Extrai principal, juros, multa, atualização e honorários de um recebimento.
    """
    principal = _para_float(receb.get("vl_emitido_recb") or 0)

    juros = multa = atualizacao = honorarios = 0.0

    encargos = receb.get("encargos", [])
    if encargos and isinstance(encargos, list):
        detalhes = encargos[0].get("detalhes", {})
        if isinstance(detalhes, dict):
            juros       = _para_float(detalhes.get("juros",       0))
            multa       = _para_float(detalhes.get("multa",       0))
            atualizacao = _para_float(detalhes.get("atualizacao", 0))
            honorarios  = _para_float(detalhes.get("honorarios",  0))

    total = round(principal + juros + multa + atualizacao + honorarios, 2)

    return {
        "principal":   round(principal,   2),
        "juros":       round(juros,       2),
        "multa":       round(multa,       2),
        "atualizacao": round(atualizacao, 2),
        "honorarios":  round(honorarios,  2),
        "total":       total,
    }


def buscar_inadimplentes_condominio(id_condominio: int, data_posicao: str, mapa_unidades: dict):
    """Busca inadimplentes de um condomínio específico, retorna resumo e detalhado."""
    resumo = {}
    detalhado = []
    processados = set()
    pagina = 1

    while True:
        response = requests.get(
            f"{settings.SUPERLOGICA_BASE_URL}/inadimplencia/index",
            headers=_get_headers(),
            params={
                "idCondominio":                       id_condominio,
                "pagina":                             pagina,
                "itensPorPagina":                     50,
                "posicaoEm":                          data_posicao,
                "comValoresAtualizados":              1,
                "comValoresAtualizadosPorComposicao": 1,
            },
            timeout=30,
        )

        if response.status_code != 200:
            return None, None

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

                id_receb = receb.get("id_recebimento_recb")
                if id_receb in processados:
                    continue
                processados.add(id_receb)

                unidade_id  = receb.get("id_unidade_uni")
                vencimento  = receb.get("dt_vencimento_recb")
                competencia = receb.get("dt_competencia_recb")

                dados_unidade = mapa_unidades.get(unidade_id, {})
                nome_pdf      = dados_unidade.get("nome_pdf", f"Unidade {unidade_id}")
                telefones     = dados_unidade.get("telefones", [])

                valores = extrair_componentes(receb)

                if unidade_id not in resumo:
                    resumo[unidade_id] = {
                        "nome_pdf":    nome_pdf,
                        "telefones":   telefones,
                        "vencimento":  _formatar_data(vencimento),
                        "competencia": _formatar_data(competencia),
                        "principal":   0.0,
                        "juros":       0.0,
                        "multa":       0.0,
                        "atualizacao": 0.0,
                        "honorarios":  0.0,
                        "total":       0.0,
                    }

                for campo in ("principal", "juros", "multa", "atualizacao", "honorarios", "total"):
                    resumo[unidade_id][campo] += valores[campo]

                detalhado.append({
                    "Condomínio":  None,  # preenchido pelo chamador
                    "Unidade":     nome_pdf,
                    "Código":      id_receb,
                    "Vencimento":  _formatar_data(vencimento),
                    "Competência": _formatar_data(competencia),
                    "Principal":   valores["principal"],
                    "Juros":       valores["juros"],
                    "Multa":       valores["multa"],
                    "Atualização": valores["atualizacao"],
                    "Honorários":  valores["honorarios"],
                    "Total":       valores["total"],
                })

        pagina += 1

    return resumo, detalhado


def _estilizar_cabecalho(ws):
    """Aplica estilo verde ao cabeçalho da planilha."""
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
    """
    Gera relatório Excel com abas Resumo e Detalhado.

    Args:
        id_condominio: ID específico ou None para varrer todos.
        data_posicao:  Data no formato DD/MM/YYYY ou None para hoje.
    """
    # Data de posição: usa o parâmetro, ou hoje formatado corretamente
    if not data_posicao:
        data_posicao = datetime.today().strftime("%m/%d/%Y")
    else:
        # Converte DD/MM/YYYY → MM/DD/YYYY (formato exigido pela API Superlógica)
        partes = data_posicao.split("/")
        if len(partes) == 3:
            data_posicao = f"{partes[1]}/{partes[0]}/{partes[2]}"

    # Range de condomínios a varrer
    if id_condominio:
        ids_range = [id_condominio]
    else:
        max_id = getattr(settings, "SUPERLOGICA_MAX_ID", 100)
        ids_range = range(1, max_id + 1)

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
                "Principal":   round(valores["principal"],   2),
                "Juros":       round(valores["juros"],       2),
                "Multa":       round(valores["multa"],       2),
                "Atualização": round(valores["atualizacao"], 2),
                "Honorários":  round(valores["honorarios"],  2),
                "Total":       round(valores["total"],       2),
            })

        for row in detalhado:
            row["Condomínio"] = nome_condominio
            todo_detalhado.append(row)

        if len(ids_range) > 1:
            time.sleep(0.3)

    if not todas_resumo:
        return None, None

    # Ordena por condomínio e depois por unidade
    todas_resumo.sort(key=lambda r: (r["Condomínio"] or "", r["Unidade"] or ""))
    todo_detalhado.sort(key=lambda r: (r["Condomínio"] or "", r["Unidade"] or ""))

    # Monta Excel com duas abas
    wb = Workbook()

    # Aba Resumo
    ws_resumo = wb.active
    ws_resumo.title = "Resumo"
    headers_resumo = ["Condomínio", "Unidade", "Telefones", "Vencimento", "Competência", "Principal", "Juros", "Multa", "Atualização", "Honorários", "Total"]
    ws_resumo.append(headers_resumo)
    for row in todas_resumo:
        ws_resumo.append([row[h] for h in headers_resumo])
    _estilizar_cabecalho(ws_resumo)

    # Aba Detalhado
    ws_det = wb.create_sheet("Detalhado")
    headers_det = ["Condomínio", "Unidade", "Código", "Vencimento", "Competência", "Principal", "Juros", "Multa", "Atualização", "Honorários", "Total"]
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