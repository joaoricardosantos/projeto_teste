"""
API do módulo financeiro — Despesas via Superlógica.
"""

from typing import List, Optional
from ninja import Router, Schema
from ninja.errors import HttpError
from core.auth import JWTAuth
from core.superlogica_despesas import buscar_todas_despesas, resumo_despesas, buscar_despesas

financeiro_router = Router(auth=JWTAuth(), tags=["Financeiro"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class DespesaOut(Schema):
    id: str
    descricao: str
    fornecedor: str
    conta: str
    categoria: str
    valor: float
    valor_pago: float
    vencimento: str
    liquidacao: str
    competencia: str
    status: str


class CategoriaOut(Schema):
    categoria: str
    total: float
    quantidade: int


class FornecedorOut(Schema):
    fornecedor: str
    total: float


class MesOut(Schema):
    mes: str
    total: float
    quantidade: int


class ResumoOut(Schema):
    total_geral: float
    total_pago: float
    total_pendente: float
    total_liquidado: float
    quantidade: int
    por_categoria: List[CategoriaOut]
    por_fornecedor: List[FornecedorOut]
    por_mes: List[MesOut]


class DespesasResponseOut(Schema):
    resumo: ResumoOut
    despesas: List[DespesaOut]
    atualizado_em: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@financeiro_router.get("/despesas/{id_condominio}", response=DespesasResponseOut)
def listar_despesas(
    request,
    id_condominio: int,
    dt_inicio: str,
    dt_fim: str,
    com_status: str = "todas",
    filtrar_por: str = "vencimento",
    contas: Optional[str] = None,
):
    """
    Retorna despesas de um condomínio no período informado.

    Parâmetros:
    - dt_inicio / dt_fim : formato DD/MM/YYYY
    - com_status         : todas | pendentes | liquidadas
    - filtrar_por        : vencimento | liquidacao | competencia | criacao
    - contas             : contas separadas por vírgula (ex: "2.1.1,2.3.2")
    """
    from datetime import datetime
    try:
        lista_contas = [c.strip() for c in contas.split(",")] if contas else None

        despesas = buscar_todas_despesas(
            id_condominio=id_condominio,
            dt_inicio=dt_inicio,
            dt_fim=dt_fim,
            com_status=com_status,
            filtrar_por=filtrar_por,
            contas=lista_contas,
        )

        res = resumo_despesas(despesas)

        return {
            "resumo": res,
            "despesas": despesas,
            "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
        }

    except Exception as e:
        raise HttpError(400, str(e))


@financeiro_router.get("/despesas/{id_condominio}/paginado")
def listar_despesas_paginado(
    request,
    id_condominio: int,
    dt_inicio: str,
    dt_fim: str,
    com_status: str = "todas",
    filtrar_por: str = "vencimento",
    contas: Optional[str] = None,
    pagina: int = 1,
):
    """Retorna despesas paginadas (50 por página)."""
    try:
        lista_contas = [c.strip() for c in contas.split(",")] if contas else None

        resultado = buscar_despesas(
            id_condominio=id_condominio,
            dt_inicio=dt_inicio,
            dt_fim=dt_fim,
            com_status=com_status,
            filtrar_por=filtrar_por,
            contas=lista_contas,
            pagina=pagina,
        )

        return resultado

    except Exception as e:
        raise HttpError(400, str(e))
