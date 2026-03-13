import os, sys
sys.path.insert(0, "/app/projeto_disparador")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django; django.setup()
from core.superlogica import buscar_inadimplentes_condominio, buscar_unidades
from datetime import datetime

data_hoje = datetime.today().strftime("%m/%d/%Y")
print(f"Buscando condominio 32 em {data_hoje}...")

mapa = buscar_unidades(32)
print(f"Unidades encontradas: {len(mapa)}")

resumo, detalhado = buscar_inadimplentes_condominio(32, data_hoje, mapa)
print(f"Unidades inadimplentes: {len(resumo)}")

# Mostra unidade 2196
if "2196" in resumo:
    v = resumo["2196"]
    print(f"\nUnidade 2196 (315 SALA):")
    print(f"  Principal:   R$ {v['principal']}")
    print(f"  Juros:       R$ {v['juros']}")
    print(f"  Multa:       R$ {v['multa']}")
    print(f"  Atualização: R$ {v['atualizacao']}")
    print(f"  Honorários:  R$ {v['honorarios']}")
    print(f"  TOTAL:       R$ {v['total']}")
    print(f"  Esperado:    R$ 335115.83")