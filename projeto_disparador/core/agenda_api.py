"""
API de Agenda — CRUD de tarefas e insights de inadimplência/contas a receber.
"""
from datetime import date, timedelta, datetime
from typing import List, Optional

from django.db.models import Sum, Count
from ninja import Router, Schema
from ninja.errors import HttpError

from core.auth import JWTAuth
from core.models import AgendaTarefa, DespesaLocal, InadimplenciaSnapshot

agenda_router = Router(auth=JWTAuth(), tags=["Agenda"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ChecklistItem(Schema):
    texto:      str
    concluido:  bool = False
    criado_por: str  = ""


class TarefaIn(Schema):
    titulo:    str
    descricao: str = ""
    data:      date
    hora:      Optional[str] = None   # "HH:MM"
    cor:       str = "primary"
    checklist: List[ChecklistItem] = []


class TarefaOut(Schema):
    id:         str
    titulo:     str
    descricao:  str
    data:       str   # "YYYY-MM-DD"
    hora:       Optional[str]
    cor:        str
    checklist:  List[ChecklistItem]
    criado_por: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _tarefa_out(t: AgendaTarefa) -> TarefaOut:
    checklist_raw = t.checklist if isinstance(t.checklist, list) else []
    return TarefaOut(
        id=str(t.id),
        titulo=t.titulo,
        descricao=t.descricao,
        data=t.data.strftime("%Y-%m-%d"),
        hora=t.hora.strftime("%H:%M") if t.hora else None,
        cor=t.cor,
        checklist=[ChecklistItem(**item) for item in checklist_raw],
        criado_por=t.criado_por,
    )


# ── CRUD Tarefas ──────────────────────────────────────────────────────────────

@agenda_router.get("/tarefas", response=List[TarefaOut])
def listar_tarefas(
    request,
    mes: Optional[str] = None,
    data_inicio: Optional[date] = None,
    data_fim: Optional[date] = None,
):
    """
    Lista tarefas.
    Aceita ?mes=YYYY-MM  OU  ?data_inicio=YYYY-MM-DD&data_fim=YYYY-MM-DD
    """
    qs = AgendaTarefa.objects.all()
    if data_inicio and data_fim:
        qs = qs.filter(data__gte=data_inicio, data__lte=data_fim)
    elif mes:
        try:
            ano, m = mes.split("-")
            qs = qs.filter(data__year=int(ano), data__month=int(m))
        except (ValueError, AttributeError):
            pass
    return [_tarefa_out(t) for t in qs]


@agenda_router.post("/tarefas", response={201: TarefaOut})
def criar_tarefa(request, payload: TarefaIn):
    """Cria uma nova tarefa na agenda."""
    hora = None
    if payload.hora:
        try:
            from datetime import time as dtime
            h, mi = payload.hora.split(":")
            hora = dtime(int(h), int(mi))
        except (ValueError, AttributeError):
            pass

    t = AgendaTarefa.objects.create(
        titulo=payload.titulo,
        descricao=payload.descricao,
        data=payload.data,
        hora=hora,
        cor=payload.cor,
        checklist=[item.dict() for item in payload.checklist],
        criado_por=getattr(request.auth, "name", "") or getattr(request.auth, "email", ""),
    )
    return 201, _tarefa_out(t)


@agenda_router.put("/tarefas/{tarefa_id}", response=TarefaOut)
def atualizar_tarefa(request, tarefa_id: str, payload: TarefaIn):
    """Atualiza uma tarefa existente."""
    try:
        t = AgendaTarefa.objects.get(id=tarefa_id)
    except AgendaTarefa.DoesNotExist:
        raise HttpError(404, "Tarefa não encontrada")

    hora = None
    if payload.hora:
        try:
            from datetime import time as dtime
            h, mi = payload.hora.split(":")
            hora = dtime(int(h), int(mi))
        except (ValueError, AttributeError):
            pass

    t.titulo = payload.titulo
    t.descricao = payload.descricao
    t.data = payload.data
    t.hora = hora
    t.cor = payload.cor
    t.checklist = [item.dict() for item in payload.checklist]
    t.save()
    return _tarefa_out(t)


@agenda_router.delete("/tarefas/{tarefa_id}", response={200: dict})
def excluir_tarefa(request, tarefa_id: str):
    """Exclui uma tarefa."""
    try:
        AgendaTarefa.objects.get(id=tarefa_id).delete()
    except AgendaTarefa.DoesNotExist:
        raise HttpError(404, "Tarefa não encontrada")
    return {"ok": True}


# ── Helpers ───────────────────────────────────────────────────────────────────

_BOLETOS_SHEET_ID  = "1C6XfrKUpIuLaj8hXCSMtCOa9_7inaIBZxYLz4awRwJ4"
_BOLETOS_SHEET_ABA = "Planilha1"

def _contar_boletos_gerados() -> int:
    """
    Lê a planilha de boletos e conta quantas linhas têm a coluna
    'DATA LANÇAMENTO' (índice 2) preenchida.
    Linha 0: título geral, Linha 1: cabeçalho, Linha 2+: dados
    Colunas: CONDOMÍNIO | DATA VENCIMENTO | DATA LANÇAMENTO
    """
    try:
        from core.sheets_service import buscar_dados_planilha
        rows = buscar_dados_planilha(
            _BOLETOS_SHEET_ID,
            _BOLETOS_SHEET_ABA,
            use_cache=True,
        )
        if not rows:
            return 0
        # Pula linha 0 (título) e linha 1 (cabeçalho), conta col[2] preenchida
        count = 0
        for row in rows[2:]:
            if len(row) >= 3 and str(row[2]).strip():
                count += 1
        return count
    except Exception:
        return 0


# ── Insights ──────────────────────────────────────────────────────────────────

@agenda_router.get("/insights", response={200: dict})
def get_insights(request):
    """
    Retorna métricas e insights de inadimplência e despesas a receber.
    Combina dados das DespesaLocal com o cache do dashboard se disponível.
    """
    hoje = date.today()
    inicio_mes = hoje.replace(day=1)

    # ── Despesas locais ──
    qs = DespesaLocal.objects.all()
    total_pendente = float(qs.filter(status="pendente").aggregate(t=Sum("valor"))["t"] or 0)
    total_pago_mes = float(
        qs.filter(status="pago", data_pagamento__gte=inicio_mes)
        .aggregate(t=Sum("valor"))["t"] or 0
    )

    vencendo_qs = qs.filter(
        status="pendente",
        vencimento__gte=hoje,
        vencimento__lte=hoje + timedelta(days=7),
    ).order_by("vencimento")

    vencidos_qs = qs.filter(
        status="pendente",
        vencimento__lt=hoje,
    ).order_by("vencimento")

    top_condominios = list(
        qs.filter(status="pendente")
        .values("condominio_nome")
        .annotate(total=Sum("valor"), qtd=Count("id"))
        .order_by("-total")[:5]
    )

    # Histórico de pagamentos últimos 6 meses (DespesaLocal)
    historico = []
    for i in range(5, -1, -1):
        ref = hoje.replace(day=1)
        mes_ref = ref.month - i
        ano_ref = ref.year
        while mes_ref <= 0:
            mes_ref += 12
            ano_ref -= 1
        ref_inicio = date(ano_ref, mes_ref, 1)
        ref_fim = date(ano_ref + 1, 1, 1) if mes_ref == 12 else date(ano_ref, mes_ref + 1, 1)
        pago = float(
            qs.filter(status="pago", data_pagamento__gte=ref_inicio, data_pagamento__lt=ref_fim)
            .aggregate(t=Sum("valor"))["t"] or 0
        )
        pendente = float(
            qs.filter(status="pendente", vencimento__gte=ref_inicio, vencimento__lt=ref_fim)
            .aggregate(t=Sum("valor"))["t"] or 0
        )
        historico.append({"mes": ref_inicio.strftime("%b/%y"), "pago": pago, "pendente": pendente})

    # ── Variações baseadas nos snapshots persistidos ──────────────────────────
    snapshots = list(InadimplenciaSnapshot.objects.order_by("ano", "mes"))
    snap_map = {(s.ano, s.mes): float(s.total) for s in snapshots}

    snap_atual = snap_map.get((hoje.year, hoje.month))

    # Mês anterior
    mes_ant = hoje.month - 1 or 12
    ano_ant = hoje.year if hoje.month > 1 else hoje.year - 1
    snap_mes_ant = snap_map.get((ano_ant, mes_ant))

    # Mesmo mês ano anterior — usa o mais próximo disponível (±2 meses) se exato não existir
    snap_ano_ant = snap_map.get((hoje.year - 1, hoje.month))
    if snap_ano_ant is None:
        for delta in [1, -1, 2, -2]:
            m = hoje.month + delta
            a = hoje.year - 1
            if m <= 0: m += 12
            if m > 12: m -= 12
            snap_ano_ant = snap_map.get((a, m))
            if snap_ano_ant is not None:
                break

    def _pct(valor, base):
        raw = (valor / base) * 100
        # Usa 2 casas decimais quando o valor absoluto é menor que 0.1%
        casas = 2 if abs(raw) < 0.1 else 1
        return round(raw, casas)

    # Variação mensal
    if snap_atual is not None and snap_mes_ant is not None and snap_mes_ant > 0:
        var_mensal_valor = round(snap_atual - snap_mes_ant, 2)
        var_mensal_pct   = _pct(var_mensal_valor, snap_mes_ant)
    else:
        var_mensal_valor = None
        var_mensal_pct   = None

    # Variação anual
    if snap_atual is not None and snap_ano_ant is not None and snap_ano_ant > 0:
        var_anual_valor = round(snap_atual - snap_ano_ant, 2)
        var_anual_pct   = _pct(var_anual_valor, snap_ano_ant)
    else:
        var_anual_valor = None
        var_anual_pct   = None

    # Projeção: tendência média dos últimos 3 snapshots disponíveis
    ultimos_snaps = [float(s.total) for s in snapshots[-3:]]
    if len(ultimos_snaps) >= 2 and (snap_atual or 0) > 0:
        deltas = [ultimos_snaps[i+1] - ultimos_snaps[i] for i in range(len(ultimos_snaps)-1)]
        media_delta = sum(deltas) / len(deltas)
        projecao = round((snap_atual or 0) + media_delta, 2)
    else:
        projecao = None

    # ── Cache do dashboard (inadimplência via Superlógica) ──
    # Fallback: usa o snapshot mais recente do banco quando o cache em memória estiver vazio
    snap_fallback = snapshots[-1] if snapshots else None
    total_fallback = float(snap_fallback.total) if snap_fallback else 0.0

    inadimplencia = {
        "total_a_receber":    total_fallback,
        "total_condominios":  0,
        "total_unidades":     0,
        "maior_condo_nome":   "",
        "maior_condo_valor":  0.0,
        "sem_numero":         0,
        "top_condominios":    [],
        "ultima_atualizacao": snap_fallback.capturado_em.strftime("%d/%m/%Y %H:%M") if snap_fallback else "",
        "variacao_valor":     None,
        "variacao_pct":       None,
        "var_mensal_valor":   var_mensal_valor,
        "var_mensal_pct":     var_mensal_pct,
        "var_anual_valor":    var_anual_valor,
        "var_anual_pct":      var_anual_pct,
        "projecao":           projecao,
        "fonte":              "snapshot",
    }
    try:
        from core.admin_api import _DASHBOARD_CACHE, _CACHE_LOCK
        with _CACHE_LOCK:
            caches = list(_DASHBOARD_CACHE.values())
        if caches:
            mais_recente = max(caches, key=lambda c: c.get("expires_at", datetime.min))
            d = mais_recente.get("data", {})
            total_atual = float(d.get("total_inadimplencia", 0) or 0)
            # Só usa o cache se tiver valor real (dashboard foi carregado)
            if total_atual > 0:
                total_anterior = mais_recente.get("total_anterior")
                if total_anterior is not None and total_anterior > 0:
                    variacao_valor = total_atual - total_anterior
                    variacao_pct   = round((variacao_valor / total_anterior) * 100, 1)
                else:
                    variacao_valor = None
                    variacao_pct   = None
                ranking_raw = d.get("condo_ranking") or []
                inadimplencia = {
                    "total_a_receber":    total_atual,
                    "total_condominios":  int(d.get("total_condominios", 0) or 0),
                    "total_unidades":     int(d.get("total_unidades", 0) or 0),
                    "maior_condo_nome":   d.get("maior_condo_nome") or "",
                    "maior_condo_valor":  float(d.get("maior_condo_valor", 0) or 0),
                    "sem_numero":         int(d.get("sem_numero_count", 0) or 0),
                    "top_condominios":    [
                        {"nome": c.get("nome", ""), "total": float(c.get("valor", 0))}
                        for c in ranking_raw[:5]
                    ],
                    "ultima_atualizacao": d.get("gerado_em", ""),
                    "variacao_valor":     variacao_valor,
                    "variacao_pct":       variacao_pct,
                    "var_mensal_valor":   var_mensal_valor,
                    "var_mensal_pct":     var_mensal_pct,
                    "var_anual_valor":    var_anual_valor,
                    "var_anual_pct":      var_anual_pct,
                    "projecao":           projecao,
                    "fonte":              "dashboard",
                }
    except Exception:
        pass

    return 200, {
        "despesas": {
            "total_pendente": total_pendente,
            "total_pago_mes": total_pago_mes,
            "vencendo_7d_count": vencendo_qs.count(),
            "vencidos_count":    vencidos_qs.count(),
            "vencendo_7d": [
                {
                    "descricao":   d.descricao,
                    "vencimento":  d.vencimento.strftime("%d/%m/%Y"),
                    "valor":       float(d.valor),
                    "condominio":  d.condominio_nome,
                }
                for d in vencendo_qs[:6]
            ],
            "vencidos": [
                {
                    "descricao":   d.descricao,
                    "vencimento":  d.vencimento.strftime("%d/%m/%Y"),
                    "valor":       float(d.valor),
                    "condominio":  d.condominio_nome,
                }
                for d in vencidos_qs[:6]
            ],
            "top_condominios": [
                {"nome": c["condominio_nome"], "total": float(c["total"]), "qtd": c["qtd"]}
                for c in top_condominios
            ],
            "historico": historico,
        },
        "inadimplencia": inadimplencia,
        "workflow": {
            "demandas_pendentes":    0,
            "cadernos_pendentes":    0,
            "condominios_sem_doc":   0,
            "folhas_pendentes":      0,
            "prestacao_pendentes":   0,
            "boletos_gerados":       _contar_boletos_gerados(),
        },
    }
