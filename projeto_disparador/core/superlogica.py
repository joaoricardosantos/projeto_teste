import time
from datetime import datetime
from io import BytesIO

import requests
from django.conf import settings
from openpyxl import Workbook


def _get_headers() -> dict:
  return {
      "Content-Type": "application/json",
      "app_token": settings.SUPERLOGICA_APP_TOKEN,
      "access_token": settings.SUPERLOGICA_ACCESS_TOKEN,
  }


def verificar_condominio(id_condominio: int):
  response = requests.get(
      f"{settings.SUPERLOGICA_BASE_URL}/unidades",
      headers=_get_headers(),
      params={
          "idCondominio": id_condominio,
          "pagina": 1,
          "itensPorPagina": 1,
      },
      timeout=20,
  )

  if response.status_code != 200:
      return False, None

  dados = response.json()
  nome_condominio = None

  if dados and isinstance(dados, list):
      nome_condominio = dados[0].get("st_nome_cond")

  return True, nome_condominio


def buscar_unidades(id_condominio: int):
  mapa = {}
  pagina = 1

  while True:
      response = requests.get(
          f"{settings.SUPERLOGICA_BASE_URL}/unidades",
          headers=_get_headers(),
          params={
              "idCondominio": id_condominio,
              "pagina": pagina,
              "itensPorPagina": 50,
          },
          timeout=30,
      )

      if response.status_code != 200:
          return None

      dados = response.json()

      if not dados:
          break

      for unidade in dados:
          unidade_id = unidade.get("id_unidade_uni")

          telefones = []
          for campo in ["telefone_proprietario", "celular_proprietario"]:
              numero = unidade.get(campo)
              if numero and str(numero).strip():
                  telefones.append(str(numero).strip())

          mapa[unidade_id] = {
              "nome": unidade.get("nome_proprietario"),
              "telefones": list(dict.fromkeys(telefones)),
          }

      pagina += 1

  return mapa


def extrair_valor_com_juros(receb: dict) -> float:
  encargos = receb.get("encargos", [])

  if encargos and isinstance(encargos, list):
      valor_corrigido = encargos[0].get("valorcorrigido")

      if valor_corrigido not in (None, "", "0", "0.00"):
          try:
              return float(str(valor_corrigido).replace(",", "."))
          except ValueError:
              pass

  try:
      return float(str(receb.get("vl_total_recb", 0)).replace(",", "."))
  except ValueError:
      return 0.0


def buscar_inadimplentes(id_condominio: int, data_posicao: str):
  pessoas = {}
  pagina = 1

  while True:
      response = requests.get(
          f"{settings.SUPERLOGICA_BASE_URL}/inadimplencia/index",
          headers=_get_headers(),
          params={
              "idCondominio": id_condominio,
              "pagina": pagina,
              "itensPorPagina": 50,
              "posicaoEm": data_posicao,
              "comValoresAtualizados": 1,
              "comValoresAtualizadosPorComposicao": 1,
          },
          timeout=30,
      )

      if response.status_code != 200:
          return None

      dados = response.json()

      if not dados:
          break

      for item in dados:
          for receb in item.get("recebimento", []):
              if receb.get("fl_status_recb") != "0":
                  continue

              unidade_id = receb.get("id_unidade_uni")
              valor = extrair_valor_com_juros(receb)

              pessoas[unidade_id] = pessoas.get(unidade_id, 0) + valor

      pagina += 1

  return pessoas


def gerar_relatorio_inadimplentes() -> tuple[bytes, str] | tuple[None, None]:
  """
  Varre os condomínios configurados e gera um arquivo Excel em memória
  com todos os inadimplentes e seus valores em aberto.
  """
  todas_dividas: list[dict] = []

  max_id = getattr(settings, "SUPERLOGICA_MAX_ID", 100)
  data_posicao = getattr(
      settings,
      "SUPERLOGICA_DATA_POSICAO",
      datetime.today().strftime("%d/%m/%Y"),
  )

  for id_condominio in range(1, max_id + 1):
      acesso, nome_condominio = verificar_condominio(id_condominio)

      if not acesso:
          continue

      inadimplentes = buscar_inadimplentes(id_condominio, data_posicao)
      if not inadimplentes:
          continue

      mapa_unidades = buscar_unidades(id_condominio)
      if not mapa_unidades:
          continue

      for unidade_id, total in inadimplentes.items():
          dados_unidade = mapa_unidades.get(unidade_id, {})

          nome = dados_unidade.get("nome", "Nome não encontrado")
          telefones = dados_unidade.get("telefones", [])

          todas_dividas.append(
              {
                  "Condomínio": nome_condominio,
                  "Nome": nome,
                  "Telefones": " | ".join(telefones) if telefones else "",
                  "Valor da dívida com juros": round(float(total), 2),
              }
          )

      # pequena pausa para evitar sobrecarga na API externa
      time.sleep(0.3)

  if not todas_dividas:
      return None, None

  # Ordena por valor da dívida
  todas_dividas.sort(
      key=lambda item: item["Valor da dívida com juros"], reverse=True
  )

  wb = Workbook()
  ws = wb.active
  ws.title = "Inadimplentes"

  headers = ["Condomínio", "Nome", "Telefones", "Valor da dívida com juros"]
  ws.append(headers)

  for linha in todas_dividas:
      ws.append(
          [
              linha["Condomínio"],
              linha["Nome"],
              linha["Telefones"],
              linha["Valor da dívida com juros"],
          ]
      )

  buffer = BytesIO()
  wb.save(buffer)
  buffer.seek(0)

  filename = f"inadimplentes_condominios_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
  return buffer.getvalue(), filename

