#!/usr/bin/env python3
"""
Aplica o patch de "ultimos_5_anos" no superlogica.py.
Execute na raiz do projeto: python3 patch_superlogica.py
"""

path = "projeto_disparador/core/superlogica.py"

with open(path, "r") as f:
    content = f.read()

erros = []

# ── Patch 1: _buscar_valores_unidade — assinatura ────────────────────────────
old1 = "def _buscar_valores_unidade(id_condominio: int, id_unidade: str, mapa_unidades: dict):"
new1 = "def _buscar_valores_unidade(id_condominio: int, id_unidade: str, mapa_unidades: dict, data_inicio: str = None):"
if old1 in content:
    content = content.replace(old1, new1, 1)
    print("✅ Patch 1 aplicado: assinatura _buscar_valores_unidade")
else:
    erros.append("❌ Patch 1: assinatura _buscar_valores_unidade não encontrada")

# ── Patch 2: _buscar_valores_unidade — filtro no loop ────────────────────────
old2 = '    for receb in dados:\n        if not isinstance(receb, dict):\n            continue\n\n        vencimento  = receb.get("dt_vencimento_recb", "")'
new2 = '    for receb in dados:\n        if not isinstance(receb, dict):\n            continue\n\n        # Filtro por período (ultimos_5_anos)\n        if data_inicio:\n            _dt_raw = receb.get("dt_vencimento_recb", "")\n            try:\n                from datetime import datetime as _dtcls\n                _s = str(_dt_raw).strip()[:10]\n                _d = _dtcls.strptime(_s, "%Y-%m-%d") if "-" in _s else _dtcls.strptime(_s, "%d/%m/%Y")\n                _i = _dtcls.strptime(data_inicio, "%d/%m/%Y")\n                if _d < _i:\n                    continue\n            except Exception:\n                pass\n\n        vencimento  = receb.get("dt_vencimento_recb", "")'
if old2 in content:
    content = content.replace(old2, new2, 1)
    print("✅ Patch 2 aplicado: filtro data_inicio no loop de recebimentos")
else:
    erros.append("❌ Patch 2: loop for receb in dados não encontrado (verifique indentação)")

# ── Patch 3: buscar_inadimplentes_condominio — assinatura ────────────────────
old3 = "def buscar_inadimplentes_condominio(id_condominio: int, data_posicao: str, mapa_unidades: dict):"
new3 = "def buscar_inadimplentes_condominio(id_condominio: int, data_posicao: str, mapa_unidades: dict, data_inicio: str = None):"
if old3 in content:
    content = content.replace(old3, new3, 1)
    print("✅ Patch 3 aplicado: assinatura buscar_inadimplentes_condominio")
else:
    erros.append("❌ Patch 3: assinatura buscar_inadimplentes_condominio não encontrada")

# ── Patch 4: executor.submit — passa data_inicio ─────────────────────────────
old4 = "            executor.submit(_buscar_valores_unidade, id_condominio, id_uni, mapa_unidades): id_uni"
new4 = "            executor.submit(_buscar_valores_unidade, id_condominio, id_uni, mapa_unidades, data_inicio): id_uni"
if old4 in content:
    content = content.replace(old4, new4, 1)
    print("✅ Patch 4 aplicado: executor.submit com data_inicio")
else:
    erros.append("❌ Patch 4: chamada executor.submit não encontrada")

# ── Patch 5: gerar_relatorio_inadimplentes — assinatura ──────────────────────
old5 = "def gerar_relatorio_inadimplentes(\n    id_condominio: Optional[int] = None,\n    data_posicao: Optional[str] = None,\n) -> tuple:"
new5 = "def gerar_relatorio_inadimplentes(\n    id_condominio: Optional[int] = None,\n    data_posicao: Optional[str] = None,\n    data_inicio: Optional[str] = None,\n) -> tuple:"
if old5 in content:
    content = content.replace(old5, new5, 1)
    print("✅ Patch 5 aplicado: assinatura gerar_relatorio_inadimplentes")
else:
    erros.append("❌ Patch 5: assinatura gerar_relatorio_inadimplentes não encontrada")

# ── Patch 6: _processar_condominio — passa data_inicio ───────────────────────
old6 = "        resumo, detalhado = buscar_inadimplentes_condominio(condo_id, data_posicao, mapa_unidades)"
new6 = "        resumo, detalhado = buscar_inadimplentes_condominio(condo_id, data_posicao, mapa_unidades, data_inicio)"
if old6 in content:
    content = content.replace(old6, new6, 1)
    print("✅ Patch 6 aplicado: chamada buscar_inadimplentes_condominio em _processar_condominio")
else:
    erros.append("❌ Patch 6: chamada buscar_inadimplentes_condominio não encontrada")

# ── Salva ─────────────────────────────────────────────────────────────────────
if erros:
    print("\nPatches com erro — arquivo NÃO foi salvo:")
    for e in erros:
        print(" ", e)
else:
    with open(path, "w") as f:
        f.write(content)
    print(f"\n✅ Todos os 6 patches aplicados com sucesso em {path}")