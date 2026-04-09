"""
API para dados de sindicos a partir do Google Sheets.
Planilha: CLIENTES PRATIKA 2026
"""

from typing import List, Optional
from ninja import Router, Schema
from core.auth import JWTAuth
from core.sheets_service import buscar_dados_planilha

sindico_router = Router(auth=JWTAuth(), tags=["Sindicos"])

SPREADSHEET_ID = "1uO5Fy5WIOtfmA37UP8uFgt0xgvhbbD-y8LYk52b9iRw"
ABA = "CLIENTES PRÁTIKA 2026"


class SindicoOut(Schema):
    numero: str
    cliente: str
    cnpj: str
    garantidora: str
    juridico_pratika: str
    juridico_proprio: str
    contas_pagar: str
    qtd_unidades: str
    municipio: str
    folha_pagamento: str
    sindico: str
    telefone_sindico: str
    subsindico: str
    telefone_subsindico: str
    gerente: str
    telefone_gerente: str
    data_inicio_mandato: str
    data_final_mandato: str
    data_inicio_contrato: str
    folha_pagamento_pratika: str
    empresa_terceirizada: str
    contrato_portaria: str
    valor_contrato_portaria: str
    contrato_vigilancia: str
    valor_contrato_vigilancia: str
    contrato_jardinagem: str
    valor_contrato_jardinagem: str
    paulo_conversou: str
    relacionamento: str


def _cell(row, idx):
    """Retorna celula ou string vazia se nao existir."""
    try:
        return (row[idx] or "").strip()
    except (IndexError, AttributeError):
        return ""


def _parse_rows(rows) -> List[dict]:
    """Converte linhas brutas da planilha em lista de dicts."""
    result = []
    for row in rows:
        if not row or not _cell(row, 0):
            continue
        result.append({
            "numero": _cell(row, 0),
            "cliente": _cell(row, 1),
            "cnpj": _cell(row, 2),
            "garantidora": _cell(row, 3),
            "juridico_pratika": _cell(row, 4),
            "juridico_proprio": _cell(row, 5),
            "contas_pagar": _cell(row, 6),
            "qtd_unidades": _cell(row, 7),
            "municipio": _cell(row, 8),
            "folha_pagamento": _cell(row, 9),
            "sindico": _cell(row, 10),
            "telefone_sindico": _cell(row, 11),
            "subsindico": _cell(row, 12),
            "telefone_subsindico": _cell(row, 13),
            "gerente": _cell(row, 14),
            "telefone_gerente": _cell(row, 15),
            "data_inicio_mandato": _cell(row, 16),
            "data_final_mandato": _cell(row, 17),
            "data_inicio_contrato": _cell(row, 18),
            "folha_pagamento_pratika": _cell(row, 19),
            "empresa_terceirizada": _cell(row, 20),
            "contrato_portaria": _cell(row, 21),
            "valor_contrato_portaria": _cell(row, 22),
            "contrato_vigilancia": _cell(row, 23),
            "valor_contrato_vigilancia": _cell(row, 24),
            "contrato_jardinagem": _cell(row, 25),
            "valor_contrato_jardinagem": _cell(row, 26),
            "paulo_conversou": _cell(row, 27),
            "relacionamento": _cell(row, 28),
        })
    return result


@sindico_router.get(
    "/",
    response=List[SindicoOut],
    summary="Lista todos os clientes/sindicos da planilha",
)
def listar_sindicos(request, busca: Optional[str] = None):
    """
    Retorna dados da planilha CLIENTES PRATIKA 2026.
    Filtro opcional por nome do cliente, sindico ou municipio.
    """
    dados = buscar_dados_planilha(SPREADSHEET_ID, f"{ABA}!A3:AC", use_cache=True)
    sindicos = _parse_rows(dados)

    if busca:
        busca_lower = busca.lower()
        sindicos = [
            s for s in sindicos
            if busca_lower in s["cliente"].lower()
            or busca_lower in s["sindico"].lower()
            or busca_lower in s["municipio"].lower()
            or busca_lower in s["cnpj"].lower()
        ]

    return sindicos
