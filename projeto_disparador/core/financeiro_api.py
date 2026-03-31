"""
API do módulo financeiro — Despesas via Superlógica + Despesas locais.
"""

from typing import List, Optional
from datetime import date
from ninja import Router, Schema
from ninja.errors import HttpError
from core.auth import JWTAuth
from core.superlogica_despesas import (
    buscar_todas_despesas, resumo_despesas, buscar_despesas,
    liquidar_despesa, criar_despesa_superlogica,
)

financeiro_router = Router(auth=JWTAuth(), tags=["Financeiro"])


def _require_financeiro_or_admin(user):
    is_admin = getattr(user, 'is_staff', False) or getattr(user, 'is_superuser', False)
    is_financeiro = getattr(user, 'is_financeiro', False)
    if not (is_admin or is_financeiro):
        raise HttpError(403, "Acesso restrito ao setor financeiro")


# ── Schemas ───────────────────────────────────────────────────────────────────

class DespesaOut(Schema):
    id: str
    id_parcela: str = ""
    id_contato: str = ""
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


# ── Liquidar despesa no Superlógica ───────────────────────────────────────────

class LiquidarDespesaIn(Schema):
    id_condominio:        int
    id_despesa:           str
    id_parcela:           str
    id_contato:           str = ""
    nome_contato:         str = ""
    dt_liquidacao:        str          # DD/MM/YYYY
    id_forma_pag:         int = 0
    id_conta_banco:       int = 0
    nm_numero_ch:         str = ""
    vl_valor:             float
    vl_pago:              float
    vl_desconto:          float = 0
    vl_multa:             float = 0
    vl_juros:             float = 0
    liquidar_todos:       int = 0      # 0 = só esta parcela, 1 = todas
    emitir_recibo:        int = 0


@financeiro_router.post("/liquidar", response={200: dict})
def liquidar(request, payload: LiquidarDespesaIn):
    """Liquida uma despesa diretamente no Superlógica."""
    _require_financeiro_or_admin(request.auth)
    try:
        data = {
            "ID_DESPESA_DES":          payload.id_despesa,
            "ID_PARCELA_PDES":         payload.id_parcela,
            "ID_CONTATO_CON":          payload.id_contato,
            "ST_NOME_CON":             payload.nome_contato,
            "DT_LIQUIDACAO_PDES":      payload.dt_liquidacao,
            "ID_FORMA_PAG":            payload.id_forma_pag,
            "ID_CONTABANCO_CB":        payload.id_conta_banco,
            "NM_NUMERO_CH":            payload.nm_numero_ch,
            "VL_VALOR_PDES":           payload.vl_valor,
            "CHECK_LIQUIDAR_TODOS_CH": payload.liquidar_todos,
            "EMITIR_RECIBO":           payload.emitir_recibo,
            "VL_DESCONTO_PDES":        payload.vl_desconto,
            "VL_MULTA_PDES":           payload.vl_multa,
            "VL_JUROS_PDES":           payload.vl_juros,
            "VL_PAGO":                 payload.vl_pago,
            "ID_CONDOMINIO_COND":      payload.id_condominio,
        }
        resultado = liquidar_despesa(data)
        return 200, {"ok": True, "resultado": resultado}
    except Exception as e:
        raise HttpError(400, str(e))


# ── Criar despesa no Superlógica ──────────────────────────────────────────────

class CriarDespesaSuperlogicaIn(Schema):
    id_condominio:    int
    id_contato:       str = ""
    nome_contato:     str = ""
    descricao:        str
    dt_vencimento:    str           # DD/MM/YYYY
    dt_competencia:   str = ""      # DD/MM/YYYY
    vl_valor:         float
    id_conta:         str = ""      # ex: "2.1.1"
    id_forma_pag:     int = 0
    id_conta_banco:   int = 0
    observacao:       str = ""
    liquidar_agora:   bool = False
    dt_liquidacao:    str = ""
    vl_pago:          float = 0


@financeiro_router.post("/criar-superlogica", response={200: dict})
def criar_no_superlogica(request, payload: CriarDespesaSuperlogicaIn):
    """Cria uma despesa diretamente no Superlógica."""
    _require_financeiro_or_admin(request.auth)
    try:
        data = {
            "ID_CONDOMINIO_COND":   payload.id_condominio,
            "ID_CONTATO_CON":       payload.id_contato,
            "ST_NOME_CON":          payload.nome_contato,
            "ST_COMPLEMENTO_PDES":  payload.descricao,
            "DT_VENCIMENTO_PDES":   payload.dt_vencimento,
            "DT_DESPESA_DES":       payload.dt_competencia or payload.dt_vencimento,
            "VL_VALOR_PDES":        payload.vl_valor,
            "ST_CONTA_CONT":        payload.id_conta,
            "ID_FORMA_PAG":         payload.id_forma_pag,
            "ID_CONTABANCO_CB":     payload.id_conta_banco,
            "ST_OBS_DES":           payload.observacao,
        }
        if payload.liquidar_agora and payload.dt_liquidacao:
            data["FL_LIQUIDADO_PDES"] = 1
            data["DT_LIQUIDACAO_PDES"] = payload.dt_liquidacao
            data["VL_PAGO"] = payload.vl_pago or payload.vl_valor
        resultado = criar_despesa_superlogica(data)
        return 200, {"ok": True, "resultado": resultado}
    except Exception as e:
        raise HttpError(400, str(e))


# ── Despesas Locais (CRUD) ─────────────────────────────────────────────────────

class DespesaLocalIn(Schema):
    condominio_id:   int
    condominio_nome: str = ""
    descricao:       str
    fornecedor:      str = ""
    categoria:       str = ""
    valor:           float
    vencimento:      date
    data_pagamento:  Optional[date] = None
    status:          str = "pendente"
    observacao:      str = ""


class DespesaLocalOut(Schema):
    id:              str
    condominio_id:   int
    condominio_nome: str
    descricao:       str
    fornecedor:      str
    categoria:       str
    valor:           float
    vencimento:      str
    data_pagamento:  Optional[str]
    status:          str
    observacao:      str
    criado_por:      str
    criado_em:       str


def _fmt_date(d) -> Optional[str]:
    return d.strftime("%d/%m/%Y") if d else None


@financeiro_router.get("/locais", response=List[DespesaLocalOut])
def listar_despesas_locais(
    request,
    condominio_id: Optional[int] = None,
    status: Optional[str] = None,
):
    _require_financeiro_or_admin(request.auth)
    from core.models import DespesaLocal
    qs = DespesaLocal.objects.all()
    if condominio_id:
        qs = qs.filter(condominio_id=condominio_id)
    if status and status != "todas":
        qs = qs.filter(status=status)
    return [
        DespesaLocalOut(
            id=str(d.id),
            condominio_id=d.condominio_id,
            condominio_nome=d.condominio_nome,
            descricao=d.descricao,
            fornecedor=d.fornecedor,
            categoria=d.categoria,
            valor=float(d.valor),
            vencimento=_fmt_date(d.vencimento),
            data_pagamento=_fmt_date(d.data_pagamento),
            status=d.status,
            observacao=d.observacao,
            criado_por=d.criado_por,
            criado_em=d.criado_em.strftime("%d/%m/%Y %H:%M"),
        )
        for d in qs
    ]


@financeiro_router.post("/locais", response={201: DespesaLocalOut})
def criar_despesa_local(request, payload: DespesaLocalIn):
    _require_financeiro_or_admin(request.auth)
    from core.models import DespesaLocal
    user = request.auth
    d = DespesaLocal.objects.create(
        condominio_id=payload.condominio_id,
        condominio_nome=payload.condominio_nome,
        descricao=payload.descricao,
        fornecedor=payload.fornecedor,
        categoria=payload.categoria,
        valor=payload.valor,
        vencimento=payload.vencimento,
        data_pagamento=payload.data_pagamento,
        status=payload.status,
        observacao=payload.observacao,
        criado_por=getattr(user, 'name', '') or getattr(user, 'email', ''),
    )
    return 201, DespesaLocalOut(
        id=str(d.id),
        condominio_id=d.condominio_id,
        condominio_nome=d.condominio_nome,
        descricao=d.descricao,
        fornecedor=d.fornecedor,
        categoria=d.categoria,
        valor=float(d.valor),
        vencimento=_fmt_date(d.vencimento),
        data_pagamento=_fmt_date(d.data_pagamento),
        status=d.status,
        observacao=d.observacao,
        criado_por=d.criado_por,
        criado_em=d.criado_em.strftime("%d/%m/%Y %H:%M"),
    )


@financeiro_router.put("/locais/{despesa_id}", response=DespesaLocalOut)
def atualizar_despesa_local(request, despesa_id: str, payload: DespesaLocalIn):
    _require_financeiro_or_admin(request.auth)
    from core.models import DespesaLocal
    try:
        d = DespesaLocal.objects.get(id=despesa_id)
    except DespesaLocal.DoesNotExist:
        raise HttpError(404, "Despesa não encontrada")
    for field, value in payload.dict().items():
        setattr(d, field, value)
    d.save()
    return DespesaLocalOut(
        id=str(d.id),
        condominio_id=d.condominio_id,
        condominio_nome=d.condominio_nome,
        descricao=d.descricao,
        fornecedor=d.fornecedor,
        categoria=d.categoria,
        valor=float(d.valor),
        vencimento=_fmt_date(d.vencimento),
        data_pagamento=_fmt_date(d.data_pagamento),
        status=d.status,
        observacao=d.observacao,
        criado_por=d.criado_por,
        criado_em=d.criado_em.strftime("%d/%m/%Y %H:%M"),
    )


@financeiro_router.delete("/locais/{despesa_id}", response={204: None})
def excluir_despesa_local(request, despesa_id: str):
    _require_financeiro_or_admin(request.auth)
    from core.models import DespesaLocal
    try:
        DespesaLocal.objects.get(id=despesa_id).delete()
    except DespesaLocal.DoesNotExist:
        raise HttpError(404, "Despesa não encontrada")
    return 204, None
