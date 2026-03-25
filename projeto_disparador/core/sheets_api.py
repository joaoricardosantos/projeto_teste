"""
API para integração com Google Sheets.
Endpoints para dashboards financeiros em tempo real.
"""

from typing import List, Optional
from ninja import Router, Schema
from ninja.errors import HttpError
from pydantic import Field
from core.auth import JWTAuth
from core.models import SheetSetor

# Importa o serviço (ajustar path conforme estrutura)
from core.sheets_service import (
    verificar_conexao,
    buscar_dados_planilha,
    buscar_multiplas_abas,
    listar_abas,
    processar_dados_financeiros,
    processar_fluxo_caixa,
    processar_cobrancas_pratika,
    processar_advocacia,
    processar_despesas_unidade,
    get_planilhas_configuradas,
)


sheets_router = Router(auth=JWTAuth(), tags=["Google Sheets"])


# ── Schemas de Setor ─────────────────────────────────────────────────────────

class SetorOut(Schema):
    id: int
    nome: str
    spreadsheet_id: str
    aba: str
    tipo_dashboard: str
    grupo: str = ""
    ativo: bool


class SetorIn(Schema):
    nome: str
    spreadsheet_id: str
    aba: str = "Sheet1"
    tipo_dashboard: str = "cobrancas"
    grupo: str = ""
    ativo: bool = True


# ── Endpoints de Setor ───────────────────────────────────────────────────────

@sheets_router.get("/setores", response=List[SetorOut])
def listar_setores(request):
    return list(SheetSetor.objects.filter(ativo=True))


@sheets_router.post("/setores", response=SetorOut)
def criar_setor(request, payload: SetorIn):
    setor = SheetSetor.objects.create(**payload.dict())
    return setor


@sheets_router.put("/setores/{setor_id}", response=SetorOut)
def atualizar_setor(request, setor_id: int, payload: SetorIn):
    try:
        setor = SheetSetor.objects.get(id=setor_id)
    except SheetSetor.DoesNotExist:
        raise HttpError(404, "Setor não encontrado")
    for attr, value in payload.dict().items():
        setattr(setor, attr, value)
    setor.save()
    return setor


@sheets_router.delete("/setores/{setor_id}")
def deletar_setor(request, setor_id: int):
    try:
        setor = SheetSetor.objects.get(id=setor_id)
    except SheetSetor.DoesNotExist:
        raise HttpError(404, "Setor não encontrado")
    setor.delete()
    return {"ok": True}


# ── Schemas ──────────────────────────────────────────────────────────────────

class StatusConexaoOut(Schema):
    conectado: bool
    service_account: Optional[str] = None
    erro: Optional[str] = None


class AbaOut(Schema):
    id: int
    title: str
    index: int


class PlanilhaConfigOut(Schema):
    id: str
    nome: str
    tipo: str
    range: Optional[str] = None


class ResumoFinanceiroOut(Schema):
    total_receitas: float
    total_despesas: float
    saldo: float
    total_transacoes: int


class CategoriaValoresOut(Schema):
    receitas: float
    despesas: float


class MesValoresOut(Schema):
    mes: str
    receitas: float
    despesas: float
    saldo: float


class TransacaoOut(Schema):
    data: str
    descricao: str
    categoria: str
    valor: float
    tipo: str


class DashboardFinanceiroOut(Schema):
    resumo: ResumoFinanceiroOut
    por_categoria: dict
    por_mes: List[MesValoresOut]
    ultimas_transacoes: List[TransacaoOut]
    atualizado_em: str


class FluxoItemOut(Schema):
    data: str
    entradas: float
    saidas: float
    saldo_dia: float
    saldo_acumulado: float


class FluxoCaixaOut(Schema):
    fluxo: List[FluxoItemOut]
    saldo_final: float
    atualizado_em: str


class BuscarDadosIn(Schema):
    spreadsheet_id: str
    range_name: str
    use_cache: bool = True


class ConfiguracaoColunas(Schema):
    col_data: int = 0
    col_descricao: int = 1
    col_categoria: int = 2
    col_valor: int = 3
    col_tipo: int = 4
    tem_cabecalho: bool = True


class ProcessarFinanceiroIn(Schema):
    spreadsheet_id: str
    range_name: str
    colunas: Optional[ConfiguracaoColunas] = None
    use_cache: bool = True


# ── Endpoints ────────────────────────────────────────────────────────────────

@sheets_router.get("/status", response=StatusConexaoOut)
def status_conexao(request):
    """
    Verifica status da conexão com Google Sheets API.
    """
    return verificar_conexao()


@sheets_router.get("/planilhas", response=List[PlanilhaConfigOut])
def listar_planilhas_configuradas(request):
    """
    Lista planilhas configuradas no sistema.
    """
    return get_planilhas_configuradas()


@sheets_router.get("/planilha/{spreadsheet_id}/abas", response=List[AbaOut])
def listar_abas_planilha(request, spreadsheet_id: str):
    """
    Lista todas as abas de uma planilha específica.
    """
    try:
        return listar_abas(spreadsheet_id)
    except Exception as e:
        raise HttpError(400, str(e))


@sheets_router.post("/dados")
def buscar_dados(request, payload: BuscarDadosIn):
    """
    Busca dados brutos de uma planilha.
    Retorna lista de linhas.
    """
    try:
        dados = buscar_dados_planilha(
            payload.spreadsheet_id,
            payload.range_name,
            payload.use_cache
        )
        return {
            "total_linhas": len(dados),
            "cabecalho": dados[0] if dados else [],
            "dados": dados[1:] if len(dados) > 1 else [],
        }
    except Exception as e:
        raise HttpError(400, str(e))


@sheets_router.post("/dashboard/financeiro", response=DashboardFinanceiroOut)
def dashboard_financeiro(request, payload: ProcessarFinanceiroIn):
    """
    Processa dados financeiros e retorna dashboard completo.
    
    Espera planilha com colunas: Data, Descrição, Categoria, Valor, Tipo
    O campo Tipo deve conter "Receita" ou "Despesa" (ou valor positivo/negativo).
    """
    try:
        dados = buscar_dados_planilha(
            payload.spreadsheet_id,
            payload.range_name,
            payload.use_cache
        )
        
        if not dados:
            raise HttpError(404, "Planilha vazia ou range inválido")
        
        colunas = payload.colunas or ConfiguracaoColunas()
        
        resultado = processar_dados_financeiros(
            dados,
            col_data=colunas.col_data,
            col_descricao=colunas.col_descricao,
            col_categoria=colunas.col_categoria,
            col_valor=colunas.col_valor,
            col_tipo=colunas.col_tipo,
            tem_cabecalho=colunas.tem_cabecalho,
        )
        
        return resultado
    
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, str(e))


@sheets_router.post("/dashboard/fluxo-caixa", response=FluxoCaixaOut)
def dashboard_fluxo_caixa(request, payload: ProcessarFinanceiroIn):
    """
    Processa dados de fluxo de caixa.
    
    Espera planilha com colunas: Data, Valor, Tipo
    """
    try:
        dados = buscar_dados_planilha(
            payload.spreadsheet_id,
            payload.range_name,
            payload.use_cache
        )
        
        if not dados:
            raise HttpError(404, "Planilha vazia ou range inválido")
        
        colunas = payload.colunas or ConfiguracaoColunas()
        
        resultado = processar_fluxo_caixa(
            dados,
            col_data=colunas.col_data,
            col_valor=colunas.col_valor,
            col_tipo=colunas.col_tipo,
            tem_cabecalho=colunas.tem_cabecalho,
        )
        
        return resultado
    
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, str(e))


@sheets_router.get("/dashboard/rapido/{spreadsheet_id}")
def dashboard_rapido(request, spreadsheet_id: str, aba: str = "Dados", force: bool = False):
    """
    Endpoint simplificado para dashboard rápido.
    Tenta detectar automaticamente as colunas.
    
    Query params:
    - aba: Nome da aba (padrão: "Dados")
    - force: Se True, ignora cache
    """
    try:
        range_name = f"'{aba}'!A:Z"
        dados = buscar_dados_planilha(spreadsheet_id, range_name, use_cache=not force)
        
        if not dados:
            raise HttpError(404, "Planilha vazia")
        
        # Tenta detectar colunas pelo cabeçalho
        cabecalho = [str(c).lower() for c in dados[0]] if dados else []
        
        # Mapeamento comum de nomes de colunas
        mapa_colunas = {
            "data": ["data", "date", "dt", "vencimento"],
            "descricao": ["descricao", "descrição", "desc", "historico", "histórico"],
            "categoria": ["categoria", "tipo", "category", "class", "classe"],
            "valor": ["valor", "value", "vlr", "total", "montante", "quantia"],
            "tipo_mov": ["movimento", "mov", "tipo_mov", "natureza", "credito_debito"],
        }
        
        def encontrar_coluna(nomes: List[str], default: int) -> int:
            for nome in nomes:
                for i, col in enumerate(cabecalho):
                    if nome in col:
                        return i
            return default
        
        col_data = encontrar_coluna(mapa_colunas["data"], 0)
        col_descricao = encontrar_coluna(mapa_colunas["descricao"], 1)
        col_categoria = encontrar_coluna(mapa_colunas["categoria"], 2)
        col_valor = encontrar_coluna(mapa_colunas["valor"], 3)
        col_tipo = encontrar_coluna(mapa_colunas["tipo_mov"], 4)
        
        resultado = processar_dados_financeiros(
            dados,
            col_data=col_data,
            col_descricao=col_descricao,
            col_categoria=col_categoria,
            col_valor=col_valor,
            col_tipo=col_tipo,
            tem_cabecalho=True,
        )
        
        resultado["colunas_detectadas"] = {
            "data": col_data,
            "descricao": col_descricao,
            "categoria": col_categoria,
            "valor": col_valor,
            "tipo": col_tipo,
        }
        resultado["cabecalho_original"] = dados[0] if dados else []
        
        return resultado
    
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, str(e))


@sheets_router.get("/dashboard/cobrancas/{spreadsheet_id}")
def dashboard_cobrancas(request, spreadsheet_id: str, aba: str = "Sheet1", force: bool = False):
    """
    Dashboard de cobrança no formato Pratika (multi-bloco de vencimentos).
    """
    try:
        range_name = f"'{aba}'!A:O"
        dados = buscar_dados_planilha(spreadsheet_id, range_name, use_cache=not force)
        if not dados:
            raise HttpError(404, "Planilha vazia")
        return processar_cobrancas_pratika(dados)
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, str(e))


@sheets_router.get("/dashboard/advocacia/{spreadsheet_id}")
def dashboard_advocacia(request, spreadsheet_id: str, aba: str = "Sheet1", force: bool = False):
    """
    Dashboard de honorários advocatícios.
    """
    try:
        range_name = f"'{aba}'!A:K"
        dados = buscar_dados_planilha(spreadsheet_id, range_name, use_cache=not force)
        if not dados:
            raise HttpError(404, "Planilha vazia")
        return processar_advocacia(dados)
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, str(e))


@sheets_router.get("/dashboard/despesas/{spreadsheet_id}")
def dashboard_despesas(request, spreadsheet_id: str, aba: str = "Sheet1", force: bool = False):
    """
    Dashboard de despesas por unidade.
    """
    try:
        range_name = f"'{aba}'!A:C"
        dados = buscar_dados_planilha(spreadsheet_id, range_name, use_cache=not force)
        if not dados:
            raise HttpError(404, "Planilha vazia")
        return processar_despesas_unidade(dados)
    except HttpError:
        raise
    except Exception as e:
        raise HttpError(400, str(e))


@sheets_router.get("/preview/{spreadsheet_id}")
def preview_planilha(request, spreadsheet_id: str, aba: str = "Sheet1", linhas: int = 10):
    """
    Preview dos primeiros dados de uma planilha para configuração.
    """
    try:
        range_name = f"'{aba}'!A1:Z{linhas + 1}"
        dados = buscar_dados_planilha(spreadsheet_id, range_name, use_cache=False)
        
        if not dados:
            return {"cabecalho": [], "preview": [], "total_colunas": 0}
        
        return {
            "cabecalho": dados[0] if dados else [],
            "preview": dados[1:] if len(dados) > 1 else [],
            "total_colunas": len(dados[0]) if dados else 0,
        }
    
    except Exception as e:
        raise HttpError(400, str(e))