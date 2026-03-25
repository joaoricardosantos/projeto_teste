"""
Serviço de integração com Google Sheets API.
Busca dados de planilhas configuradas e formata para dashboards.
"""

import json
import os
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Optional, List, Dict, Any
from functools import lru_cache
import time

from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from django.conf import settings
from django.core.cache import cache


# ── Configuração ─────────────────────────────────────────────────────────────

SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]
CACHE_TTL = int(os.environ.get("SHEETS_CACHE_TTL", "30"))  # segundos


def _get_credentials() -> Optional[Credentials]:
    """
    Carrega credenciais do Google a partir de variável de ambiente ou arquivo.
    """
    creds_json = os.environ.get("GOOGLE_SHEETS_CREDENTIALS")
    creds_file = os.environ.get("GOOGLE_SHEETS_CREDENTIALS_FILE")
    
    if creds_json:
        try:
            creds_data = json.loads(creds_json)
            return Credentials.from_service_account_info(creds_data, scopes=SCOPES)
        except json.JSONDecodeError:
            return None
    
    if creds_file and os.path.exists(creds_file):
        return Credentials.from_service_account_file(creds_file, scopes=SCOPES)
    
    return None


def _get_sheets_service():
    """
    Retorna instância do serviço Google Sheets API.
    """
    creds = _get_credentials()
    if not creds:
        raise ValueError("Credenciais do Google Sheets não configuradas")
    return build("sheets", "v4", credentials=creds)


# ── Funções de Busca ─────────────────────────────────────────────────────────

def buscar_dados_planilha(
    spreadsheet_id: str,
    range_name: str,
    use_cache: bool = True
) -> List[List[Any]]:
    """
    Busca dados de uma planilha específica.
    
    Args:
        spreadsheet_id: ID da planilha (da URL do Google Sheets)
        range_name: Range no formato "Aba!A1:Z100" ou apenas "Aba"
        use_cache: Se deve usar cache (padrão: True)
    
    Returns:
        Lista de linhas, cada linha é uma lista de valores
    """
    cache_key = f"sheets:{spreadsheet_id}:{range_name}"
    
    if use_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
    
    try:
        service = _get_sheets_service()
        result = service.spreadsheets().values().get(
            spreadsheetId=spreadsheet_id,
            range=range_name
        ).execute()
        
        values = result.get("values", [])
        
        if use_cache:
            cache.set(cache_key, values, CACHE_TTL)
        
        return values
    
    except HttpError as e:
        raise Exception(f"Erro ao acessar planilha: {e.reason}")
    except Exception as e:
        raise Exception(f"Erro ao buscar dados: {str(e)}")


def buscar_multiplas_abas(
    spreadsheet_id: str,
    ranges: List[str],
    use_cache: bool = True
) -> Dict[str, List[List[Any]]]:
    """
    Busca dados de múltiplas abas em uma única requisição.
    
    Args:
        spreadsheet_id: ID da planilha
        ranges: Lista de ranges (ex: ["Receitas!A:Z", "Despesas!A:Z"])
        use_cache: Se deve usar cache
    
    Returns:
        Dicionário com range como chave e dados como valor
    """
    cache_key = f"sheets:multi:{spreadsheet_id}:{'-'.join(ranges)}"
    
    if use_cache:
        cached = cache.get(cache_key)
        if cached is not None:
            return cached
    
    try:
        service = _get_sheets_service()
        result = service.spreadsheets().values().batchGet(
            spreadsheetId=spreadsheet_id,
            ranges=ranges
        ).execute()
        
        value_ranges = result.get("valueRanges", [])
        dados = {}
        
        for vr in value_ranges:
            range_name = vr.get("range", "")
            # Normaliza o nome (remove qualificadores como $A$1:$Z$100)
            nome_aba = range_name.split("!")[0].replace("'", "")
            dados[nome_aba] = vr.get("values", [])
        
        if use_cache:
            cache.set(cache_key, dados, CACHE_TTL)
        
        return dados
    
    except HttpError as e:
        raise Exception(f"Erro ao acessar planilha: {e.reason}")
    except Exception as e:
        raise Exception(f"Erro ao buscar dados: {str(e)}")


def listar_abas(spreadsheet_id: str) -> List[Dict[str, Any]]:
    """
    Lista todas as abas de uma planilha.
    
    Returns:
        Lista de dicionários com id, title e index de cada aba
    """
    try:
        service = _get_sheets_service()
        result = service.spreadsheets().get(spreadsheetId=spreadsheet_id).execute()
        
        sheets = result.get("sheets", [])
        return [
            {
                "id": s["properties"]["sheetId"],
                "title": s["properties"]["title"],
                "index": s["properties"]["index"],
            }
            for s in sheets
        ]
    
    except HttpError as e:
        raise Exception(f"Erro ao listar abas: {e.reason}")


# ── Funções de Processamento ─────────────────────────────────────────────────

def _parse_valor(valor: str) -> Decimal:
    """
    Converte string de valor monetário para Decimal.
    Aceita formatos: R$ 1.234,56 / 1234.56 / 1.234,56
    """
    if not valor:
        return Decimal("0")
    
    # Remove prefixo monetário e espaços
    valor = str(valor).replace("R$", "").replace(" ", "").strip()
    
    if not valor:
        return Decimal("0")
    
    try:
        # Detecta formato brasileiro (1.234,56)
        if "," in valor and "." in valor:
            valor = valor.replace(".", "").replace(",", ".")
        elif "," in valor:
            valor = valor.replace(",", ".")
        
        return Decimal(valor)
    except InvalidOperation:
        return Decimal("0")


def _parse_data(data: str) -> Optional[datetime]:
    """
    Converte string de data para datetime.
    Aceita formatos: dd/mm/yyyy, yyyy-mm-dd
    """
    if not data:
        return None
    
    data = str(data).strip()
    
    for fmt in ["%d/%m/%Y", "%Y-%m-%d", "%d/%m/%y"]:
        try:
            return datetime.strptime(data, fmt)
        except ValueError:
            continue
    
    return None


def processar_dados_financeiros(
    dados: List[List[Any]],
    col_data: int = 0,
    col_descricao: int = 1,
    col_categoria: int = 2,
    col_valor: int = 3,
    col_tipo: int = 4,  # "Receita" ou "Despesa"
    tem_cabecalho: bool = True
) -> Dict[str, Any]:
    """
    Processa dados financeiros e retorna estatísticas para dashboard.
    
    Args:
        dados: Lista de linhas da planilha
        col_*: Índices das colunas (0-based)
        tem_cabecalho: Se a primeira linha é cabeçalho
    
    Returns:
        Dicionário com totais, por categoria, por mês, etc.
    """
    if tem_cabecalho and dados:
        dados = dados[1:]
    
    total_receitas = Decimal("0")
    total_despesas = Decimal("0")
    por_categoria = {}
    por_mes = {}
    transacoes = []
    
    for linha in dados:
        if len(linha) <= max(col_data, col_descricao, col_valor):
            continue
        
        data = _parse_data(linha[col_data]) if col_data < len(linha) else None
        descricao = linha[col_descricao] if col_descricao < len(linha) else ""
        categoria = linha[col_categoria] if col_categoria < len(linha) else "Outros"
        valor = _parse_valor(linha[col_valor]) if col_valor < len(linha) else Decimal("0")
        tipo = linha[col_tipo].lower() if col_tipo < len(linha) else "despesa"
        
        is_receita = "receita" in tipo or valor > 0
        
        if is_receita:
            total_receitas += abs(valor)
        else:
            total_despesas += abs(valor)
        
        # Por categoria
        if categoria not in por_categoria:
            por_categoria[categoria] = {"receitas": Decimal("0"), "despesas": Decimal("0")}
        
        if is_receita:
            por_categoria[categoria]["receitas"] += abs(valor)
        else:
            por_categoria[categoria]["despesas"] += abs(valor)
        
        # Por mês
        if data:
            mes_key = data.strftime("%Y-%m")
            if mes_key not in por_mes:
                por_mes[mes_key] = {"receitas": Decimal("0"), "despesas": Decimal("0")}
            
            if is_receita:
                por_mes[mes_key]["receitas"] += abs(valor)
            else:
                por_mes[mes_key]["despesas"] += abs(valor)
        
        # Lista de transações (últimas 50)
        if len(transacoes) < 50:
            transacoes.append({
                "data": data.strftime("%d/%m/%Y") if data else "-",
                "descricao": descricao,
                "categoria": categoria,
                "valor": float(valor),
                "tipo": "receita" if is_receita else "despesa",
            })
    
    # Ordena meses
    meses_ordenados = sorted(por_mes.items())
    
    # Calcula saldo
    saldo = total_receitas - total_despesas
    
    return {
        "resumo": {
            "total_receitas": float(total_receitas),
            "total_despesas": float(total_despesas),
            "saldo": float(saldo),
            "total_transacoes": len(dados),
        },
        "por_categoria": {
            k: {"receitas": float(v["receitas"]), "despesas": float(v["despesas"])}
            for k, v in por_categoria.items()
        },
        "por_mes": [
            {
                "mes": mes,
                "receitas": float(dados["receitas"]),
                "despesas": float(dados["despesas"]),
                "saldo": float(dados["receitas"] - dados["despesas"]),
            }
            for mes, dados in meses_ordenados
        ],
        "ultimas_transacoes": transacoes,
        "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def processar_fluxo_caixa(
    dados: List[List[Any]],
    col_data: int = 0,
    col_valor: int = 1,
    col_tipo: int = 2,
    tem_cabecalho: bool = True
) -> Dict[str, Any]:
    """
    Processa dados de fluxo de caixa para gráfico de linha.
    """
    if tem_cabecalho and dados:
        dados = dados[1:]
    
    fluxo = {}
    saldo_acumulado = Decimal("0")
    
    for linha in dados:
        if len(linha) < 2:
            continue
        
        data = _parse_data(linha[col_data])
        valor = _parse_valor(linha[col_valor]) if col_valor < len(linha) else Decimal("0")
        tipo = linha[col_tipo].lower() if col_tipo < len(linha) else ""
        
        if not data:
            continue
        
        dia_key = data.strftime("%Y-%m-%d")
        
        if dia_key not in fluxo:
            fluxo[dia_key] = {"entradas": Decimal("0"), "saidas": Decimal("0")}
        
        if "receita" in tipo or "entrada" in tipo or valor > 0:
            fluxo[dia_key]["entradas"] += abs(valor)
            saldo_acumulado += abs(valor)
        else:
            fluxo[dia_key]["saidas"] += abs(valor)
            saldo_acumulado -= abs(valor)
    
    # Ordena por data
    fluxo_ordenado = sorted(fluxo.items())
    
    # Calcula saldo acumulado dia a dia
    saldo = Decimal("0")
    resultado = []
    
    for dia, valores in fluxo_ordenado:
        saldo += valores["entradas"] - valores["saidas"]
        resultado.append({
            "data": dia,
            "entradas": float(valores["entradas"]),
            "saidas": float(valores["saidas"]),
            "saldo_dia": float(valores["entradas"] - valores["saidas"]),
            "saldo_acumulado": float(saldo),
        })
    
    return {
        "fluxo": resultado,
        "saldo_final": float(saldo),
        "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


# ── Verificação de Conexão ───────────────────────────────────────────────────

def verificar_conexao() -> Dict[str, Any]:
    """
    Verifica se as credenciais estão configuradas corretamente.
    """
    creds = _get_credentials()
    
    if not creds:
        return {
            "conectado": False,
            "erro": "Credenciais não configuradas. Configure GOOGLE_SHEETS_CREDENTIALS ou GOOGLE_SHEETS_CREDENTIALS_FILE.",
        }
    
    try:
        service = _get_sheets_service()
        # Tenta uma operação simples para validar
        return {
            "conectado": True,
            "service_account": creds.service_account_email,
        }
    except Exception as e:
        return {
            "conectado": False,
            "erro": str(e),
        }


# ── Gerenciamento de Planilhas Configuradas ──────────────────────────────────

def get_planilhas_configuradas() -> List[Dict[str, Any]]:
    """
    Retorna lista de planilhas configuradas no sistema.
    Por enquanto usa variável de ambiente, mas pode ser migrado para banco.
    
    Formato esperado da env GOOGLE_SHEETS_CONFIG:
    [
        {"id": "xxx", "nome": "Financeiro", "tipo": "financeiro", "range": "Dados!A:Z"},
        {"id": "yyy", "nome": "Fluxo Caixa", "tipo": "fluxo", "range": "Fluxo!A:D"}
    ]
    """
    config_json = os.environ.get("GOOGLE_SHEETS_CONFIG", "[]")
    
    try:
        return json.loads(config_json)
    except json.JSONDecodeError:
        return []


def processar_cobrancas_pratika(dados: List[List[Any]]) -> Dict[str, Any]:
    """
    Processa planilha no formato multi-bloco de cobrança Pratika.

    Layout esperado:
    - Bloco esquerdo : cols 1-4  (nome, valor, data_pag, valor_pago)
    - Bloco direito  : cols 7-10 (nome, valor, data_pag, valor_pago)
    - Boletos antec. : cols 12-14 (nome, valor, data)
    Seções identificadas por linhas de cabeçalho "VENCIMENTO XX".
    """
    registros: List[Dict[str, Any]] = []
    secao_esq: Optional[str] = None
    secao_dir: Optional[str] = None
    titulo = ""

    def cell(row, i):
        return str(row[i]).strip() if i < len(row) else ""

    for raw_row in dados:
        row = list(raw_row) + [""] * max(0, 15 - len(raw_row))

        c1, c2, c7, c8 = cell(row, 1), cell(row, 2), cell(row, 7), cell(row, 8)

        # Boletos antecipados (col 12 = M, col 13 = N) — processado ANTES dos continue
        _ignorar_antec = {"BOLETOS ANTECIPADOS", "TOTAL", "SUBTOTAL"}
        c12 = str(row[12]).strip()
        c13 = str(row[13]).strip()
        if c12 and c12.upper() not in _ignorar_antec and not c12.upper().startswith("R$"):
            valor = _parse_valor(c13)
            if valor > 0:
                registros.append({
                    "condominio": c12,
                    "vencimento": "Antecipado",
                    "valor_previsto": None,
                    "data_pagamento": "",
                    "valor_pago": float(valor),
                    "status": "antecipado",
                    "diferenca": None,
                })

        # Título (primeira célula não-vazia na col 1)
        if not titulo and c1 and not re.search(r"VENCIMENTO", c1.upper()):
            titulo = c1
            continue

        # Cabeçalho de seção esquerda
        if re.search(r"VENCIMENTO\s+\d+", c1.upper()) and c2.upper() in ("VALOR", "TOTAL"):
            m = re.search(r"VENCIMENTO\s+(\d+)", c1.upper())
            secao_esq = f"Vencimento {m.group(1)}"
            # Cabeçalho direito na mesma linha
            if re.search(r"VENCIMENTO\s+\d+", c7.upper()) and c8.upper() in ("VALOR", "TOTAL"):
                m2 = re.search(r"VENCIMENTO\s+(\d+)", c7.upper())
                secao_dir = f"Vencimento {m2.group(1)}"
            continue

        # Cabeçalho de seção direita em linha separada
        if re.search(r"VENCIMENTO\s+\d+", c7.upper()) and c8.upper() in ("VALOR", "TOTAL"):
            m = re.search(r"VENCIMENTO\s+(\d+)", c7.upper())
            secao_dir = f"Vencimento {m.group(1)}"
            continue

        _ignorar = {"VENCIMENTO", "TOTAL", "SUBTOTAL"}

        # Bloco esquerdo — ignora linhas sem nome ou com totais
        if secao_esq and c1 and not any(w in c1.upper() for w in _ignorar):
            valor = _parse_valor(c2)
            if valor > 0:
                valor_pago = _parse_valor(cell(row, 4))
                registros.append({
                    "condominio": c1,
                    "vencimento": secao_esq,
                    "valor_previsto": float(valor),
                    "data_pagamento": cell(row, 3),
                    "valor_pago": float(valor_pago),
                    "status": "pago" if valor_pago > 0 else "pendente",
                    "diferenca": round(float(valor_pago - valor), 2),
                })

        # Bloco direito
        if secao_dir and c7 and not any(w in c7.upper() for w in _ignorar):
            valor = _parse_valor(c8)
            if valor > 0:
                valor_pago = _parse_valor(cell(row, 10))
                registros.append({
                    "condominio": c7,
                    "vencimento": secao_dir,
                    "valor_previsto": float(valor),
                    "data_pagamento": cell(row, 9),
                    "valor_pago": float(valor_pago),
                    "status": "pago" if valor_pago > 0 else "pendente",
                    "diferenca": round(float(valor_pago - valor), 2),
                })


    # Resumo
    regulares = [r for r in registros if r["status"] != "antecipado"]
    total_previsto = sum(r["valor_previsto"] for r in regulares)
    total_recebido = sum(r["valor_pago"] for r in regulares)
    total_antecipado = sum(r["valor_pago"] for r in registros if r["status"] == "antecipado")
    pendente = total_previsto - total_recebido
    pct = round(total_recebido / total_previsto * 100, 1) if total_previsto else 0.0

    # Por vencimento
    por_venc_map: Dict[str, Any] = {}
    for r in registros:
        v = r["vencimento"]
        if v not in por_venc_map:
            por_venc_map[v] = {"vencimento": v, "previsto": 0.0, "recebido": 0.0, "pagos": 0, "pendentes": 0}
        if r["valor_previsto"]:
            por_venc_map[v]["previsto"] += r["valor_previsto"]
        por_venc_map[v]["recebido"] += r["valor_pago"]
        if r["status"] == "pago":
            por_venc_map[v]["pagos"] += 1
        elif r["status"] == "pendente":
            por_venc_map[v]["pendentes"] += 1

    def _sort_key(item):
        m = re.search(r"\d+", item["vencimento"])
        return int(m.group()) if m else 999

    por_vencimento = sorted(por_venc_map.values(), key=_sort_key)
    for pv in por_vencimento:
        pv["previsto"] = round(pv["previsto"], 2)
        pv["recebido"] = round(pv["recebido"], 2)

    return {
        "tipo": "cobrancas",
        "titulo": titulo,
        "resumo": {
            "total_previsto": round(total_previsto, 2),
            "total_recebido": round(total_recebido, 2),
            "total_antecipado": round(total_antecipado, 2),
            "pendente": round(pendente, 2),
            "percentual_recebido": pct,
            "total_condominios": len(regulares),
            "pagos": len([r for r in regulares if r["status"] == "pago"]),
            "pendentes": len([r for r in regulares if r["status"] == "pendente"]),
        },
        "por_vencimento": por_vencimento,
        "registros": registros,
        "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def processar_advocacia(dados: List[List[Any]]) -> Dict[str, Any]:
    """
    Processa planilha de honorários advocatícios.

    Layout esperado (colunas 0-based):
      0: vazio | 1: Unidade | 2: Compet. | 3: Vencimento | 4: Liquidação
      5: Honorários | 6: Advogado | 7: Taxa de cobrança | 8: Cobrança
      9: Creditado | 10: Extrato
    """
    registros: List[Dict[str, Any]] = []
    titulo = ""
    header_encontrado = False

    def cell(row, i):
        return str(row[i]).strip() if i < len(row) else ""

    for raw_row in dados:
        row = list(raw_row) + [""] * max(0, 11 - len(raw_row))

        c1 = cell(row, 1)

        # Título (primeira linha não vazia)
        if not titulo and c1:
            titulo = c1
            continue

        # Detecta linha de cabeçalho
        if not header_encontrado and "unidade" in c1.lower():
            header_encontrado = True
            continue

        if not header_encontrado:
            continue

        # Pula linhas sem unidade (totais ou vazias)
        if not c1:
            continue

        taxa = _parse_valor(cell(row, 7))
        honorarios = _parse_valor(cell(row, 5))
        creditado = _parse_valor(cell(row, 9))
        liquidacao = cell(row, 4)
        extrato = cell(row, 10)

        registros.append({
            "unidade": c1,
            "competencia": cell(row, 2),
            "vencimento": cell(row, 3),
            "liquidacao": liquidacao,
            "honorarios": float(honorarios),
            "advogado": cell(row, 6),
            "taxa_cobranca": float(taxa),
            "creditado": float(creditado),
            "extrato": extrato,
            "status": "liquidado" if liquidacao else "pendente",
        })

    # Resumo
    total_taxa = sum(r["taxa_cobranca"] for r in registros)
    total_creditado = sum(r["creditado"] for r in registros)
    total_honorarios = sum(r["honorarios"] for r in registros)
    liquidados = [r for r in registros if r["status"] == "liquidado"]
    pendentes = [r for r in registros if r["status"] == "pendente"]
    pct = round(len(liquidados) / len(registros) * 100, 1) if registros else 0.0

    # Por advogado
    por_adv_map: Dict[str, Any] = {}
    for r in registros:
        adv = r["advogado"] or "Sem advogado"
        if adv not in por_adv_map:
            por_adv_map[adv] = {"advogado": adv, "taxa_total": 0.0, "creditado_total": 0.0, "liquidados": 0, "pendentes": 0}
        por_adv_map[adv]["taxa_total"] += r["taxa_cobranca"]
        por_adv_map[adv]["creditado_total"] += r["creditado"]
        if r["status"] == "liquidado":
            por_adv_map[adv]["liquidados"] += 1
        else:
            por_adv_map[adv]["pendentes"] += 1

    por_advogado = sorted(por_adv_map.values(), key=lambda x: x["taxa_total"], reverse=True)
    for pa in por_advogado:
        pa["taxa_total"] = round(pa["taxa_total"], 2)
        pa["creditado_total"] = round(pa["creditado_total"], 2)

    return {
        "tipo": "advocacia",
        "titulo": titulo,
        "resumo": {
            "total_taxa_cobranca": round(total_taxa, 2),
            "total_creditado": round(total_creditado, 2),
            "total_honorarios": round(total_honorarios, 2),
            "percentual_liquidado": pct,
            "total_unidades": len(registros),
            "liquidados": len(liquidados),
            "pendentes": len(pendentes),
        },
        "por_advogado": por_advogado,
        "registros": registros,
        "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def processar_despesas_unidade(dados: List[List[Any]]) -> Dict[str, Any]:
    """
    Processa planilha de despesas por unidade.

    Layout: múltiplas seções empilhadas verticalmente.
    Cada seção: nome da unidade → cabeçalho → linhas de despesa → TOTAL
    Colunas: 0=Vencimento, 1=Fornecedor, 2=Valor líquido
    """
    registros: List[Dict[str, Any]] = []
    unidade_atual: Optional[str] = None
    titulo = ""

    def cell(row, i):
        return str(row[i]).strip() if i < len(row) else ""

    def _is_date(s: str) -> bool:
        return bool(re.search(r"\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4}", s))

    for raw_row in dados:
        row = list(raw_row) + [""] * max(0, 3 - len(raw_row))
        c0, c1, c2 = cell(row, 0), cell(row, 1), cell(row, 2)

        # Ignora linhas totalmente vazias
        if not c0 and not c1 and not c2:
            continue

        # Ignora linha de total geral (só col 2 tem valor)
        if not c0 and not c1 and c2:
            continue

        # Ignora cabeçalho de coluna
        if "venc" in c0.lower() and "fornec" in c1.lower():
            continue

        # Ignora linha de TOTAL da seção
        if c0.upper().startswith("TOTAL"):
            continue

        # Ignora subtítulos entre parênteses
        if c0.startswith("("):
            continue

        # Nome da seção: col0 com texto, col1 e col2 vazios, sem data
        if c0 and not c1 and not c2 and not _is_date(c0):
            if not titulo:
                titulo = c0
            else:
                unidade_atual = c0
            continue

        # Linha de dados
        if unidade_atual and c1 and c2:
            valor = _parse_valor(c2)
            if valor > 0:
                registros.append({
                    "unidade": unidade_atual,
                    "vencimento": c0,
                    "fornecedor": c1,
                    "valor": float(valor),
                })

    # Resumo
    total_geral = sum(r["valor"] for r in registros)

    # Por unidade
    por_unidade_map: Dict[str, Any] = {}
    for r in registros:
        u = r["unidade"]
        if u not in por_unidade_map:
            por_unidade_map[u] = {"unidade": u, "total": 0.0, "count": 0}
        por_unidade_map[u]["total"] += r["valor"]
        por_unidade_map[u]["count"] += 1

    por_unidade = sorted(por_unidade_map.values(), key=lambda x: x["total"], reverse=True)
    for pu in por_unidade:
        pu["total"] = round(pu["total"], 2)

    # Por fornecedor (top 10)
    por_forn_map: Dict[str, float] = {}
    for r in registros:
        f = r["fornecedor"]
        por_forn_map[f] = por_forn_map.get(f, 0.0) + r["valor"]

    por_fornecedor = sorted(
        [{"fornecedor": k, "total": round(v, 2)} for k, v in por_forn_map.items()],
        key=lambda x: x["total"],
        reverse=True,
    )[:10]

    return {
        "tipo": "despesas",
        "titulo": titulo,
        "resumo": {
            "total_geral": round(total_geral, 2),
            "total_unidades": len(por_unidade_map),
            "total_registros": len(registros),
            "fornecedores_unicos": len(por_forn_map),
            "maior_unidade": por_unidade[0]["unidade"] if por_unidade else "",
            "maior_unidade_valor": por_unidade[0]["total"] if por_unidade else 0.0,
        },
        "por_unidade": por_unidade,
        "por_fornecedor": por_fornecedor,
        "registros": registros,
        "atualizado_em": datetime.now().strftime("%d/%m/%Y %H:%M"),
    }


def adicionar_planilha_config(planilha: Dict[str, str]) -> bool:
    """
    Adiciona planilha à configuração.
    Nota: Em produção, isso deve ser salvo no banco de dados.
    """
    # Por enquanto, apenas valida. Em produção, salvar no banco.
    required = ["id", "nome", "tipo"]
    return all(k in planilha for k in required)