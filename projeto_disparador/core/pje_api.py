"""
Endpoints para consulta de processos no DataJud (CNJ) — TJRN
e comunicações do PJE Comunica por OAB.
"""
import logging
import requests
from ninja import Router
from ninja.errors import HttpError
from core.auth import JWTAuth

logger = logging.getLogger(__name__)
pje_router = Router(auth=JWTAuth())

DATAJUD_URL    = "https://api-publica.datajud.cnj.jus.br/api_publica_tjrn/_search"
DATAJUD_APIKEY = "APIKey cDZHYzlZa0JadVREZDJCendQbXY6SkJlTzNjLV9TRENyQk1RdnFKZGRQdw=="
HEADERS        = {"Authorization": DATAJUD_APIKEY, "Content-Type": "application/json"}

COMUNICA_URL = "https://comunicaapi.pje.jus.br/api/v1/comunicacao"


def _formatar_data(iso: str) -> str:
    """Converte '2024-03-15T10:30:00' para '15/03/2024 10:30'."""
    if not iso:
        return ""
    try:
        from datetime import datetime
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%d/%m/%Y %H:%M")
    except Exception:
        return iso[:10]


def _extrair_ultimo_movimento(movimentos: list) -> dict:
    """Retorna o movimento mais recente com data e descrição."""
    if not movimentos:
        return {}
    try:
        ordenados = sorted(
            movimentos,
            key=lambda m: m.get("dataHora", ""),
            reverse=True,
        )
        ult = ordenados[0]
        return {
            "data":      _formatar_data(ult.get("dataHora", "")),
            "descricao": ult.get("nome", "") or ult.get("complementosTabelados", [{}])[0].get("descricao", ""),
        }
    except Exception:
        return {}


def _serializar_processo(hit: dict) -> dict:
    src = hit.get("_source", {})
    movimentos = src.get("movimentos", [])
    ultimo_mov = _extrair_ultimo_movimento(movimentos)

    assuntos = [a.get("nome", "") for a in src.get("assuntos", []) if a.get("nome")]
    partes   = []
    for p in src.get("partes", []):
        nome = p.get("nome", "")
        tipo = p.get("polo", "") or p.get("tipoParte", {}).get("nome", "")
        if nome:
            partes.append({"nome": nome, "polo": tipo})

    return {
        "numero":           src.get("numeroProcesso", ""),
        "tribunal":         src.get("tribunal", "TJRN"),
        "grau":             src.get("grau", ""),
        "classe":           src.get("classe", {}).get("nome", ""),
        "assuntos":         assuntos,
        "orgao_julgador":   src.get("orgaoJulgador", {}).get("nome", ""),
        "data_ajuizamento": _formatar_data(src.get("dataAjuizamento", "")),
        "partes":           partes,
        "ultimo_movimento": ultimo_mov,
        "total_movimentos": len(movimentos),
        "nivel_sigilo":     src.get("nivelSigilo", 0),
    }


@pje_router.get("/consultar", response={200: dict})
def consultar_processo(request, numero: str):
    """Consulta um processo no DataJud pelo número CNJ."""
    numero_limpo = numero.strip().replace(" ", "").replace("-", "").replace(".", "")
    if not numero_limpo:
        raise HttpError(400, "Número do processo não informado")

    payload = {
        "query": {
            "term": {"numeroProcesso.keyword": numero_limpo}
        }
    }

    try:
        resp = requests.post(DATAJUD_URL, json=payload, headers=HEADERS, timeout=15)
    except requests.exceptions.Timeout:
        raise HttpError(504, "DataJud não respondeu — tente novamente")
    except Exception as e:
        logger.error(f"Erro ao consultar DataJud: {e}")
        raise HttpError(502, "Erro ao conectar com o DataJud")

    if not resp.ok:
        raise HttpError(502, f"DataJud retornou erro {resp.status_code}")

    data = resp.json()
    hits = data.get("hits", {}).get("hits", [])

    if not hits:
        raise HttpError(404, "Processo não encontrado no TJRN")

    return 200, {"processo": _serializar_processo(hits[0])}


@pje_router.get("/movimentos", response={200: dict})
def listar_movimentos(request, numero: str):
    """Retorna todos os movimentos de um processo ordenados do mais recente."""
    numero_limpo = numero.strip().replace(" ", "").replace("-", "").replace(".", "")
    if not numero_limpo:
        raise HttpError(400, "Número do processo não informado")

    payload = {
        "query": {
            "term": {"numeroProcesso.keyword": numero_limpo}
        },
        "_source": ["numeroProcesso", "movimentos"],
    }

    try:
        resp = requests.post(DATAJUD_URL, json=payload, headers=HEADERS, timeout=15)
    except Exception as e:
        logger.error(f"Erro ao consultar DataJud: {e}")
        raise HttpError(502, "Erro ao conectar com o DataJud")

    if not resp.ok:
        raise HttpError(502, f"DataJud retornou erro {resp.status_code}")

    hits = resp.json().get("hits", {}).get("hits", [])
    if not hits:
        raise HttpError(404, "Processo não encontrado")

    movimentos = hits[0].get("_source", {}).get("movimentos", [])
    ordenados  = sorted(movimentos, key=lambda m: m.get("dataHora", ""), reverse=True)

    return 200, {
        "numero":     numero_limpo,
        "movimentos": [
            {
                "data":      _formatar_data(m.get("dataHora", "")),
                "descricao": m.get("nome", "") or "",
                "codigo":    m.get("codigo", ""),
            }
            for m in ordenados
        ],
    }


@pje_router.get("/oab", response={200: dict})
def consultar_por_oab(request, numero_oab: str, uf_oab: str, pagina: int = 1):
    """
    Consulta comunicações processuais pelo número da OAB via PJE Comunica.
    Parâmetros:
      - numero_oab: número da OAB (apenas dígitos)
      - uf_oab: UF da OAB (ex: RN, SP)
      - pagina: página de resultados (padrão 1)
    """
    numero_limpo = numero_oab.strip().replace(" ", "")
    uf_limpo = uf_oab.strip().upper()

    if not numero_limpo or not uf_limpo:
        raise HttpError(400, "Número e UF da OAB são obrigatórios")

    params = {
        "numeroOAB": numero_limpo,
        "ufOAB": uf_limpo,
        "pagina": pagina,
    }

    try:
        resp = requests.get(COMUNICA_URL, params=params, timeout=20)
    except requests.exceptions.Timeout:
        raise HttpError(504, "PJE Comunica não respondeu — tente novamente")
    except Exception as e:
        logger.error(f"Erro ao consultar PJE Comunica: {e}")
        raise HttpError(502, "Erro ao conectar com o PJE Comunica")

    if resp.status_code == 404:
        return 200, {"comunicacoes": [], "total": 0, "pagina": pagina, "total_paginas": 0}

    if not resp.ok:
        raise HttpError(502, f"PJE Comunica retornou erro {resp.status_code}")

    data = resp.json()
    logger.debug(f"PJE Comunica resposta: {str(data)[:500]}")

    items = data.get("items", [])
    total = data.get("count", len(items))
    # A API não informa total de páginas; calcula com base em 20 itens por página (padrão)
    por_pagina = len(items) if items else 20
    total_paginas = max(1, (total + por_pagina - 1) // por_pagina) if por_pagina else 1

    comunicacoes = []
    for item in items:
        # Monta string de destinatários a partir do array
        destinatarios = item.get("destinatarios", [])
        nomes_dest = ", ".join(d.get("nome", "") for d in destinatarios if d.get("nome"))

        # Data já vem como "YYYY-MM-DD" ou "DD/MM/YYYY"
        data_disp = item.get("data_disponibilizacao", "")
        if data_disp and "-" in data_disp:
            try:
                from datetime import datetime
                data_disp = datetime.strptime(data_disp, "%Y-%m-%d").strftime("%d/%m/%Y")
            except Exception:
                pass

        texto = item.get("texto", "") or ""

        comunicacoes.append({
            "numero_processo":        item.get("numeroprocessocommascara", "") or item.get("numero_processo", ""),
            "tipo_comunicacao":       item.get("tipoComunicacao", ""),
            "data_disponibilizacao":  data_disp,
            "destinatario":           nomes_dest,
            "meio_comunicacao":       item.get("meiocompleto", item.get("meio", "")),
            "orgao_julgador":         item.get("nomeOrgao", ""),
            "status":                 item.get("status", ""),
            "texto":                  texto[:300],
        })

    return 200, {
        "comunicacoes":  comunicacoes,
        "total":         total,
        "pagina":        pagina,
        "total_paginas": total_paginas,
    }
