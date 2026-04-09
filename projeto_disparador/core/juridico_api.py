"""
API para aba Jurídico — planilhas de advogados via Google Sheets.
"""

import re
from typing import List, Optional
from decimal import Decimal, InvalidOperation
from ninja import Router, Schema
from core.auth import JWTAuth
from core.sheets_service import buscar_dados_planilha, listar_abas
from core.models import AdvogadoPlanilha

juridico_router = Router(auth=JWTAuth(), tags=["Juridico"])


# ── Schemas ──────────────────────────────────────────────────────────────────

class AdvogadoIn(Schema):
    nome: str
    spreadsheet_id: str
    aba: str = ""


class AdvogadoOut(Schema):
    id: int
    nome: str
    spreadsheet_id: str
    aba: str


class AdvogadoUpdateIn(Schema):
    nome: Optional[str] = None
    spreadsheet_id: Optional[str] = None
    aba: Optional[str] = None


# ── CRUD Advogados ───────────────────────────────────────────────────────────

@juridico_router.get("/advogados", response=List[AdvogadoOut], summary="Lista advogados cadastrados")
def listar_advogados(request):
    return list(AdvogadoPlanilha.objects.all().values("id", "nome", "spreadsheet_id", "aba"))


@juridico_router.post("/advogados", response=AdvogadoOut, summary="Cadastra advogado com planilha")
def criar_advogado(request, payload: AdvogadoIn):
    adv = AdvogadoPlanilha.objects.create(
        nome=payload.nome,
        spreadsheet_id=payload.spreadsheet_id,
        aba=payload.aba,
    )
    return {"id": adv.id, "nome": adv.nome, "spreadsheet_id": adv.spreadsheet_id, "aba": adv.aba}


@juridico_router.put("/advogados/{adv_id}", response=AdvogadoOut, summary="Atualiza advogado")
def atualizar_advogado(request, adv_id: int, payload: AdvogadoUpdateIn):
    adv = AdvogadoPlanilha.objects.get(id=adv_id)
    if payload.nome is not None:
        adv.nome = payload.nome
    if payload.spreadsheet_id is not None:
        adv.spreadsheet_id = payload.spreadsheet_id
    if payload.aba is not None:
        adv.aba = payload.aba
    adv.save()
    return {"id": adv.id, "nome": adv.nome, "spreadsheet_id": adv.spreadsheet_id, "aba": adv.aba}


@juridico_router.delete("/advogados/{adv_id}", summary="Remove advogado")
def deletar_advogado(request, adv_id: int):
    AdvogadoPlanilha.objects.filter(id=adv_id).delete()
    return {"ok": True}


# ── Abas disponíveis ─────────────────────────────────────────────────────────

@juridico_router.get("/advogados/{adv_id}/abas", summary="Lista abas da planilha do advogado")
def listar_abas_advogado(request, adv_id: int):
    adv = AdvogadoPlanilha.objects.get(id=adv_id)
    try:
        abas = listar_abas(adv.spreadsheet_id)
        return {"advogado": adv.nome, "abas": abas}
    except Exception as e:
        return {"advogado": adv.nome, "abas": [], "erro": str(e)}


# ── Dados da planilha ────────────────────────────────────────────────────────

@juridico_router.get("/advogados/{adv_id}/dados", summary="Retorna dados da planilha do advogado")
def dados_advogado(request, adv_id: int, aba: Optional[str] = None):
    adv = AdvogadoPlanilha.objects.get(id=adv_id)
    aba_nome = aba or adv.aba
    if not aba_nome:
        # Se não tem aba configurada, busca a primeira
        try:
            abas = listar_abas(adv.spreadsheet_id)
            if abas:
                aba_nome = abas[0]["title"]
            else:
                return {"advogado": adv.nome, "cabecalho": [], "linhas": [], "erro": "Nenhuma aba encontrada"}
        except Exception as e:
            return {"advogado": adv.nome, "cabecalho": [], "linhas": [], "erro": str(e)}

    try:
        dados = buscar_dados_planilha(adv.spreadsheet_id, f"{aba_nome}!A1:Z500", use_cache=True)
        if not dados:
            return {"advogado": adv.nome, "aba": aba_nome, "cabecalho": [], "linhas": []}

        cabecalho = dados[0] if dados else []
        linhas = dados[1:] if len(dados) > 1 else []

        return {
            "advogado": adv.nome,
            "aba": aba_nome,
            "cabecalho": cabecalho,
            "linhas": linhas,
            "total_linhas": len(linhas),
        }
    except Exception as e:
        return {"advogado": adv.nome, "aba": aba_nome, "cabecalho": [], "linhas": [], "erro": str(e)}


# ── Helpers de parsing ───────────────────────────────────────────────────────

def _cell(row, idx):
    try:
        return (row[idx] or "").strip()
    except (IndexError, AttributeError):
        return ""


def _parse_valor(valor: str) -> float:
    if not valor:
        return 0.0
    valor = str(valor).replace("R$", "").replace(" ", "").strip()
    if not valor:
        return 0.0
    try:
        if "," in valor and "." in valor:
            valor = valor.replace(".", "").replace(",", ".")
        elif "," in valor:
            valor = valor.replace(",", ".")
        return float(valor)
    except (ValueError, InvalidOperation):
        return 0.0


# ── Dashboard consolidado ───────────────────────────────────────────────────

@juridico_router.get("/dashboard", summary="Dashboard consolidado de todos os advogados")
def dashboard_juridico(request):
    """
    Coleta dados de todos os advogados e retorna KPIs consolidados.
    Colunas esperadas: Condomínio(0), Bloco(1), Unidade(2), Nome(3), CPF(4),
    Total(5), Data Última Mov.(6), Nº Processo(7), Análise(8),
    Situação Judicial(9), Movimentou Semana(10), Situação Atual(11),
    Data Situação(12), Prospecção(13)
    """
    advogados = AdvogadoPlanilha.objects.all()
    por_advogado = []
    por_condominio = {}
    por_situacao = {}
    total_geral = 0.0
    total_processos = 0
    total_com_processo = 0
    total_sem_processo = 0
    total_movimentou = 0
    todos_processos = []

    for adv in advogados:
        aba = adv.aba or "Jurídico"
        try:
            dados = buscar_dados_planilha(adv.spreadsheet_id, f"{aba}!A1:N500", use_cache=True)
        except Exception:
            por_advogado.append({
                "nome": adv.nome, "processos": 0, "total": 0.0,
                "com_processo": 0, "sem_processo": 0, "movimentou": 0,
            })
            continue

        linhas = dados[1:] if dados else []
        adv_total = 0.0
        adv_processos = 0
        adv_com_processo = 0
        adv_sem_processo = 0
        adv_movimentou = 0

        for row in linhas:
            cond = _cell(row, 0)
            if not cond:
                continue

            valor = _parse_valor(_cell(row, 5))
            num_processo = _cell(row, 7)
            situacao = _cell(row, 9)
            mov_semana = _cell(row, 10).lower()

            adv_processos += 1
            adv_total += valor

            tem_processo = bool(num_processo and num_processo != "-" and num_processo != "não")
            if tem_processo:
                adv_com_processo += 1
            else:
                adv_sem_processo += 1

            if mov_semana == "sim":
                adv_movimentou += 1

            # Por condomínio
            if cond not in por_condominio:
                por_condominio[cond] = {"condominio": cond, "processos": 0, "total": 0.0}
            por_condominio[cond]["processos"] += 1
            por_condominio[cond]["total"] += valor

            # Por situação judicial
            sit_key = situacao if situacao and situacao != "-" else "Sem situação"
            if sit_key not in por_situacao:
                por_situacao[sit_key] = 0
            por_situacao[sit_key] += 1

            # Top devedores
            todos_processos.append({
                "condominio": cond,
                "unidade": _cell(row, 2),
                "nome": _cell(row, 3),
                "valor": valor,
                "advogado": adv.nome,
                "situacao": situacao or "-",
                "num_processo": num_processo or "-",
            })

        total_geral += adv_total
        total_processos += adv_processos
        total_com_processo += adv_com_processo
        total_sem_processo += adv_sem_processo
        total_movimentou += adv_movimentou

        por_advogado.append({
            "nome": adv.nome,
            "processos": adv_processos,
            "total": round(adv_total, 2),
            "com_processo": adv_com_processo,
            "sem_processo": adv_sem_processo,
            "movimentou": adv_movimentou,
        })

    # Ordena condomínios por total
    condominios_list = sorted(por_condominio.values(), key=lambda x: x["total"], reverse=True)
    for c in condominios_list:
        c["total"] = round(c["total"], 2)

    # Ordena situações por quantidade
    situacoes_list = sorted(
        [{"situacao": k, "quantidade": v} for k, v in por_situacao.items()],
        key=lambda x: x["quantidade"], reverse=True,
    )

    # Top 20 maiores devedores
    top_devedores = sorted(todos_processos, key=lambda x: x["valor"], reverse=True)[:20]
    for d in top_devedores:
        d["valor"] = round(d["valor"], 2)

    return {
        "resumo": {
            "total_geral": round(total_geral, 2),
            "total_processos": total_processos,
            "com_processo": total_com_processo,
            "sem_processo": total_sem_processo,
            "movimentou_semana": total_movimentou,
            "total_condominios": len(por_condominio),
            "total_advogados": len(por_advogado),
        },
        "por_advogado": por_advogado,
        "por_condominio": condominios_list,
        "por_situacao": situacoes_list,
        "top_devedores": top_devedores,
    }
