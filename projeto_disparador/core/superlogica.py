import time
from datetime import datetime
from io import BytesIO

import requests
from django.conf import settings
from openpyxl import Workbook


def _get_headers() -> dict:
    return {
        "Content-Type": "application/json",
        "app_token": settings.SUPERLOGICA_APP_TOKEN,
        "access_token": settings.SUPERLOGICA_ACCESS_TOKEN,
    }


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


def buscar_unidades(id_condominio: int) -> dict | None:
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


def _extrair_componentes(receb: dict) -> dict:
    """
    Extrai principal, juros, multa, atualização e honorários de um recebimento.

    - Principal: vl_emitido_recb (valor original, sem encargos)
    - Encargos: apenas de encargos[0].detalhes quando a API é chamada
      com comValoresAtualizados=1 e comValoresAtualizadosPorComposicao=1
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


def buscar_inadimplentes(
    id_condominio: int, mapa_unidades: dict, data_posicao: str
) -> tuple[dict, list] | tuple[None, None]:
    resumo: dict = {}
    detalhado: list = []
    recebimentos_processados: set = set()
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
            recebimentos = item.get("recebimento", [])
            if not isinstance(recebimentos, list):
                continue

            for receb in recebimentos:
                if not isinstance(receb, dict):
                    continue
                if receb.get("fl_status_recb") != "0":
                    continue

                id_receb = receb.get("id_recebimento_recb")
                if id_receb in recebimentos_processados:
                    continue
                recebimentos_processados.add(id_receb)

                unidade_id  = receb.get("id_unidade_uni")
                codigo      = receb.get("id_recebimento_recb")
                vencimento  = receb.get("dt_vencimento_recb")
                competencia = receb.get("dt_competencia_recb")

                dados_unidade = mapa_unidades.get(unidade_id, {})
                nome_pdf      = dados_unidade.get("nome_pdf", f"Unidade {unidade_id}")
                valores       = _extrair_componentes(receb)

                if unidade_id not in resumo:
                    resumo[unidade_id] = {
                        "nome_pdf":    nome_pdf,
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
                    "Unidade":     nome_pdf,
                    "Código":      codigo,
                    "Vencimento":  vencimento,
                    "Competência": competencia,
                    "Principal":   valores["principal"],
                    "Juros":       valores["juros"],
                    "Multa":       valores["multa"],
                    "Atualização": valores["atualizacao"],
                    "Honorários":  valores["honorarios"],
                    "Total":       valores["total"],
                })

        pagina += 1

    return resumo, detalhado


def gerar_relatorio_inadimplentes(
    id_condominio: int | None = None,
    data_posicao: str | None = None,
) -> tuple[bytes, str] | tuple[None, None]:
    """
    Gera um arquivo Excel em memória com duas abas:
      - Resumo: uma linha por unidade inadimplente com totais
      - Detalhado: uma linha por cobrança em aberto

    Se id_condominio for None, varre do ID 1 até SUPERLOGICA_MAX_ID.
    Se data_posicao for None, usa a data de hoje (formato dd/mm/yyyy).
    """
    if data_posicao is None:
        data_posicao = datetime.today().strftime("%d/%m/%Y")

    max_id = getattr(settings, "SUPERLOGICA_MAX_ID", 100)

    ids_para_varrer = (
        [id_condominio] if id_condominio is not None else range(1, max_id + 1)
    )

    linhas_resumo: list[dict] = []
    linhas_detalhado: list[dict] = []

    for cid in ids_para_varrer:
        acesso, nome_condominio = verificar_condominio(cid)
        if not acesso:
            continue

        mapa_unidades = buscar_unidades(cid)
        if not mapa_unidades:
            continue

        resumo, detalhado = buscar_inadimplentes(cid, mapa_unidades, data_posicao)
        if not resumo:
            continue

        for unidade_id, valores in resumo.items():
            dados_unidade = mapa_unidades.get(unidade_id, {})
            telefones     = dados_unidade.get("telefones", [])

            linhas_resumo.append({
                "Condomínio":  nome_condominio,
                "Unidade":     valores["nome_pdf"],
                "Telefones":   " | ".join(telefones) if telefones else "",
                "Principal":   round(valores["principal"],   2),
                "Juros":       round(valores["juros"],       2),
                "Multa":       round(valores["multa"],       2),
                "Atualização": round(valores["atualizacao"], 2),
                "Honorários":  round(valores["honorarios"],  2),
                "Total":       round(valores["total"],       2),
            })

        for linha in detalhado:
            linhas_detalhado.append({
                "Condomínio": nome_condominio,
                **linha,
            })

        time.sleep(0.3)

    if not linhas_resumo:
        return None, None

    # Ordena resumo por condomínio e unidade
    linhas_resumo.sort(key=lambda r: (r["Condomínio"] or "", r["Unidade"] or ""))
    linhas_detalhado.sort(key=lambda r: (r["Condomínio"] or "", r["Unidade"] or "", str(r.get("Código") or "")))

    wb = Workbook()

    # ── Aba Resumo ──────────────────────────────────────────────────────────────
    ws_resumo = wb.active
    ws_resumo.title = "Resumo"
    headers_resumo = [
        "Condomínio", "Unidade", "Telefones",
        "Principal", "Juros", "Multa", "Atualização", "Honorários", "Total",
    ]
    ws_resumo.append(headers_resumo)
    for linha in linhas_resumo:
        ws_resumo.append([linha[h] for h in headers_resumo])

    # ── Aba Detalhado ───────────────────────────────────────────────────────────
    ws_det = wb.create_sheet("Detalhado")
    headers_det = [
        "Condomínio", "Unidade", "Código", "Vencimento", "Competência",
        "Principal", "Juros", "Multa", "Atualização", "Honorários", "Total",
    ]
    ws_det.append(headers_det)
    for linha in linhas_detalhado:
        ws_det.append([linha.get(h, "") for h in headers_det])

    buffer = BytesIO()
    wb.save(buffer)
    buffer.seek(0)

    filename = f"inadimplentes_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return buffer.getvalue(), filename