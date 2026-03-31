"""
API de Agenda — CRUD de tarefas e insights de inadimplência/contas a receber.
"""
from datetime import date, timedelta, datetime
from typing import List, Optional

from django.db.models import Sum, Count
from ninja import Router, Schema
from ninja.errors import HttpError

from core.auth import JWTAuth
from core.models import AgendaTarefa, DespesaLocal

agenda_router = Router(auth=JWTAuth(), tags=["Agenda"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class TarefaIn(Schema):
    titulo:   str
    descricao: str = ""
    data:     date
    hora:     Optional[str] = None   # "HH:MM"
    cor:      str = "primary"


class TarefaOut(Schema):
    id:         str
    titulo:     str
    descricao:  str
    data:       str   # "YYYY-MM-DD"
    hora:       Optional[str]
    cor:        str
    criado_por: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _tarefa_out(t: AgendaTarefa) -> TarefaOut:
    return TarefaOut(
        id=str(t.id),
        titulo=t.titulo,
        descricao=t.descricao,
        data=t.data.strftime("%Y-%m-%d"),
        hora=t.hora.strftime("%H:%M") if t.hora else None,
        cor=t.cor,
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

    # Histórico de pagamentos últimos 6 meses
    historico = []
    for i in range(5, -1, -1):
        ref = hoje.replace(day=1) - timedelta(days=i * 30)
        ref_inicio = ref.replace(day=1)
        if ref.month == 12:
            ref_fim = ref.replace(year=ref.year + 1, month=1, day=1)
        else:
            ref_fim = ref.replace(month=ref.month + 1, day=1)
        pago = float(
            qs.filter(status="pago", data_pagamento__gte=ref_inicio, data_pagamento__lt=ref_fim)
            .aggregate(t=Sum("valor"))["t"] or 0
        )
        pendente = float(
            qs.filter(status="pendente", vencimento__gte=ref_inicio, vencimento__lt=ref_fim)
            .aggregate(t=Sum("valor"))["t"] or 0
        )
        historico.append({
            "mes": ref_inicio.strftime("%b/%y"),
            "pago": pago,
            "pendente": pendente,
        })

    # ── Cache do dashboard (inadimplência via Superlógica) ──
    inadimplencia = {}
    try:
        from core.admin_api import _DASHBOARD_CACHE, _CACHE_LOCK
        with _CACHE_LOCK:
            caches = list(_DASHBOARD_CACHE.values())
        if caches:
            mais_recente = max(caches, key=lambda c: c.get("expires_at", datetime.min))
            d = mais_recente.get("data", {})
            # condo_ranking: [{"nome": ..., "valor": ...}]
            ranking_raw = d.get("condo_ranking") or []
            top_condominios_inadimp = [
                {"nome": c.get("nome", ""), "total": float(c.get("valor", 0))}
                for c in ranking_raw[:5]
            ]
            inadimplencia = {
                "total_a_receber":    float(d.get("total_inadimplencia", 0) or 0),
                "total_condominios":  int(d.get("total_condominios", 0) or 0),
                "total_unidades":     int(d.get("total_unidades", 0) or 0),
                "maior_condo_nome":   d.get("maior_condo_nome") or "",
                "maior_condo_valor":  float(d.get("maior_condo_valor", 0) or 0),
                "sem_numero":         int(d.get("sem_numero_count", 0) or 0),
                "top_condominios":    top_condominios_inadimp,
                "ultima_atualizacao": d.get("gerado_em", ""),
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
    }
