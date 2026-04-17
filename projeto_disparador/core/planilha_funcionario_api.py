from datetime import datetime
from typing import List, Optional

from ninja import Router, Schema
from ninja.errors import HttpError

from core.auth import JWTAuth
from core.models import (
    User,
    PlanilhaFuncionarioConfig,
    PlanilhaConfigColuna,
    PlanilhaPeriodo,
    PlanilhaLinha,
    PlanilhaCelula,
)

planilha_router = Router(auth=JWTAuth(), tags=["Planilhas"])


def _is_admin(user):
    return user.is_staff or user.is_superuser


def _require_admin(user):
    if not _is_admin(user):
        raise HttpError(403, "Admin_required")


# ── Schemas ───────────────────────────────────────────────────────────────────

class UserOut(Schema):
    id: str
    nome: str
    email: str


class ColunaIn(Schema):
    nome: str
    tipo: str = 'texto'
    ordem: int = 0
    prazo_dias: Optional[int] = None
    obrigatorio: bool = True


class ColunaOut(Schema):
    id: str
    nome: str
    tipo: str
    ordem: int
    prazo_dias: Optional[int]
    obrigatorio: bool


class ConfigIn(Schema):
    funcionario_id: str
    nome: str


class ConfigOut(Schema):
    id: str
    nome: str
    funcionario_id: str
    funcionario_nome: str
    colunas: List[ColunaOut]


class PeriodoIn(Schema):
    ano: int
    mes: int


class PeriodoResumo(Schema):
    id: str
    ano: int
    mes: int


class LinhaIn(Schema):
    label: str
    ordem: int = 0


class CelulaOut(Schema):
    coluna_id: str
    valor: Optional[str]
    atualizado_em: Optional[datetime]


class LinhaOut(Schema):
    id: str
    label: str
    ordem: int
    celulas: List[CelulaOut]


class PeriodoOut(Schema):
    id: str
    ano: int
    mes: int
    colunas: List[ColunaOut]
    linhas: List[LinhaOut]


class MinhaPlanilhaOut(Schema):
    config: ConfigOut
    periodos: List[PeriodoResumo]


class CelulaIn(Schema):
    linha_id: str
    coluna_id: str
    valor: Optional[str] = None


# ── Helpers ───────────────────────────────────────────────────────────────────

def _coluna_out(col):
    return {
        'id': str(col.id),
        'nome': col.nome,
        'tipo': col.tipo,
        'ordem': col.ordem,
        'prazo_dias': col.prazo_dias,
        'obrigatorio': col.obrigatorio,
    }


def _config_out(config):
    return {
        'id': str(config.id),
        'nome': config.nome,
        'funcionario_id': str(config.funcionario_id),
        'funcionario_nome': config.funcionario.name,
        'colunas': [_coluna_out(c) for c in config.colunas.all()],
    }


def _linha_out(linha):
    return {
        'id': str(linha.id),
        'label': linha.label,
        'ordem': linha.ordem,
        'celulas': [
            {
                'coluna_id': str(c.coluna_id),
                'valor': c.valor,
                'atualizado_em': c.atualizado_em,
            }
            for c in linha.celulas.all()
        ],
    }


def _periodo_out(periodo):
    return {
        'id': str(periodo.id),
        'ano': periodo.ano,
        'mes': periodo.mes,
        'colunas': [_coluna_out(c) for c in periodo.config.colunas.all()],
        'linhas': [_linha_out(l) for l in periodo.linhas.prefetch_related('celulas').all()],
    }


# ── Usuários ──────────────────────────────────────────────────────────────────

@planilha_router.get("/usuarios", response=List[UserOut])
def listar_usuarios(request):
    _require_admin(request.auth)
    users = User.objects.filter(is_active=True).order_by('name')
    return [{'id': str(u.id), 'nome': u.name, 'email': u.email} for u in users]


# ── Configs ───────────────────────────────────────────────────────────────────

@planilha_router.get("/configs", response=List[ConfigOut])
def listar_configs(request):
    _require_admin(request.auth)
    configs = (
        PlanilhaFuncionarioConfig.objects
        .select_related('funcionario')
        .prefetch_related('colunas')
        .all()
    )
    return [_config_out(c) for c in configs]


@planilha_router.post("/configs", response=ConfigOut)
def criar_config(request, payload: ConfigIn):
    _require_admin(request.auth)
    try:
        user = User.objects.get(id=payload.funcionario_id)
    except User.DoesNotExist:
        raise HttpError(404, "Usuário não encontrado")
    if PlanilhaFuncionarioConfig.objects.filter(funcionario=user).exists():
        raise HttpError(400, "Este funcionário já possui uma planilha")
    config = PlanilhaFuncionarioConfig.objects.create(funcionario=user, nome=payload.nome)
    config.refresh_from_db()
    return _config_out(config)


@planilha_router.put("/configs/{config_id}", response=ConfigOut)
def atualizar_config(request, config_id: str, payload: ConfigIn):
    _require_admin(request.auth)
    try:
        config = (
            PlanilhaFuncionarioConfig.objects
            .select_related('funcionario')
            .prefetch_related('colunas')
            .get(id=config_id)
        )
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    config.nome = payload.nome
    config.save()
    return _config_out(config)


@planilha_router.delete("/configs/{config_id}")
def deletar_config(request, config_id: str):
    _require_admin(request.auth)
    try:
        PlanilhaFuncionarioConfig.objects.get(id=config_id).delete()
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    return {"ok": True}


# ── Colunas ───────────────────────────────────────────────────────────────────

@planilha_router.post("/configs/{config_id}/colunas", response=ColunaOut)
def adicionar_coluna(request, config_id: str, payload: ColunaIn):
    _require_admin(request.auth)
    try:
        config = PlanilhaFuncionarioConfig.objects.get(id=config_id)
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    col = PlanilhaConfigColuna.objects.create(
        config=config,
        nome=payload.nome,
        tipo=payload.tipo,
        ordem=payload.ordem,
        prazo_dias=payload.prazo_dias,
        obrigatorio=payload.obrigatorio,
    )
    return _coluna_out(col)


@planilha_router.put("/colunas/{coluna_id}", response=ColunaOut)
def atualizar_coluna(request, coluna_id: str, payload: ColunaIn):
    _require_admin(request.auth)
    try:
        col = PlanilhaConfigColuna.objects.get(id=coluna_id)
    except PlanilhaConfigColuna.DoesNotExist:
        raise HttpError(404, "Coluna não encontrada")
    col.nome = payload.nome
    col.tipo = payload.tipo
    col.ordem = payload.ordem
    col.prazo_dias = payload.prazo_dias
    col.obrigatorio = payload.obrigatorio
    col.save()
    return _coluna_out(col)


@planilha_router.delete("/colunas/{coluna_id}")
def deletar_coluna(request, coluna_id: str):
    _require_admin(request.auth)
    try:
        PlanilhaConfigColuna.objects.get(id=coluna_id).delete()
    except PlanilhaConfigColuna.DoesNotExist:
        raise HttpError(404, "Coluna não encontrada")
    return {"ok": True}


# ── Minha planilha ────────────────────────────────────────────────────────────

@planilha_router.get("/minha", response=MinhaPlanilhaOut)
def minha_planilha(request):
    try:
        config = (
            PlanilhaFuncionarioConfig.objects
            .select_related('funcionario')
            .prefetch_related('colunas')
            .get(funcionario=request.auth)
        )
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Planilha_nao_configurada")
    periodos = PlanilhaPeriodo.objects.filter(config=config).order_by('-ano', '-mes')
    return {
        'config': _config_out(config),
        'periodos': [{'id': str(p.id), 'ano': p.ano, 'mes': p.mes} for p in periodos],
    }


# ── Períodos ──────────────────────────────────────────────────────────────────

@planilha_router.get("/configs/{config_id}/periodos", response=List[PeriodoResumo])
def listar_periodos(request, config_id: str):
    user = request.auth
    try:
        config = PlanilhaFuncionarioConfig.objects.get(id=config_id)
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    if not _is_admin(user) and config.funcionario_id != user.id:
        raise HttpError(403, "Acesso negado")
    periodos = PlanilhaPeriodo.objects.filter(config=config).order_by('-ano', '-mes')
    return [{'id': str(p.id), 'ano': p.ano, 'mes': p.mes} for p in periodos]


@planilha_router.post("/configs/{config_id}/periodos", response=PeriodoResumo)
def criar_periodo(request, config_id: str, payload: PeriodoIn):
    _require_admin(request.auth)
    try:
        config = PlanilhaFuncionarioConfig.objects.get(id=config_id)
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    periodo, _ = PlanilhaPeriodo.objects.get_or_create(
        config=config, ano=payload.ano, mes=payload.mes
    )
    return {'id': str(periodo.id), 'ano': periodo.ano, 'mes': periodo.mes}


@planilha_router.get("/periodos/{periodo_id}", response=PeriodoOut)
def get_periodo(request, periodo_id: str):
    user = request.auth
    try:
        periodo = (
            PlanilhaPeriodo.objects
            .select_related('config__funcionario')
            .prefetch_related('config__colunas', 'linhas__celulas')
            .get(id=periodo_id)
        )
    except PlanilhaPeriodo.DoesNotExist:
        raise HttpError(404, "Período não encontrado")
    if not _is_admin(user) and periodo.config.funcionario_id != user.id:
        raise HttpError(403, "Acesso negado")
    return _periodo_out(periodo)


# ── Linhas ────────────────────────────────────────────────────────────────────

@planilha_router.post("/periodos/{periodo_id}/linhas", response=LinhaOut)
def adicionar_linha(request, periodo_id: str, payload: LinhaIn):
    _require_admin(request.auth)
    try:
        periodo = PlanilhaPeriodo.objects.get(id=periodo_id)
    except PlanilhaPeriodo.DoesNotExist:
        raise HttpError(404, "Período não encontrado")
    linha = PlanilhaLinha.objects.create(
        periodo=periodo, label=payload.label, ordem=payload.ordem
    )
    return _linha_out(linha)


@planilha_router.put("/linhas/{linha_id}", response=LinhaOut)
def atualizar_linha(request, linha_id: str, payload: LinhaIn):
    _require_admin(request.auth)
    try:
        linha = PlanilhaLinha.objects.prefetch_related('celulas').get(id=linha_id)
    except PlanilhaLinha.DoesNotExist:
        raise HttpError(404, "Linha não encontrada")
    linha.label = payload.label
    linha.ordem = payload.ordem
    linha.save()
    return _linha_out(linha)


@planilha_router.delete("/linhas/{linha_id}")
def deletar_linha(request, linha_id: str):
    _require_admin(request.auth)
    try:
        PlanilhaLinha.objects.get(id=linha_id).delete()
    except PlanilhaLinha.DoesNotExist:
        raise HttpError(404, "Linha não encontrada")
    return {"ok": True}


# ── Células ───────────────────────────────────────────────────────────────────

@planilha_router.put("/celulas", response=CelulaOut)
def upsert_celula(request, payload: CelulaIn):
    user = request.auth
    try:
        linha = PlanilhaLinha.objects.select_related('periodo__config').get(id=payload.linha_id)
    except PlanilhaLinha.DoesNotExist:
        raise HttpError(404, "Linha não encontrada")
    if not _is_admin(user) and linha.periodo.config.funcionario_id != user.id:
        raise HttpError(403, "Acesso negado")
    try:
        coluna = PlanilhaConfigColuna.objects.get(id=payload.coluna_id)
    except PlanilhaConfigColuna.DoesNotExist:
        raise HttpError(404, "Coluna não encontrada")
    celula, _ = PlanilhaCelula.objects.update_or_create(
        linha=linha,
        coluna=coluna,
        defaults={'valor': payload.valor, 'atualizado_por': user},
    )
    return {
        'coluna_id': str(celula.coluna_id),
        'valor': celula.valor,
        'atualizado_em': celula.atualizado_em,
    }
