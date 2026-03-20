#!/usr/bin/env python3
"""
Remove Principal, Juros, Multa, Atualização, Honorários do PDF.
Versão robusta com regex — funciona independente de indentação.
Execute na raiz do projeto: python patch_pdf_colunas_v2.py
"""
import re, sys

path = "projeto_disparador/core/superlogica.py"

with open(path, "r", encoding="utf-8") as f:
    content = f.read()

erros = []

# ── Patch 1: Cabeçalho da tabela por condomínio ──────────────────────────────
# Substitui o bloco "cabecalho = [..." dentro de gerar_pdf_inadimplentes
# procurando pelas colunas financeiras e removendo-as

p1_old = re.compile(
    r'([ \t]+cabecalho\s*=\s*\[.*?'
    r'p\("Juizado",\s*style_cell_bold\),\s*\n)'   # ancora em Juizado
    r'([ \t]+p\("Principal".*?\n)'
    r'([ \t]+p\("Juros".*?\n)'
    r'([ \t]+p\("Multa".*?\n)'
    r'([ \t]+p\("Atualização".*?\n)'
    r'([ \t]+p\("Honorários".*?\n)'
    r'([ \t]+p\("Total",\s*style_cell_bold\),\s*\n[ \t]*\])',
    re.DOTALL
)

m1 = p1_old.search(content)
if m1:
    indent = re.match(r'^([ \t]+)', m1.group(1)).group(1)
    new_cabecalho = (
        m1.group(1)  # tudo até Juizado inclusive
        + indent + 'p("Total", style_cell_bold),\n'
        + indent[:-4] + ']'  # fecha lista
    )
    content = content[:m1.start()] + new_cabecalho + content[m1.end():]
    print("✅ Patch 1 aplicado: cabeçalho da tabela")
else:
    erros.append("❌ Patch 1: cabeçalho não encontrado")

# ── Patch 2: Linhas de dados da tabela ───────────────────────────────────────
p2_old = re.compile(
    r'([ \t]+dados_tabela\.append\(\[\s*\n'
    r'[ \t]+p\(row\["Unidade"\]\),\s*\n'
    r'[ \t]+p\(row\["Nome"\]\),\s*\n'
    r'[ \t]+p\(row\["Telefone 1"\]\),\s*\n'
    r'[ \t]+p\(row\["Telefone 2"\]\),\s*\n'
    r'[ \t]+p\(row\.get\("Juizado"[^)]*\)\),\s*\n)'   # ancora em Juizado
    r'[ \t]+p\(brl\(row\["Principal"\]\)\),\s*\n'
    r'[ \t]+p\(brl\(row\["Juros"\]\)\),\s*\n'
    r'[ \t]+p\(brl\(row\["Multa"\]\)\),\s*\n'
    r'[ \t]+p\(brl\(row\["Atualização"\]\)\),\s*\n'
    r'[ \t]+p\(brl\(row\["Honorários"\]\)\),\s*\n'
    r'([ \t]+p\(brl\(row\["Total"\]\)\),\s*\n[ \t]+\]\))',
)

m2 = p2_old.search(content)
if m2:
    new_row = m2.group(1) + m2.group(2)
    content = content[:m2.start()] + new_row + content[m2.end():]
    print("✅ Patch 2 aplicado: linhas de dados")
else:
    erros.append("❌ Patch 2: linhas de dados não encontradas")

# ── Patch 3: Linha de totais do condomínio ────────────────────────────────────
p3_old = re.compile(
    r'([ \t]+dados_tabela\.append\(\[\s*\n'
    r'[ \t]+p\("TOTAL",\s*style_tot\),\s*\n'
    r'(?:[ \t]+p\("",\s*style_tot\),\s*\n){2,6})'   # 2 a 6 células vazias
    r'[ \t]+p\(brl\(tot_principal\),\s*style_tot\),\s*\n'
    r'[ \t]+p\(brl\(tot_juros\),\s*style_tot\),\s*\n'
    r'[ \t]+p\(brl\(tot_multa\),\s*style_tot\),\s*\n'
    r'[ \t]+p\(brl\(tot_atualiz\),\s*style_tot\),\s*\n'
    r'[ \t]+p\(brl\(tot_honor\),\s*style_tot\),\s*\n'
    r'([ \t]+p\(brl\(tot_total\),\s*style_tot\),\s*\n[ \t]+\]\))',
)

m3 = p3_old.search(content)
if m3:
    new_total = m3.group(1) + m3.group(2)
    content = content[:m3.start()] + new_total + content[m3.end():]
    print("✅ Patch 3 aplicado: linha de totais")
else:
    erros.append("❌ Patch 3: linha de totais não encontrada")

# ── Salva ─────────────────────────────────────────────────────────────────────
if erros:
    print("\nPatches com erro — arquivo NÃO foi salvo:")
    for e in erros:
        print(" ", e)
    print("\n--- DIAGNÓSTICO ---")
    print("Procurando trecho 'cabecalho' na função gerar_pdf_inadimplentes:")
    idx = content.find("cabecalho = [")
    if idx >= 0:
        print(repr(content[idx:idx+600]))
    else:
        print("'cabecalho = [' não encontrado no arquivo")
    sys.exit(1)
else:
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"\n✅ Todos os patches aplicados em {path}")
    print("\nPDF agora mostra: Unidade · Nome · Tel 1 · Tel 2 · Juizado · Total")
    print("Excel mantém todas as colunas financeiras.")