# Guia do Desenvolvedor — Pratika Cobrança

> Guia completo para um novo desenvolvedor entrar no projeto. Pré-requisitos, setup, workflow, deploy e troubleshooting.
>
> Para visão de produto/features, veja `README.md` na raiz. Para histórico de mudanças e estado atual, veja `Contexto/CONTEXTO.md`.

---

## 📑 Índice

1. [Pré-requisitos](#1-pré-requisitos)
2. [Setup inicial](#2-setup-inicial)
3. [Rodando o projeto local](#3-rodando-o-projeto-local)
4. [Estrutura do projeto](#4-estrutura-do-projeto)
5. [Workflow de desenvolvimento](#5-workflow-de-desenvolvimento)
6. [Integrações externas](#6-integrações-externas)
7. [Deploy em produção](#7-deploy-em-produção)
8. [Tarefas comuns do dia a dia](#8-tarefas-comuns-do-dia-a-dia)
9. [Troubleshooting](#9-troubleshooting)
10. [Convenções e boas práticas](#10-convenções-e-boas-práticas)
11. [Contatos e recursos](#11-contatos-e-recursos)

---

## 1. Pré-requisitos

### Software

| Software | Versão | Por quê |
|---|---|---|
| **Docker Desktop** | última | Roda backend + frontend + banco em containers |
| **Git** | qualquer | Versionamento |
| **Node.js** | 20+ | Apenas se quiser rodar o frontend fora do Docker (opcional) |
| **Python** | 3.13 | Apenas se quiser rodar o backend fora do Docker (opcional) |
| Editor de código | — | Recomendado: VS Code com extensões Python, Vue, Vetur |

### Contas e acessos necessários

| Conta | Para quê | Quem fornece |
|---|---|---|
| **GitHub** | Acessar o repo | Solicitar ao João Ricardo |
| **Google Cloud Console** | Service account de Sheets/Drive | Compartilhado pela liderança |
| **Superlógica** | Tokens de API (já no `.env`) | Já configurado |
| **Evolution API (servidor)** | Reconectar WhatsApp em produção | API key compartilhada com a equipe |
| **SSH no servidor de produção** | Deploy (`186.202.209.150`) | Solicitar ao admin do projeto |

### Conhecimentos esperados

- **Backend**: Django, Django Ninja (REST), ORM, migrations, JWT
- **Frontend**: Vue 3 Composition API, Vuetify 3, Vite
- **Outros**: Docker Compose, PostgreSQL, integração com APIs externas
- **Domínio**: gestão de condomínios é nice-to-have (cobranças, inadimplência, execução jurídica)

---

## 2. Setup inicial

### 2.1 Clonar o repositório

```bash
git clone https://github.com/joaoricardosantos/projeto_teste.git pratika_cobranca
cd pratika_cobranca
```

### 2.2 Criar o arquivo `.env`

Existe um `.env` na raiz com todas as variáveis. **Não está no git** (está em `.gitignore`). Peça ao João Ricardo o `.env` atualizado, ou copie o template abaixo e preencha:

```bash
# Django
DJANGO_SECRET_KEY=development-secret-key-change-in-prod
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=*

# Banco
DB_HOST=db
DB_NAME=condo_db
DB_USER=postgres
DB_PASSWORD=postgres

# Evolution API (WhatsApp)
EVOLUTION_BASE_URL=http://evolution_api:8080
EVOLUTION_INSTANCE=Cobranca           # com C maiúsculo
EVOLUTION_API_KEY=<peça à equipe>
AUTHENTICATION_API_KEY=<mesma chave do EVOLUTION_API_KEY>

# Superlógica (já no .env atual)
SUPERLOGICA_BASE_URL=https://api.superlogica.net/v2/condor
SUPERLOGICA_APP_TOKEN="..."
SUPERLOGICA_ACCESS_TOKEN="..."
SUPERLOGICA_MAX_ID=100

# Google Drive (para integração de execução)
DRIVE_EXECUCOES_FOLDER_ID=<ID da pasta-mãe das execuções no Drive>
GOOGLE_SHEETS_CREDENTIALS_FILE=/app/credentials/google-sheets.json

# E-mail (reset de senha)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_USE_SSL=False
EMAIL_HOST_USER=joaoricardopratika@gmail.com
EMAIL_HOST_PASSWORD=<app password do Gmail>
DEFAULT_FROM_EMAIL=Pratika Cobranças <joaoricardopratika@gmail.com>
FRONTEND_URL=http://localhost:3000
```

### 2.3 Configurar credenciais do Google

Crie a pasta `credentials/` na raiz e coloque o arquivo `google-sheets.json` (service account):

```bash
mkdir -p credentials
# Coloque google-sheets.json aqui (peça ao João Ricardo)
```

> ⚠️ Esse JSON é **segredo**. Já está no `.gitignore`. Nunca commite.

A service account em uso atualmente é `sheets-reader@projetoteste-491111.iam.gserviceaccount.com` com escopos `spreadsheets.readonly` + `drive.readonly`.

### 2.4 Levantar os containers

```bash
docker compose up --build -d
```

Primeira execução: leva uns 3-5 minutos baixando imagens e instalando deps. Backend roda migrations automaticamente e cria o superusuário padrão.

### 2.5 Verificar se subiu

```bash
docker ps
# Deve listar 4 containers rodando: web, frontend, db, evolution_api
```

Acesse:
- Frontend: <http://localhost:3000>
- Backend API docs: <http://localhost:8000/api/docs>
- Evolution Manager: <http://localhost:8080/manager>

### 2.6 Login inicial

```
Email:  admin@admin.com
Senha:  admin123
```

> ⚠️ **Trocar essas credenciais** assim que possível em produção.

---

## 3. Rodando o projeto local

### Comandos do dia a dia

```bash
# Subir tudo
docker compose up -d

# Ver logs (live)
docker compose logs -f web              # backend
docker compose logs -f frontend         # frontend
docker compose logs -f evolution_api    # WhatsApp

# Reiniciar só um serviço
docker compose restart web

# Recriar um serviço (necessário ao mudar .env)
docker compose up -d --force-recreate web

# Parar tudo
docker compose down

# Parar e apagar volumes (banco zerado!)
docker compose down -v

# Rebuild quando mudou Dockerfile/requirements
docker compose up -d --build web
```

### Hot reload

- **Frontend**: Vite com `WATCHPACK_POLLING=true` no Docker — edita arquivo, recarrega na hora
- **Backend**: Django dev server **não está com auto-reload por padrão** — `gunicorn` em produção; para mudanças em `.py`, rode `docker compose restart web`

### Acessar o shell do backend

```bash
# Shell Django (ORM, models)
docker compose exec web python manage.py shell

# Bash dentro do container
docker compose exec web bash

# Rodar comando avulso
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

### Acessar o banco

```bash
docker compose exec db psql -U postgres -d condo_db
# Comandos úteis:
# \dt           — listar tabelas
# \d core_user  — descrever tabela
# \q            — sair
```

---

## 4. Estrutura do projeto

```
pratika_cobranca/
├── docker-compose.yml          # Orquestração dos containers
├── Dockerfile                  # Imagem do backend Python
├── evolution.env               # Config Evolution (WhatsApp)
├── requirements.txt            # Deps Python
├── .env                        # Variáveis de ambiente (NÃO versionado)
├── credentials/
│   └── google-sheets.json      # Service account Google (NÃO versionado)
│
├── README.md                   # Visão geral do produto e features
├── INTEGRACAO_GOOGLE_SHEETS.md # (vazio — TODO documentar)
├── Contexto/
│   ├── CONTEXTO.md             # Snapshot/histórico do projeto
│   └── GUIA_DESENVOLVEDOR.md   # Este arquivo
│
├── projeto_disparador/         # Backend Django
│   ├── manage.py
│   └── core/
│       ├── settings.py         # Config Django
│       ├── urls.py             # Rotas globais (registra os routers)
│       ├── api.py              # Definição da api ninja
│       ├── auth.py             # JWT + permissões
│       │
│       ├── models.py           # TODOS os models do Django
│       ├── admin.py            # Configuração do Django admin
│       │
│       ├── # ─── Routers Ninja (cada um responde por /api/<area>) ───
│       ├── admin_api.py        # /api/admin
│       ├── campanha_api.py     # /api/campanhas
│       ├── message_api.py      # /api/messages
│       ├── template_api.py     # /api/templates
│       ├── juridico_api.py     # /api/juridico
│       ├── financeiro_api.py   # /api/financeiro
│       ├── sheets_api.py       # /api/sheets
│       ├── agenda_api.py       # /api/agenda
│       ├── execucao_api.py     # /api/execucao  (Geração DOCX/PDF + Drive)
│       ├── sindico_api.py      # /api/sindicos
│       ├── webhook_api.py      # /api/webhooks  (Evolution callbacks)
│       ├── planilha_funcionario_api.py  # /api/planilhas
│       │
│       ├── # ─── Serviços (lógica de integração externa) ───
│       ├── superlogica.py      # Wrapper API Superlógica
│       ├── evolution_service.py # Wrapper Evolution API (WhatsApp)
│       ├── sheets_service.py   # Wrapper Google Sheets
│       ├── drive_service.py    # Wrapper Google Drive (NOVO)
│       ├── condominio_service.py # Lógica de condomínio
│       ├── services.py         # Genéricos (envio mensagens, etc.)
│       │
│       └── migrations/         # 0001 → 0025
│
├── frontend/                   # Vue 3 + Vuetify 3 + Vite
│   ├── Dockerfile
│   ├── vite.config.js
│   ├── package.json
│   ├── public/
│   │   ├── modelo_execucao.docx
│   │   ├── modelo_execucao_honorarios.docx
│   │   └── modelo_justicaComum.docx
│   └── src/
│       ├── App.vue             # Layout + sidebar
│       ├── main.js             # Bootstrap Vue + Vuetify
│       ├── router/index.js     # Rotas frontend
│       ├── composables/        # Hooks reutilizáveis (useCondominios, etc.)
│       └── views/              # Uma view por aba do sistema
│           ├── DashboardView.vue
│           ├── ExecucaoView.vue          # Execução jurídica
│           ├── PlanilhasView.vue         # Dashboard planilhas funcionários
│           ├── CampanhasAba.vue
│           ├── ... (outras 10+ views)
│           └── AuthView.vue
```

### Mapa: "onde mexer pra fazer X"

| Quero... | Vai em |
|---|---|
| Adicionar/alterar campo do banco | `core/models.py` + criar migration |
| Adicionar endpoint REST | Cria/edita um `*_api.py` em `core/` e registra em `core/urls.py` |
| Mudar tela do frontend | `frontend/src/views/<NomeDaView>.vue` |
| Mudar sidebar | `frontend/src/App.vue` |
| Adicionar rota frontend | `frontend/src/router/index.js` |
| Mudar lógica de envio WhatsApp | `core/evolution_service.py` |
| Mudar parsing/integração Sheets | `core/sheets_service.py` |
| Mudar parsing Drive | `core/drive_service.py` |
| Buscar dados Superlógica | `core/superlogica.py` |
| Mudar template DOCX da execução | `frontend/public/modelo_*.docx` |

---

## 5. Workflow de desenvolvimento

### 5.1 Criar uma nova feature

```bash
# Ainda na main (não há branches por feature por convenção do projeto, embora seja recomendado)
git pull
# ...mexe no código...
docker compose restart web   # se mudou .py
# Testa no navegador

# Criar migration se mexeu em models.py
docker compose exec web python manage.py makemigrations core
docker compose exec web python manage.py migrate

# Commitar
git add <arquivos>
git commit -m "feat: descrição do que faz"
git push
```

### 5.2 Criar uma migration

Sempre que mudar `models.py`:

```bash
docker compose exec web python manage.py makemigrations core
# Vai criar arquivo em core/migrations/0026_xxx.py
docker compose exec web python manage.py migrate
```

⚠️ **Sempre commite o arquivo de migration junto com a mudança em `models.py`**, senão outros devs (e produção) vão quebrar.

### 5.3 Criar um endpoint novo

1. Abre o `*_api.py` da área (ou cria um novo)
2. Define schemas (Pydantic via Ninja `Schema`)
3. Cria a função decorada com `@router.get/post/...`
4. Se for novo router, registra em `core/urls.py`:
   ```python
   from core.meu_novo_api import meu_router
   api.add_router("/meu", meu_router)
   ```
5. Recarrega: `docker compose restart web`

### 5.4 Criar uma nova view no frontend

1. Cria `frontend/src/views/MinhaView.vue`
2. Adiciona rota em `frontend/src/router/index.js`
3. Adiciona link na sidebar em `frontend/src/App.vue`
4. Vite faz hot reload automaticamente

### 5.5 Estilo de commits

Convenção informal usada no projeto (Conventional Commits):

```
feat: nova funcionalidade
fix: correção de bug
refactor: mudança que não altera comportamento
chore: tarefas administrativas (deps, configs, etc.)
docs: documentação
```

Mensagens em **português** seguindo os exemplos do `git log`.

---

## 6. Integrações externas

### 6.1 Superlógica (ERP de condomínios)

- Tokens em `.env` (`SUPERLOGICA_APP_TOKEN`, `SUPERLOGICA_ACCESS_TOKEN`)
- Wrapper: `core/superlogica.py`
- Endpoints usados: `/condor/condominios`, `/condor/unidades`, `/condor/inadimplencia/avancada`, etc.
- Rate limit: a API é lenta — tem retry automático de 6x com backoff

### 6.2 Evolution API (WhatsApp)

- URL: `http://evolution_api:8080` (rede interna do compose) ou `http://localhost:8080` (host)
- Instância em uso: `Cobranca` (com C maiúsculo)
- API Key: igual à variável `EVOLUTION_API_KEY` no `.env`
- Manager UI: <http://localhost:8080/manager>
- Wrapper: `core/evolution_service.py`

#### Conectar/reconectar WhatsApp

```bash
# Pelo Manager UI (recomendado): http://localhost:8080/manager
# Login com a API key, encontra a instance "Cobranca", clica em Connect/QR

# Ou via API:
curl -X DELETE "http://localhost:8080/instance/delete/Cobranca" -H "apikey: $EVOLUTION_API_KEY"
docker restart evolution_api && sleep 15
curl -X POST "http://localhost:8080/instance/create" \
  -H "Content-Type: application/json" -H "apikey: $EVOLUTION_API_KEY" \
  -d '{"instanceName":"Cobranca","qrcode":true,"integration":"WHATSAPP-BAILEYS"}'
# Pega o QR ou pairingCode do retorno e escaneia/digita no celular
```

#### Anti-spam (configurado em `settings.py`)

- `WA_DELAY_MIN`/`WA_DELAY_MAX`: delay aleatório entre mensagens (default 20-45s)
- `WA_TYPING_MIN_MS`/`WA_TYPING_MAX_MS`: simulação de digitação (3-8s)

### 6.3 Google Sheets (planilhas dos funcionários)

- Service account: `sheets-reader@projetoteste-491111.iam.gserviceaccount.com`
- Credencial: `credentials/google-sheets.json`
- Wrapper: `core/sheets_service.py`
- **Cada planilha precisa ser compartilhada** com o email do service account como Leitor

### 6.4 Google Drive (modelos de execução)

- Mesma service account do Sheets
- Wrapper: `core/drive_service.py`
- **A pasta-mãe (`DRIVE_EXECUCOES_FOLDER_ID`) precisa estar no Meu Drive** do dono — ⚠️ não funciona em "Compartilhados comigo"
- A pasta precisa ser **compartilhada com o service account** como Leitor
- Estrutura esperada:
  ```
  DRIVE_EXECUCOES_FOLDER_ID (pasta-mãe)
  ├── 18 - JANGADAS/
  │   └── 01 - Modelos/      ← arquivos daqui são anexados
  ├── 19 - PORTO AZUL/
  │   └── 01 - Modelos/
  └── ...
  ```
- Auto-match: o backend procura uma subpasta cujo nome **contenha** o nome do condomínio (case-insensitive, ignora acentos). Se não bate, pode mapear manualmente via `CondominioDriveMap` (admin ou pela própria UI).

---

## 7. Deploy em produção

### 7.1 Servidor

- IP: `186.202.209.150`
- Usuário SSH: `root`
- Pasta do projeto: `/root/`
- Containers: `root-web-1`, `root-frontend-1`, `root-db-1`, `evolution_api`

### 7.2 Acesso SSH

```bash
ssh root@186.202.209.150
```

> 💡 **Dica**: configure SSH key para evitar digitar senha toda vez. Adicione sua chave pública em `~/.ssh/authorized_keys` no servidor.

### 7.3 Deploy completo

```bash
ssh root@186.202.209.150
cd /root

# Atualiza código
git pull

# Se mudou .env, atualize aqui (usar nano ou vim)
# nano .env

# Aplica mudanças
docker compose up -d --force-recreate web frontend

# Verifica logs
docker logs --tail 50 root-web-1
docker logs --tail 50 root-frontend-1
```

### 7.4 Rollback

```bash
git log --oneline    # ver commits
git checkout <hash-anterior>
docker compose up -d --force-recreate web frontend
```

### 7.5 Cuidados

- ⚠️ `docker compose restart` **não recarrega `.env`** — sempre use `up -d --force-recreate` ao mudar variável
- Migrations rodam automaticamente no comando do `docker-compose.yml` (`makemigrations + migrate` antes do gunicorn)
- O frontend de produção é buildado e servido pelo container `root-frontend-1`
- Se a build do frontend falhar, o container fica em loop — verifique `docker logs root-frontend-1`

### 7.6 Backup do banco

```bash
# No servidor
docker compose exec db pg_dump -U postgres condo_db > backup_$(date +%Y%m%d).sql

# Restaurar
docker compose exec -T db psql -U postgres condo_db < backup_20260428.sql
```

---

## 8. Tarefas comuns do dia a dia

### 8.1 Criar um usuário admin via shell

```bash
docker compose exec web python manage.py shell
```

```python
from core.models import User
User.objects.create_superuser('email@exemplo.com', 'senha', name='Nome Completo')
```

### 8.2 Aprovar usuário (is_approved)

```python
from core.models import User
u = User.objects.get(email='usuario@exemplo.com')
u.is_approved = True
u.save()
```

### 8.3 Resetar senha de admin via shell

```python
from core.models import User
u = User.objects.get(email='admin@admin.com')
u.set_password('nova_senha')
u.save()
```

### 8.4 Listar mapeamentos Drive

```python
from core.models import CondominioDriveMap
for m in CondominioDriveMap.objects.all():
    print(m.condominio_id, m.condominio_nome, m.drive_folder_nome)
```

### 8.5 Conectar/reconectar WhatsApp em produção

Veja seção [6.2](#62-evolution-api-whatsapp), os comandos são os mesmos só trocando `localhost` por `186.202.209.150`.

### 8.6 Adicionar uma planilha de funcionário

1. No sistema, tela "Planilhas" → "Gerenciar Planilhas" (admin only)
2. Clica em "+ Nova"
3. Seleciona o funcionário, dá um nome e cola o **ID da planilha** (parte da URL entre `/d/` e `/edit`)
4. **Compartilha a planilha** no Google Sheets com `sheets-reader@projetoteste-491111.iam.gserviceaccount.com` como Leitor

### 8.7 Ver qual aba do Sheets/Drive um funcionário está vendo

Os endpoints expostos para debug:
- `GET /api/planilhas/configs` — lista de configs (admin)
- `GET /api/planilhas/configs/{id}/abas` — abas de uma planilha
- `GET /api/planilhas/configs/{id}/dashboard?aba=Planilha1` — dados processados

---

## 9. Troubleshooting

### "Não consigo conectar no Docker"
```bash
# Windows: Docker Desktop precisa estar rodando
# Reinicie o Docker Desktop pelo ícone na bandeja
```

### "docker compose restart não fez efeito"
Você mudou `.env`? `restart` não recarrega variáveis. Use:
```bash
docker compose up -d --force-recreate <serviço>
```

### "Erro 500 ao enviar WhatsApp / Connection Closed"
A sessão Evolution caiu. Veja seção [6.2](#62-evolution-api-whatsapp) — delete + recreate a instance.

### "Service account não vê pastas do Drive"
- Conferir se a pasta está no **Meu Drive** do dono (não em "Compartilhados comigo")
- Conferir se o SA está como Leitor na pasta (Compartilhar > olhar a lista)
- Conferir se a Drive API está ativa no projeto Google Cloud
- Pasta dentro de Shared Drive: adicionar SA como **membro do Shared Drive**, não da pasta

### "Pasta encontrada mas 0 arquivos no ZIP"
Auto-match parou na pasta do condomínio mas não entrou em `01 - Modelos`. Use "Trocar pasta" no UI e navegue até a subpasta com arquivos. Salva o mapeamento.

### "Dashboard de planilhas todo zerado"
- Verifique se a planilha tem a coluna `CONDOMÍNIO` (case-insensitive, exato)
- Verifique se as datas estão em formato reconhecido (`DD/MM/YYYY`, `DD/MM/YY`, etc.)
- Para PRAZO BOLETO, aceita só o **dia do mês** (ex: "30") — usa mês da geração como referência

### "Migrations conflitando"
```bash
# Liste pendentes
docker compose exec web python manage.py showmigrations core

# Se tiver migrations duplicadas (números iguais), faça merge:
docker compose exec web python manage.py makemigrations --merge
```

### "Frontend não atualiza ao salvar"
- Confira se `WATCHPACK_POLLING=true` está no `docker-compose.yml`
- Force restart: `docker compose restart frontend`

### "Backend não atualiza ao salvar .py"
Esperado — gunicorn não tem auto-reload. Sempre rode `docker compose restart web` após mudar Python.

### "Superlógica timeout"
A API é lenta às vezes. O wrapper tem retry de 6x. Se persistir, provavelmente é instabilidade do Superlógica — verifique no `status.superlogica.com.br`.

### "Login inválido"
- Confira se o usuário tem `is_approved=True`
- Se for admin, `is_staff=True` e `is_superuser=True`

### Logs úteis
```bash
docker logs --tail 100 -f pratika_cobranca-web-1       # local
docker logs --tail 100 -f root-web-1                   # produção
docker logs --tail 100 -f evolution_api                # WhatsApp
```

---

## 10. Convenções e boas práticas

### Backend

- **Type hints**: em handlers Ninja, use sempre Schema/Pydantic
- **Erros HTTP**: use `from ninja.errors import HttpError; raise HttpError(400, "msg")`
- **Auth**: routers protegidos têm `auth=JWTAuth()` no decorator
- **Logs**: `logger = logging.getLogger(__name__)` e `logger.info/error/...`

### Frontend

- **Composition API**: use `<script setup>` (Vue 3 idiomatic)
- **Composables**: lógica reutilizável vai em `composables/` (ex: `useCondominios`)
- **Vuetify**: prefira componentes Vuetify (`v-btn`, `v-card`, `v-data-table`) sobre HTML puro
- **Responsividade**: `v-col cols="12" md="6"` para layouts adaptáveis

### Geral

- Mensagens de UI em **português**
- Datas no formato **DD/MM/YYYY** (consistência com Superlógica/Sheets)
- Valores monetários sempre `Decimal` no backend e formatados no frontend (`R$ 1.234,56`)
- Não commite `.env`, `credentials/`, `node_modules/`, arquivos `.docx` gerados

---

## 11. Contatos e recursos

### Time
- **João Ricardo** (owner do repo, líder do projeto)
- **Paulo Henrique** (Dono original / contexto histórico)

### Documentação
- **Django Ninja**: <https://django-ninja.dev/>
- **Vuetify 3**: <https://vuetifyjs.com/>
- **Evolution API v2**: <https://doc.evolution-api.com/v2/api-reference/get-started/introduction>
- **Superlógica API**: <https://help.superlogica.com/hc/pt-br/categories/360002106473>
- **Google Sheets API**: <https://developers.google.com/sheets/api>
- **Google Drive API**: <https://developers.google.com/drive/api>

### Repositórios e ambientes
- **Repo**: <https://github.com/joaoricardosantos/projeto_teste>
- **Produção (frontend)**: `http://186.202.209.150` (porta dependendo do nginx/proxy)
- **Produção (backend)**: `http://186.202.209.150:8000`
- **Evolution Manager**: `http://186.202.209.150:8080/manager`

### Pra começar
1. Leia `README.md` (visão de produto)
2. Leia `Contexto/CONTEXTO.md` (estado atual e histórico)
3. Faça o setup deste guia (seções 1-3)
4. Explore o código a partir de `frontend/src/App.vue` (sidebar) → entra em cada view
5. Backend: comece por `core/urls.py` → cada `*_api.py`

Boa jornada! 🚀
