from datetime import date, datetime, timedelta
from typing import List, Optional, Any

from ninja import Router, Schema
from ninja.errors import HttpError

from core.auth import JWTAuth
from core.models import User, PlanilhaFuncionarioConfig
from core.sheets_service import buscar_dados_planilha, listar_abas

planilha_router = Router(auth=JWTAuth(), tags=["Planilhas"])

# ── Nomes exatos das colunas na planilha ──────────────────────────────────────
_COL_CONDOMINIO        = 'CONDOMÍNIO'
_COL_PRAZO_PRESTACAO   = 'PRAZO DE RECEBIMENTO DA PRESTAÇÃO'
_COL_OK_PRESTACAO      = 'OK DA PRESTAÇÃO DE CONTAS'
_COL_RECEB_AGUA        = 'RECEBIMENTO DO RELATÓRIO DE ÁGUA'
_COL_RECEB_GAS         = 'RECEBIMENTO DO RELATÓRIO DE GÁS'
_COL_RECEB_RESERVAS    = 'RECEBIMENTO DO RELATÓRIO DE RESERVAS'
_COL_PRAZO_BOLETO      = 'PRAZO PARA GERAR BOLETO'
_COL_GERACAO_BOLETO    = 'GERAÇÃO DO BOLETO'
_COL_EMAIL             = 'ENVIADO POR E-MAIL'
_COL_IMPRESSO          = 'IMPRESSO NA PRATIKA'
_COL_GRAFICA           = 'ENVIADO PARA A GRÁFICA'
_COL_RETORNO_GRAFICA   = 'RETORNO DA GRÁFICA'


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


class ConfigIn(Schema):
    funcionario_id: str
    nome: str
    spreadsheet_id: str = ''


class ConfigOut(Schema):
    id: str
    nome: str
    funcionario_id: str
    funcionario_nome: str
    spreadsheet_id: str


class AbaOut(Schema):
    id: int
    title: str
    index: int


class CelulaOut(Schema):
    valor: str
    status: str   # 'success' | 'error' | 'warning' | 'pending' | 'none'


class LinhaOut(Schema):
    condominio: str
    prazo_prestacao: str
    ok_prestacao: CelulaOut
    recebimento_agua: CelulaOut
    recebimento_gas: CelulaOut
    recebimento_reservas: CelulaOut
    prazo_boleto: str
    geracao_boleto: CelulaOut
    enviado_email: CelulaOut
    impresso_pratika: CelulaOut
    enviado_grafica: CelulaOut
    retorno_grafica: CelulaOut


class KpiItemOut(Schema):
    total: int
    pendentes: int
    lista: List[str]


class KpiBoletosOut(Schema):
    no_prazo: int
    atrasados: int
    lista_atrasados: List[str]


class KpiRecebimentosOut(Schema):
    agua: KpiItemOut
    gas: KpiItemOut
    reservas: KpiItemOut
    total_pendentes: int


class KpisOut(Schema):
    prestacao: KpiItemOut
    recebimentos: KpiRecebimentosOut
    boletos: KpiBoletosOut


class PipelinePassoOut(Schema):
    label: str
    concluidos: int
    total: int
    pct: float


class ResumoOut(Schema):
    total_condominios: int
    prestacao_pct: float
    recebimentos_pct: float
    boletos_pct: float


class DashboardOut(Schema):
    config_id: str
    aba: str
    resumo: ResumoOut
    pipeline: List[PipelinePassoOut]
    kpis: KpisOut
    linhas: List[LinhaOut]
    atualizado_em: str


# ── Helpers de data e status ──────────────────────────────────────────────────

def _parse_date(s: Any) -> Optional[date]:
    if not s:
        return None
    s = str(s).strip()
    for fmt in ('%d/%m/%Y', '%d/%m/%y', '%d.%m.%Y', '%d.%m.%y', '%Y-%m-%d'):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _preenchido(valor: str) -> bool:
    return bool(valor and valor.strip() and valor.strip().lower() not in ('0', 'none', '-'))


def _status_com_prazo(valor: str, prazo_str: str, hoje: date) -> str:
    """
    Célula cujo prazo de conclusão é informado por outra coluna (ex: PRAZO DE RECEBIMENTO).
    Retorna 'none' se a linha não tiver prazo (ignora).
    """
    prazo = _parse_date(prazo_str)
    if not prazo:
        return 'none'
    if _preenchido(valor):
        return 'success'
    if hoje > prazo:
        return 'error'
    if hoje >= prazo - timedelta(days=2):
        return 'warning'
    return 'pending'


def _prazo_boleto_date(prazo_str: str, ref: date) -> Optional[date]:
    """
    Interpreta o prazo do boleto.
    Aceita data completa OU apenas o dia do mês (ex: '30').
    Quando for só um dia, usa o mês/ano de `ref` (data de geração ou hoje).
    """
    d = _parse_date(prazo_str)
    if d:
        return d
    try:
        import calendar
        dia = int(str(prazo_str).strip())
        if 1 <= dia <= 31:
            ultimo = calendar.monthrange(ref.year, ref.month)[1]
            return date(ref.year, ref.month, min(dia, ultimo))
    except (ValueError, TypeError):
        pass
    return None


def _status_boleto(geracao_str: str, prazo_str: str, hoje: date) -> str:
    geracao = _parse_date(geracao_str)
    ref = geracao or hoje
    prazo = _prazo_boleto_date(prazo_str, ref)
    if not prazo:
        return 'none'
    if geracao:
        return 'success' if geracao <= prazo else 'error'
    if hoje > prazo:
        return 'error'
    if hoje >= prazo - timedelta(days=2):
        return 'warning'
    return 'pending'


def _status_sequencial(valor: str) -> str:
    """Colunas sem prazo fixo: verde se preenchido, none se vazio."""
    return 'success' if _preenchido(valor) else 'none'


def _celula(valor: str, status: str) -> dict:
    return {'valor': valor or '', 'status': status}


# ── Processamento da planilha ─────────────────────────────────────────────────

def _processar_sheet(raw: List[List[Any]], config_id: str, aba: str) -> dict:
    hoje = date.today()

    # Encontra a linha de cabeçalho procurando por 'CONDOMÍNIO'
    header_idx = None
    for i, row in enumerate(raw):
        if any(_COL_CONDOMINIO.upper() in str(c).upper() for c in row):
            header_idx = i
            break

    if header_idx is None:
        return {
            'config_id': config_id, 'aba': aba,
            'resumo': _resumo_vazio(),
            'pipeline': [],
            'kpis': _kpis_vazios(),
            'linhas': [],
            'atualizado_em': datetime.now().strftime('%d/%m/%Y %H:%M'),
        }

    headers = [str(h).strip() for h in raw[header_idx]]
    col = {h.upper(): i for i, h in enumerate(headers)}

    def _get(row, nome):
        idx = col.get(nome.upper())
        if idx is None or idx >= len(row):
            return ''
        return str(row[idx]).strip()

    linhas = []
    kpi_prestacao = {'total': 0, 'pendentes': 0, 'lista': []}
    kpi_agua      = {'total': 0, 'pendentes': 0, 'lista': []}
    kpi_gas       = {'total': 0, 'pendentes': 0, 'lista': []}
    kpi_reservas  = {'total': 0, 'pendentes': 0, 'lista': []}
    kpi_boletos   = {'no_prazo': 0, 'atrasados': 0, 'lista_atrasados': []}

    for row in raw[header_idx + 1:]:
        condominio = _get(row, _COL_CONDOMINIO)
        if not condominio:
            continue

        prazo_prest    = _get(row, _COL_PRAZO_PRESTACAO)
        ok_prest       = _get(row, _COL_OK_PRESTACAO)
        receb_agua     = _get(row, _COL_RECEB_AGUA)
        receb_gas      = _get(row, _COL_RECEB_GAS)
        receb_reservas = _get(row, _COL_RECEB_RESERVAS)
        prazo_boleto   = _get(row, _COL_PRAZO_BOLETO)
        geracao_boleto = _get(row, _COL_GERACAO_BOLETO)
        email          = _get(row, _COL_EMAIL)
        impresso       = _get(row, _COL_IMPRESSO)
        grafica        = _get(row, _COL_GRAFICA)
        retorno        = _get(row, _COL_RETORNO_GRAFICA)

        # Statuses
        st_ok_prest    = _status_com_prazo(ok_prest, prazo_prest, hoje)
        st_agua        = _status_com_prazo(receb_agua, prazo_prest, hoje)
        st_gas         = _status_com_prazo(receb_gas, prazo_prest, hoje)
        st_reservas    = _status_com_prazo(receb_reservas, prazo_prest, hoje)
        st_boleto      = _status_boleto(geracao_boleto, prazo_boleto, hoje)

        # KPI: prestação
        if prazo_prest:
            kpi_prestacao['total'] += 1
            if st_ok_prest == 'error':
                kpi_prestacao['pendentes'] += 1
                kpi_prestacao['lista'].append(condominio)

        # KPI: recebimentos (só conta se tem prazo)
        if prazo_prest:
            kpi_agua['total'] += 1
            if st_agua == 'error':
                kpi_agua['pendentes'] += 1
                kpi_agua['lista'].append(condominio)

            kpi_gas['total'] += 1
            if st_gas == 'error':
                kpi_gas['pendentes'] += 1
                kpi_gas['lista'].append(condominio)

            kpi_reservas['total'] += 1
            if st_reservas == 'error':
                kpi_reservas['pendentes'] += 1
                kpi_reservas['lista'].append(condominio)

        # KPI: boletos
        if prazo_boleto:
            if st_boleto == 'success':
                kpi_boletos['no_prazo'] += 1
            elif st_boleto == 'error':
                kpi_boletos['atrasados'] += 1
                kpi_boletos['lista_atrasados'].append(condominio)

        linhas.append({
            'condominio': condominio,
            'prazo_prestacao': prazo_prest,
            'ok_prestacao': _celula(ok_prest, st_ok_prest),
            'recebimento_agua': _celula(receb_agua, st_agua),
            'recebimento_gas': _celula(receb_gas, st_gas),
            'recebimento_reservas': _celula(receb_reservas, st_reservas),
            'prazo_boleto': prazo_boleto,
            'geracao_boleto': _celula(geracao_boleto, st_boleto),
            'enviado_email': _celula(email, _status_sequencial(email)),
            'impresso_pratika': _celula(impresso, _status_sequencial(impresso)),
            'enviado_grafica': _celula(grafica, _status_sequencial(grafica)),
            'retorno_grafica': _celula(retorno, _status_sequencial(retorno)),
        })

    total_receb_pendentes = (
        kpi_agua['pendentes'] + kpi_gas['pendentes'] + kpi_reservas['pendentes']
    )
    total = len(linhas)

    def _passo(label, campo):
        c = sum(1 for l in linhas if _preenchido(l[campo]['valor']))
        pct = round(c / total * 100, 1) if total else 0.0
        return {'label': label, 'concluidos': c, 'total': total, 'pct': pct}

    pipeline = [
        _passo('Geração',  'geracao_boleto'),
        _passo('E-mail',   'enviado_email'),
        _passo('Impresso', 'impresso_pratika'),
        _passo('Gráfica',  'enviado_grafica'),
        _passo('Retorno',  'retorno_grafica'),
    ]

    def _pct(ok, ttl):
        return round(ok / ttl * 100, 1) if ttl else 0.0

    resumo = {
        'total_condominios': total,
        'prestacao_pct': _pct(
            kpi_prestacao['total'] - kpi_prestacao['pendentes'], kpi_prestacao['total']
        ),
        'recebimentos_pct': _pct(
            sum([
                kpi_agua['total'] - kpi_agua['pendentes'],
                kpi_gas['total'] - kpi_gas['pendentes'],
                kpi_reservas['total'] - kpi_reservas['pendentes'],
            ]),
            kpi_agua['total'] + kpi_gas['total'] + kpi_reservas['total'],
        ),
        'boletos_pct': _pct(kpi_boletos['no_prazo'],
                            kpi_boletos['no_prazo'] + kpi_boletos['atrasados']),
    }

    return {
        'config_id': config_id,
        'aba': aba,
        'resumo': resumo,
        'pipeline': pipeline,
        'kpis': {
            'prestacao': kpi_prestacao,
            'recebimentos': {
                'agua': kpi_agua,
                'gas': kpi_gas,
                'reservas': kpi_reservas,
                'total_pendentes': total_receb_pendentes,
            },
            'boletos': kpi_boletos,
        },
        'linhas': linhas,
        'atualizado_em': datetime.now().strftime('%d/%m/%Y %H:%M'),
    }


def _kpis_vazios():
    vazio = {'total': 0, 'pendentes': 0, 'lista': []}
    return {
        'prestacao': vazio,
        'recebimentos': {
            'agua': vazio, 'gas': vazio, 'reservas': vazio, 'total_pendentes': 0,
        },
        'boletos': {'no_prazo': 0, 'atrasados': 0, 'lista_atrasados': []},
    }


def _resumo_vazio():
    return {'total_condominios': 0, 'prestacao_pct': 0.0, 'recebimentos_pct': 0.0, 'boletos_pct': 0.0}


# ── Endpoints ─────────────────────────────────────────────────────────────────

@planilha_router.get("/usuarios", response=List[UserOut])
def listar_usuarios(request):
    _require_admin(request.auth)
    return [
        {'id': str(u.id), 'nome': u.name, 'email': u.email}
        for u in User.objects.filter(is_active=True).order_by('name')
    ]


@planilha_router.get("/configs", response=List[ConfigOut])
def listar_configs(request):
    _require_admin(request.auth)
    return [
        {
            'id': str(c.id), 'nome': c.nome,
            'funcionario_id': str(c.funcionario_id),
            'funcionario_nome': c.funcionario.name,
            'spreadsheet_id': c.spreadsheet_id,
        }
        for c in PlanilhaFuncionarioConfig.objects.select_related('funcionario').all()
    ]


@planilha_router.post("/configs", response=ConfigOut)
def criar_config(request, payload: ConfigIn):
    _require_admin(request.auth)
    try:
        user = User.objects.get(id=payload.funcionario_id)
    except User.DoesNotExist:
        raise HttpError(404, "Usuário não encontrado")
    if PlanilhaFuncionarioConfig.objects.filter(funcionario=user).exists():
        raise HttpError(400, "Este funcionário já possui uma planilha")
    c = PlanilhaFuncionarioConfig.objects.create(
        funcionario=user, nome=payload.nome, spreadsheet_id=payload.spreadsheet_id,
    )
    return {'id': str(c.id), 'nome': c.nome, 'funcionario_id': str(c.funcionario_id),
            'funcionario_nome': c.funcionario.name, 'spreadsheet_id': c.spreadsheet_id}


@planilha_router.put("/configs/{config_id}", response=ConfigOut)
def atualizar_config(request, config_id: str, payload: ConfigIn):
    _require_admin(request.auth)
    try:
        c = PlanilhaFuncionarioConfig.objects.select_related('funcionario').get(id=config_id)
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    c.nome = payload.nome
    c.spreadsheet_id = payload.spreadsheet_id
    c.save()
    return {'id': str(c.id), 'nome': c.nome, 'funcionario_id': str(c.funcionario_id),
            'funcionario_nome': c.funcionario.name, 'spreadsheet_id': c.spreadsheet_id}


@planilha_router.delete("/configs/{config_id}")
def deletar_config(request, config_id: str):
    _require_admin(request.auth)
    try:
        PlanilhaFuncionarioConfig.objects.get(id=config_id).delete()
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    return {"ok": True}


@planilha_router.get("/minha", response=ConfigOut)
def minha_config(request):
    try:
        c = PlanilhaFuncionarioConfig.objects.select_related('funcionario').get(funcionario=request.auth)
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Planilha_nao_configurada")
    return {'id': str(c.id), 'nome': c.nome, 'funcionario_id': str(c.funcionario_id),
            'funcionario_nome': c.funcionario.name, 'spreadsheet_id': c.spreadsheet_id}


@planilha_router.get("/configs/{config_id}/abas", response=List[AbaOut])
def listar_abas_planilha(request, config_id: str):
    user = request.auth
    try:
        c = PlanilhaFuncionarioConfig.objects.get(id=config_id)
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    if not _is_admin(user) and c.funcionario_id != user.id:
        raise HttpError(403, "Acesso negado")
    if not c.spreadsheet_id:
        raise HttpError(400, "Planilha sem spreadsheet_id configurado")
    try:
        return listar_abas(c.spreadsheet_id)
    except Exception as e:
        raise HttpError(502, str(e))


@planilha_router.get("/configs/{config_id}/dashboard", response=DashboardOut)
def get_dashboard(request, config_id: str, aba: str):
    user = request.auth
    try:
        c = PlanilhaFuncionarioConfig.objects.get(id=config_id)
    except PlanilhaFuncionarioConfig.DoesNotExist:
        raise HttpError(404, "Config não encontrada")
    if not _is_admin(user) and c.funcionario_id != user.id:
        raise HttpError(403, "Acesso negado")
    if not c.spreadsheet_id:
        raise HttpError(400, "Planilha sem spreadsheet_id configurado")
    try:
        raw = buscar_dados_planilha(c.spreadsheet_id, aba, use_cache=False)
    except Exception as e:
        raise HttpError(502, str(e))
    return _processar_sheet(raw, str(c.id), aba)
