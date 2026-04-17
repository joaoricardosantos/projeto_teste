from typing import List, Optional

from ninja import Router, Schema
from ninja.errors import HttpError

from core.auth import JWTAuth
from core.models import User, PlanilhaFuncionarioConfig, PlanilhaColunaRegra
from core.sheets_service import buscar_dados_planilha, listar_abas

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


class RegraIn(Schema):
    coluna_nome: str
    tipo: str = 'texto'
    prazo_dias: Optional[int] = None


class RegraOut(Schema):
    id: str
    coluna_nome: str
    tipo: str
    prazo_dias: Optional[int]


class ConfigIn(Schema):
    funcionario_id: str
    nome: str
    spreadsheet_id: str = ''
    linha_cabecalho: int = 1
    linha_dados_inicio: int = 2
    coluna_label_indice: int = 0


class ConfigOut(Schema):
    id: str
    nome: str
    funcionario_id: str
    funcionario_nome: str
    spreadsheet_id: str
    linha_cabecalho: int
    linha_dados_inicio: int
    coluna_label_indice: int
    regras: List[RegraOut]


class AbaOut(Schema):
    id: int
    title: str
    index: int


class CelulaOut(Schema):
    valor: str
    status: str   # 'success' | 'error' | 'warning' | 'pending' | 'none'


class LinhaOut(Schema):
    label: str
    celulas: List[CelulaOut]


class DadosPlanilhaOut(Schema):
    config_id: str
    aba: str
    colunas: List[str]       # headers excluindo a coluna label
    linhas: List[LinhaOut]
    atualizado_em: str


# ── Helpers ───────────────────────────────────────────────────────────────────

def _regra_out(r):
    return {'id': str(r.id), 'coluna_nome': r.coluna_nome, 'tipo': r.tipo, 'prazo_dias': r.prazo_dias}


def _config_out(config):
    return {
        'id': str(config.id),
        'nome': config.nome,
        'funcionario_id': str(config.funcionario_id),
        'funcionario_nome': config.funcionario.name,
        'spreadsheet_id': config.spreadsheet_id,
        'linha_cabecalho': config.linha_cabecalho,
        'linha_dados_inicio': config.linha_dados_inicio,
        'coluna_label_indice': config.coluna_label_indice,
        'regras': [_regra_out(r) for r in config.regras.all()],
    }


def _cell_status(valor: str, regra, aba_nome: str) -> str:
    """
    Calcula status de cor para uma célula baseado na regra e no mês da aba.
    Tenta extrair mês/ano do nome da aba (ex: 'EMISSÃO NOVEMBRO 2025').
    Fallback: usa data atual como referência de período.
    """
    if not regra or not regra.prazo_dias:
        return 'none'

    from datetime import date
    import re

    _MESES = {
        'janeiro': 1, 'fevereiro': 2, 'março': 3, 'abril': 4,
        'maio': 5, 'junho': 6, 'julho': 7, 'agosto': 8,
        'setembro': 9, 'outubro': 10, 'novembro': 11, 'dezembro': 12,
    }

    # Tenta extrair mês do nome da aba
    periodo_inicio = None
    aba_lower = aba_nome.lower()
    for nome_mes, num_mes in _MESES.items():
        if nome_mes in aba_lower:
            # Tenta encontrar ano no nome da aba
            match_ano = re.search(r'\b(20\d{2})\b', aba_nome)
            ano = int(match_ano.group(1)) if match_ano else date.today().year
            periodo_inicio = date(ano, num_mes, 1)
            break

    if not periodo_inicio:
        hoje = date.today()
        periodo_inicio = date(hoje.year, hoje.month, 1)

    from datetime import timedelta
    deadline = periodo_inicio + timedelta(days=regra.prazo_dias)
    hoje = date.today()

    is_preenchido = bool(valor and valor.strip() and valor.strip().lower() not in ('0', 'none', ''))
    if is_preenchido:
        return 'success'
    if hoje > deadline:
        return 'error'
    warn = deadline - timedelta(days=2)
    if hoje >= warn:
        return 'warning'
    return 'pending'


# ── Usuários (para select no admin) ──────────────────────────────────────────

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
        .prefetch_related('regras')
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
    config = PlanilhaFuncionarioConfig.objects.create(
        funcionario=user,
        nome=payload.nome,
        spreadsheet_id=payload.spreadsheet_id,
        linha_cabecalho=payload.linha_cabecalho,
        linha_dados_inicio=payload.linha_dados_inicio,
        coluna_label_indice=payload.coluna_label_indice,
    )
    return _config_out(config)


@planilha_router.put("/configs/{config_id}", response=ConfigOut)
def atualizar_config(request, config_id: str, payload: ConfigIn):
    _require_admin(request.auth)
    try:
        config = (
            PlanilhaFuncionarioConfig.objects
            .select_related('funcionario')
            .prefetch_related('regras')
            .get(id=config_id)
        )
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    config.nome = payload.nome
    config.spreadsheet_id = payload.spreadsheet_id
    config.linha_cabecalho = payload.linha_cabecalho
    config.linha_dados_inicio = payload.linha_dados_inicio
    config.coluna_label_indice = payload.coluna_label_indice
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


# ── Regras de coluna ──────────────────────────────────────────────────────────

@planilha_router.post("/configs/{config_id}/regras", response=RegraOut)
def adicionar_regra(request, config_id: str, payload: RegraIn):
    _require_admin(request.auth)
    try:
        config = PlanilhaFuncionarioConfig.objects.get(id=config_id)
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    regra = PlanilhaColunaRegra.objects.create(
        config=config,
        coluna_nome=payload.coluna_nome,
        tipo=payload.tipo,
        prazo_dias=payload.prazo_dias,
    )
    return _regra_out(regra)


@planilha_router.put("/regras/{regra_id}", response=RegraOut)
def atualizar_regra(request, regra_id: str, payload: RegraIn):
    _require_admin(request.auth)
    try:
        regra = PlanilhaColunaRegra.objects.get(id=regra_id)
    except PlanilhaColunaRegra.DoesNotExist:
        raise HttpError(404, "Regra não encontrada")
    regra.coluna_nome = payload.coluna_nome
    regra.tipo = payload.tipo
    regra.prazo_dias = payload.prazo_dias
    regra.save()
    return _regra_out(regra)


@planilha_router.delete("/regras/{regra_id}")
def deletar_regra(request, regra_id: str):
    _require_admin(request.auth)
    try:
        PlanilhaColunaRegra.objects.get(id=regra_id).delete()
    except PlanilhaColunaRegra.DoesNotExist:
        raise HttpError(404, "Regra não encontrada")
    return {"ok": True}


# ── Dados da planilha (lê do Google Sheets) ───────────────────────────────────

@planilha_router.get("/minha", response=ConfigOut)
def minha_config(request):
    try:
        config = (
            PlanilhaFuncionarioConfig.objects
            .select_related('funcionario')
            .prefetch_related('regras')
            .get(funcionario=request.auth)
        )
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Planilha_nao_configurada")
    return _config_out(config)


@planilha_router.get("/configs/{config_id}/abas", response=List[AbaOut])
def listar_abas_planilha(request, config_id: str):
    user = request.auth
    try:
        config = PlanilhaFuncionarioConfig.objects.get(id=config_id)
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    if not _is_admin(user) and config.funcionario_id != user.id:
        raise HttpError(403, "Acesso negado")
    if not config.spreadsheet_id:
        raise HttpError(400, "Planilha não configurada (sem spreadsheet_id)")
    try:
        abas = listar_abas(config.spreadsheet_id)
    except Exception as e:
        raise HttpError(502, str(e))
    return abas


@planilha_router.get("/configs/{config_id}/dados", response=DadosPlanilhaOut)
def dados_planilha(request, config_id: str, aba: str):
    from datetime import datetime

    user = request.auth
    try:
        config = (
            PlanilhaFuncionarioConfig.objects
            .prefetch_related('regras')
            .get(id=config_id)
        )
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    if not _is_admin(user) and config.funcionario_id != user.id:
        raise HttpError(403, "Acesso negado")
    if not config.spreadsheet_id:
        raise HttpError(400, "Planilha não configurada")

    try:
        raw = buscar_dados_planilha(config.spreadsheet_id, aba, use_cache=False)
    except Exception as e:
        raise HttpError(502, str(e))

    if not raw:
        return {
            'config_id': str(config.id),
            'aba': aba,
            'colunas': [],
            'linhas': [],
            'atualizado_em': datetime.now().strftime('%d/%m/%Y %H:%M'),
        }

    # Identifica linha de cabeçalho e dados
    cab_idx = config.linha_cabecalho - 1       # 0-based
    dados_idx = config.linha_dados_inicio - 1  # 0-based
    label_col = config.coluna_label_indice

    headers_row = raw[cab_idx] if cab_idx < len(raw) else []
    # Normaliza headers (remove espaços)
    headers = [str(h).strip() for h in headers_row]

    # Índices das colunas que NÃO são o label
    col_indices = [i for i in range(len(headers)) if i != label_col]
    colunas = [headers[i] for i in col_indices]

    # Monta mapa coluna_nome → regra
    regras_map = {r.coluna_nome.strip(): r for r in config.regras.all()}

    linhas_out = []
    for row in raw[dados_idx:]:
        if not row:
            continue
        label = str(row[label_col]).strip() if label_col < len(row) else ''
        if not label:
            continue

        celulas = []
        for ci in col_indices:
            valor = str(row[ci]).strip() if ci < len(row) else ''
            col_nome = headers[ci] if ci < len(headers) else ''
            regra = regras_map.get(col_nome)
            status = _cell_status(valor, regra, aba)
            celulas.append({'valor': valor, 'status': status})

        linhas_out.append({'label': label, 'celulas': celulas})

    return {
        'config_id': str(config.id),
        'aba': aba,
        'colunas': colunas,
        'linhas': linhas_out,
        'atualizado_em': datetime.now().strftime('%d/%m/%Y %H:%M'),
    }
