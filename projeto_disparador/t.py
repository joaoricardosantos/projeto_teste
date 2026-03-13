import os, sys
sys.path.insert(0, "/app/projeto_disparador")
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
import django; django.setup()
import requests, json
from django.conf import settings

headers = {"app_token": settings.SUPERLOGICA_APP_TOKEN, "access_token": settings.SUPERLOGICA_ACCESS_TOKEN}

r = requests.get("https://api.superlogica.net/v2/condor/inadimplencia/avancada", headers=headers,
    params={"idCondominio": 79, "itensPorPagina": 5,
            "comEncargos": "true", "comHonorarios": "true", "comAtualizacaoMonetaria": "true"},
    timeout=60)

print(f"Status: {r.status_code}")
if r.status_code == 200:
    dados = r.json()
    if dados:
        det = dados[0].get("detalhes", {})
        print("detalhes:", json.dumps(det, indent=2))
        print("taxas:", json.dumps(dados[0].get("taxas", {}), indent=2))