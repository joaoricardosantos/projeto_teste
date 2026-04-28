# Pratika Cobrança — Handoff / Contexto Completo

> **Objetivo**: permitir que outra Claude, em outra máquina, continue o trabalho **exatamente** de onde Paulo Henrique parou.

---

## 1. Snapshot do estado atual (28/04/2026)

| Campo | Valor |
|---|---|
| Pasta | `pratika_cobranca` |
| Repositório | `https://github.com/joaoricardosantos/projeto_teste.git` |
| Branch atual | `main` |
| Local vs `origin/main` | **Em sincronia** (0 ahead / 0 behind) — tudo pushado! |
| Último commit | `67f8207 feat: integra Google Drive na execucao para anexar modelos do condominio` |
| Working tree | **Limpo** (só `Contexto/` untracked) |
| **Produção vs main** | ⚠️ **DESATUALIZADO** — features novas (Drive, dashboard de planilhas, fix prazo boleto) ainda **não foram deployadas em produção** |
| Servidor produção | `186.202.209.150` (root), Docker em `/root/`, containers prefixados `root-*` |
| WhatsApp produção | ✅ **Conectado** (instance `Cobranca`, reconectado em 28/04/2026) |

### Últimos commits

```
67f8207 feat: integra Google Drive na execucao para anexar modelos do condominio ← NOVO
87af68a fix: corrige dashboard de planilhas - prazo boleto por dia do mês e cards zerados
03bb14b feat: dashboard fixo de planilha com KPIs e tabela visual
2de2ce4 refactor: integra planilhas dos funcionários com Google Sheets
8dc1089 feat: adiciona dashboard de planilhas dos funcionários
12f01fd chore: ajusta espacamento do modelo Justica Comum
3bbdc98 feat: adiciona modelo de peticao 'Justica Comum' na execucao
1e4b7f4 chore: remove frontend/node_modules do tracking
7ead0d8 feat: categoriza menu lateral, melhora fila de pagamento e corrige bugs
928f7e8 Update README.md
```

---

## 2. O que mudou desde o último snapshot (18/04 → 28/04)

### 2.1 NOVIDADE — Integração Google Drive na Execução

Commit `67f8207` — funcionalidade significativa (+765 linhas).

**O que faz**: ao gerar documentos de execução de cobrança (DOCX/PDF), o sistema agora pode **anexar modelos (documentos) armazenados no Google Drive** de cada condomínio. A estrutura esperada no Drive é:

```
{DRIVE_EXECUCOES_FOLDER_ID}/
├── 18 - JANGADAS/
│   └── 01 - Modelos/   ← arquivos daqui são anexados
├── 19 - OUTRO/
│   └── 01 - Modelos/
└── ...
```

#### Novo arquivo: `projeto_disparador/core/drive_service.py` (216 linhas)
- Usa `google-auth` + `googleapiclient` (mesmas credenciais do Google Sheets)
- Escopos: `spreadsheets.readonly` + `drive.readonly`
- Busca pastas de condomínios pelo nome, navega até subpasta `"Modelos"`, lista e baixa arquivos
- Suporta Google Docs/Sheets/Slides nativos (converte para PDF/xlsx/pptx no download)
- Busca por hints de nome: `("modelo", "modelos")` case-insensitive + unidecode

#### Novo model: `CondominioDriveMap`
```python
class CondominioDriveMap(models.Model):
    condominio_id     = models.IntegerField(unique=True)
    condominio_nome   = models.CharField(max_length=255, blank=True)
    drive_folder_id   = models.CharField(max_length=200)
    drive_folder_nome = models.CharField(max_length=255, blank=True)
    criado_em         = DateTimeField(auto_now_add)
    atualizado_em     = DateTimeField(auto_now)
```
Mapeia um condomínio (por ID Superlógica) para uma pasta específica no Google Drive. Permite override manual caso o nome da pasta no Drive não bata com o nome no Superlógica.

**Migrations**: `0024_condominio_drive_map.py`, `0025_alter_condominiodrivemap_id.py`

#### Mudanças no backend: `execucao_api.py` (+249 linhas)
- Endpoints de geração de execução agora consultam `CondominioDriveMap` para buscar modelos do Drive
- Arquivos do Drive são baixados e incluídos no ZIP de saída junto com os DOCX/PDF gerados

#### Mudanças no frontend: `ExecucaoView.vue` (+247 linhas)
- UI para visualizar e selecionar modelos do Google Drive por condomínio
- Integração com o fluxo de geração de execução existente

#### Nova configuração: `settings.py`
- 1 nova setting: `DRIVE_EXECUCOES_FOLDER_ID` (lido de env var, default `""`)
- Valor atual em uso (local): `1TBlbsMlzjXcR5DAFjQqEmRJoCrrbGWF6` (pasta "01 - EXECUÇÕES" no Meu Drive do João Ricardo)

#### Endpoints novos em `execucao_api.py`
- `GET /api/execucao/drive/buscar-pasta?id_condominio=X&nome_condominio=Y`
  Retorna `status: ok|ambiguo|nao_encontrada|nao_configurado|erro` + folder_id/name
  Prioridade: mapeamento manual no banco > match automático por nome (slug substring case-insensitive)
- `GET /api/execucao/drive/listar-subpastas?parent_id=X` — lista subpastas (raiz se omitir)
- `POST /api/execucao/drive/mapeamento` — salva/atualiza `CondominioDriveMap`
- `DELETE /api/execucao/drive/mapeamento/{id_condominio}` — remove mapeamento
- `GET /api/execucao/drive/diagnostico?folder_id=X` — debug (metadata + listagem de itens visíveis pelo SA)
- `gerar-docx` e `gerar-pdf` aceitam `incluir_modelos_drive: bool` + `drive_folder_id: str` no payload. Se marcado, **sempre** retorna ZIP (mesmo 1 unidade) com pasta `modelos/` contendo os arquivos do Drive.

#### UI no `ExecucaoView.vue`
- Card "Modelos do Drive" mostra status ao buscar condomínio
- Dialog "Trocar pasta" tem **breadcrumb navegável** + botão "entrar na subpasta" (ícone →) — permite navegar até `01 - Modelos` dentro de `18 - JANGADAS` e selecionar
- Mapeamento manual é persistido em `CondominioDriveMap` para próximas execuções

### 2.3 Fix do dashboard de planilhas — commit `87af68a`

- **Bug 1**: campo "PRAZO BOLETO" da planilha do funcionário pode conter apenas o **dia do mês** (ex: `"30"`). Antes, `_parse_date("30")` retornava `None` e o status virava `'none'`, fazendo os boletos não entrarem nos KPIs.
- **Fix**: nova função `_prazo_boleto_date(prazo_str, ref)` em `planilha_funcionario_api.py` que aceita data completa OU só o dia, usando o mês/ano da **data de geração do boleto** como referência (fallback: hoje).
- **Bug 2**: API retornava só `kpis` mas não `resumo` e `pipeline` em alguns casos → frontend dava TypeError silencioso e não renderizava nada.
- **Fix**: computed `dash` no `PlanilhasView.vue` deriva `resumo` (de `kpis`) e `pipeline` (de `linhas`) localmente como fallback, mantendo o dashboard resiliente.
- **Bug 3**: alinhamento do botão "atualizar" desalinhado por causa do label flutuante do v-select → adicionado `hide-details` no select.

### 2.2 Tudo do snapshot anterior (já pushado)
- Sidebar categorizada ✅
- Módulo Planilhas dos Funcionários ✅
- Modelo Justiça Comum ✅
- `node_modules` removidos do tracking ✅

---

## 3. Onde parei / Próximos passos

### O que acabou de ser feito (28/04/2026)
- ✅ Integração Google Drive na execução — completa, testada localmente, **pushada**
- ✅ Fix do dashboard de planilhas (prazo boleto + cards zerados)
- ✅ WhatsApp em produção reconectado (instance `Cobranca`)
- ✅ `EVOLUTION_API_KEY` em produção corrigida (`m6zlm4vfowg7i8y4citjvn`)
- Working tree limpo — **nada pendente em git**

### ⚠️ Pendências críticas
1. **DEPLOY EM PRODUÇÃO** — features novas (Drive + dashboard) ainda **não estão no servidor**. Como fazer:
   ```bash
   # Local: confirmar git push (já feito)
   # No servidor:
   ssh root@186.202.209.150
   cd /root
   git pull
   docker compose up -d --force-recreate web frontend
   # Migrações 0024 e 0025 rodam automaticamente (no comando do docker-compose.yml)
   # Definir DRIVE_EXECUCOES_FOLDER_ID no /root/.env antes do up
   ```
   Cuidado: `restart` **não recarrega `.env`** — precisa `up -d --force-recreate`.

2. **Migração de credenciais Google** — bloqueada pela política `iam.disableServiceAccountKeyCreation` do Workspace `dr-nuvio`.
   - Atualmente usa `sheets-reader@projetoteste-491111.iam.gserviceaccount.com` (projeto antigo, fora da org)
   - Tentou-se criar service account em projeto novo `dr-nuvio` mas Google bloqueou geração de chave JSON
   - **Soluções possíveis**:
     a) Admin do Workspace desativa a constraint para o projeto
     b) Criar projeto novo fora da organização (Gmail pessoal)
     c) Workload Identity Federation (não aplicável — backend roda em VPS, não em GCP)

### Próximos passos sugeridos
1. **Deploy** das features novas em produção (ver acima)
2. **Configurar `DRIVE_EXECUCOES_FOLDER_ID`** no `.env` de produção
3. **Compartilhar pasta de produção** com o service account (`sheets-reader@projetoteste-491111.iam.gserviceaccount.com` como Leitor)
4. **Popular `CondominioDriveMap`** para os condomínios cujo nome no Superlógica não bate com o nome da pasta no Drive (ex: "CONDOMINIO RESIDENCIAL JANGADAS E CARAVELAS" vs "18 - JANGADAS" — auto-match falha porque o slug do nome longo não está contido no slug curto)
5. **`INTEGRACAO_GOOGLE_SHEETS.md`** continua **vazio** — documentar setup de Sheets + agora Drive
6. **Testes automatizados** — zero cobertura
7. **Segurança**: trocar credenciais padrão (`admin@admin.com` / `admin123`)
8. **CI/CD** — sem pipeline (`git pull && docker compose up` é manual)
9. **Revisar views pouco documentadas**: `LevantamentoView.vue`, `PainelView.vue`

---

## 4. Identidade

- **Produto**: Sistema de Gestão de Cobranças — Pratika
- **Cliente**: Pratika (administradora de condomínios)
- **Owner**: Paulo Henrique (João Ricardo como repo owner)
- **Licença**: MIT © 2026 João Ricardo
- **Comunicação**: pt-BR

## 5. Stack

| Camada | Tecnologias |
|---|---|
| Backend | Python 3.13, Django 6.0, Django-Ninja 1.5 |
| Autenticação | PyJWT |
| Banco | PostgreSQL 16 |
| Frontend | Vue.js 3 Composition API, Vuetify 3, Vite |
| Infra | Docker + Docker Compose |
| Integrações | API Superlógica, Evolution API (WhatsApp), Google Sheets API, **Google Drive API** ← NOVO |
| Relatórios | openpyxl (Excel), ReportLab (PDF), python-docx (DOCX) |

## 6. Estrutura (atualizada)

```
pratika_cobranca/
├── docker-compose.yml, Dockerfile, evolution.env
├── README.md, requirements.txt
├── INTEGRACAO_GOOGLE_SHEETS.md         # ⚠️ VAZIO
├── patch_pdf_colunas_v2.py, patch_superlogica.py
├── projeto_disparador/
│   └── core/
│       ├── models.py                   # User, MessageTemplate, Campanha, MensagemEnviada,
│       │                               # AdvogadoPlanilha, PlanilhaFuncionarioConfig,
│       │                               # CondominioDriveMap ← NOVO
│       ├── auth.py, api.py
│       ├── admin_api.py, campanha_api.py, message_api.py
│       ├── template_api.py, juridico_api.py, financeiro_api.py
│       ├── sheets_api.py, agenda_api.py
│       ├── execucao_api.py             # atualizado: integração Drive
│       ├── sindico_api.py, webhook_api.py
│       ├── planilha_funcionario_api.py
│       ├── drive_service.py            # ← NOVO (Google Drive integration)
│       ├── services.py, evolution_service.py, superlogica.py, sheets_service.py
│       ├── settings.py                 # +3 settings Drive
│       ├── urls.py
│       └── migrations/
│           ├── ... (0001–0023 existentes)
│           ├── 0024_condominio_drive_map.py     # ← NOVO
│           └── 0025_alter_condominiodrivemap_id.py  # ← NOVO
├── frontend/
│   ├── Dockerfile
│   ├── public/modelo_justicaComum.docx
│   └── src/
│       ├── App.vue                     # Sidebar categorizada
│       ├── main.js, router/index.js
│       └── views/
│           ├── PlanilhasView.vue       # Dashboard planilhas funcionários
│           ├── ExecucaoView.vue        # atualizado: UI de modelos Drive
│           ├── DashboardView.vue, ReportsView.vue, CampanhasAba.vue
│           ├── TemplatesView.vue, AdminView.vue, JuridicoView.vue
│           ├── FinanceiroView.vue, AgendaView.vue, SheetsView.vue
│           ├── SindicosView.vue, LevantamentoView.vue, PainelView.vue
│           └── AuthView.vue
└── credentials/google-sheets.json      # NÃO versionar (agora também usado pelo Drive)
```

## 7. Modelos Django (atualizado)

- `User` — auth customizado, `is_staff`, `is_superuser`, `is_approved`
- `MessageTemplate` — templates WhatsApp
- `Campanha` — agrupa disparos
- `MensagemEnviada` — status/histórico
- `AdvogadoPlanilha` — advogado ↔ spreadsheet_id + aba
- `PlanilhaFuncionarioConfig` — funcionário ↔ spreadsheet_id
- **`CondominioDriveMap`** — condomínio_id ↔ drive_folder_id ← NOVO

## 8. Módulos funcionais (atualizado)

### Módulos existentes (inalterados)
Dashboard inadimplência, Jurídico, Financeiro, Recebimentos (Sheets), Agenda, Síndicos, Relatórios, Mensagens WhatsApp, Planilhas dos Funcionários

### Execução de Cobrança (atualizado)
- Gera DOCX/PDF em lote por unidade
- **Modelos Justiça Comum** (template DOCX)
- **NOVO: anexa modelos do Google Drive** — busca na pasta do condomínio → subpasta "Modelos" → lista e baixa arquivos → inclui no ZIP
- Mapeamento via `CondominioDriveMap` (condomínio → pasta Drive)

### Sidebar categorizada
- **Geral**: Dashboard, Agenda, Planilhas
- **Comunicação**: Enviar Mensagens, Templates
- **Financeiro**: Financeiro, Google Sheets, Síndicos
- **Jurídico**: Jurídico, Levantamento, Execução, Relatórios
- **Sistema**: Administração

## 9. API — mapa de endpoints

Todos os endpoints anteriores permanecem. Novos (desde último snapshot):

### Planilhas dos Funcionários (`/api/planilhas`)
`GET /configs`, `POST /configs`, `PUT /configs/{id}`, `DELETE /configs/{id}`, `GET /configs/{id}/abas`, `GET /configs/{id}/dashboard?aba=...`

### Execução (atualizado)
Endpoints de geração agora consultam `CondominioDriveMap` e incluem modelos do Drive.

## 10. Segurança / Variáveis de ambiente

Credenciais padrão: `admin@admin.com` / `admin123` (trocar em produção).

### Variáveis de ambiente atuais (LOCAL `.env`)

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
EVOLUTION_INSTANCE=Cobranca         # ⚠️ era "minha-instancia" antes — corrigido em 28/04/2026
EVOLUTION_API_KEY=m6zlm4vfowg7i8y4citjvn   # mesma do servidor de produção

# Superlógica
SUPERLOGICA_BASE_URL=https://api.superlogica.net/v2/condor
SUPERLOGICA_APP_TOKEN="d904263b-a203-42fb-b33c-c4d772ebeb02"
SUPERLOGICA_ACCESS_TOKEN="1d0acbdd-6a3d-42da-9314-ff78bde5d081"
SUPERLOGICA_MAX_ID=100

# Google Drive (NOVO)
DRIVE_EXECUCOES_FOLDER_ID=1TBlbsMlzjXcR5DAFjQqEmRJoCrrbGWF6  # "01 - EXECUÇÕES" no Meu Drive
GOOGLE_SHEETS_CREDENTIALS_FILE=/app/credentials/google-sheets.json

# E-mail (reset de senha)
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_HOST_USER=joaoricardopratika@gmail.com
EMAIL_HOST_PASSWORD=<app password>
```

### Servidor de produção (`/root/.env` em `186.202.209.150`)
- Mesmas variáveis, com `DJANGO_DEBUG=False` (ou similar)
- `EVOLUTION_API_KEY=m6zlm4vfowg7i8y4citjvn` (CONFIRMADO funcionando)
- `EVOLUTION_INSTANCE=Cobranca`
- `DRIVE_EXECUCOES_FOLDER_ID` — ⚠️ AINDA NÃO CONFIGURADO em produção (precisa ser feito)
- Outras `.env` no servidor (NÃO confundir): `/root/projeto_teste/.env`, `/root/rivieira/.env`

### Service Account Google
- **Email**: `sheets-reader@projetoteste-491111.iam.gserviceaccount.com`
- **Escopos**: `spreadsheets.readonly` + `drive.readonly`
- **Pasta-mãe Drive compartilhada**: pasta "01 - EXECUÇÕES" no Meu Drive do João Ricardo (NÃO em "Compartilhados comigo" — não funciona)
- **Pasta original (referência)**: `Compartilhados comigo > 02 - Juridico > 00 0 JURIDICO 2026 > 01 - EXECUÇÕES` (do email `Jessicabernardo@gmail.com`)
- **Por que mover**: SA não enxergava conteúdo de pastas em "Compartilhados comigo" mesmo com permissão (dono original tinha restrições). Solução: upload da pasta inteira para o Meu Drive do João Ricardo, daí compartilhar com SA.

### Evolution API (WhatsApp)
- **Manager UI produção**: `http://186.202.209.150:8080/manager`
- **Instância**: `Cobranca` (com C maiúsculo — case-sensitive)
- **Webhook**: ainda não configurado (`/webhook/find/Cobranca` retorna `null`). Endpoint `/api/webhooks/evolution` existe no backend mas está inativo no Evolution.
- **Reconectar (caso desconecte)**:
  ```bash
  # No servidor
  curl -X DELETE "http://localhost:8080/instance/delete/Cobranca" -H "apikey: m6zlm4vfowg7i8y4citjvn"
  docker restart evolution_api && sleep 15
  curl -X POST "http://localhost:8080/instance/create" \
    -H "Content-Type: application/json" -H "apikey: m6zlm4vfowg7i8y4citjvn" \
    -d '{"instanceName":"Cobranca","qrcode":true,"integration":"WHATSAPP-BAILEYS"}'
  # Pegar o QR code do retorno e escanear
  ```

### Comandos úteis

```bash
docker compose up --build -d                  # Frontend: :3000, Backend docs: :8000/api/docs
docker compose up -d --force-recreate web     # Recarrega .env (restart NÃO recarrega!)
docker logs --tail 80 pratika_cobranca-web-1  # Logs locais
docker logs --tail 80 root-web-1              # Logs produção (no servidor)
```

## 11. Variáveis de template WhatsApp (inalterado)

`{{nome}}`, `{{condominio}}`, `{{unidade}}`, `{{valor}}`, `{{vencimento}}`, `{{competencia}}`, `{{qtd}}`

## 12. Gaps / dívidas

### Documentação e processo
- `INTEGRACAO_GOOGLE_SHEETS.md` **vazio** — agora deveria cobrir Sheets E Drive
- Sem testes automatizados
- Sem CI/CD (deploy é manual: `git pull && docker compose up -d --force-recreate`)
- Credenciais padrão fracas (`admin@admin.com`/`admin123`)

### Hardcodes
- Nomes de colunas de planilha de funcionários **hardcoded** em `planilha_funcionario_api.py` (CONDOMÍNIO, PRAZO DE RECEBIMENTO DA PRESTAÇÃO, etc.)
- Nomes de subpastas Drive ("modelo"/"modelos") hardcoded em `drive_service.py` — se a estrutura do Drive mudar, quebra

### Mapeamentos de dados
- `CondominioDriveMap` precisa ser populado para condomínios cujo nome no Superlógica não bate com a pasta no Drive (auto-match falha quando o nome longo não está contido no nome curto da pasta — ex: "CONDOMINIO RESIDENCIAL JANGADAS E CARAVELAS" vs "18 - JANGADAS")
- O auto-match faz `slug(nome_condominio) in slug(nome_pasta)` — falha quando o condomínio é mais específico que a pasta

### Credenciais Google
- `google-sheets.json` serve duplo propósito (Sheets + Drive) — escopos `spreadsheets.readonly` + `drive.readonly` confirmados
- Migração para service account no projeto novo `dr-nuvio` **bloqueada** pela política `iam.disableServiceAccountKeyCreation` do Workspace
- Service account atual está em projeto antigo (`projetoteste-491111`) sem organização — funciona mas não é o ideal a longo prazo

### Gotchas operacionais (descobertos em 28/04/2026)
- **`docker compose restart` NÃO recarrega `.env`** — use `up -d --force-recreate <serviço>` ao mudar variável de ambiente
- **Service account não enxerga pastas em "Compartilhados comigo"** mesmo com permissão (problema do dono original / herança quebrada). Solução: pasta precisa estar no "Meu Drive" do dono ou em Shared Drive com SA como membro
- **Evolution API status pode mentir**: `state="open"` não garante conexão real. Se mensagens falham com "Connection Closed", precisa logout + delete instance + recreate
- **WhatsApp permite até 4 aparelhos linkados + celular**: se Evolution reconectar e o slot anterior não saiu, abre conflito — desconectar manualmente em "Aparelhos conectados" no celular
- **`pairingCode` é mais rápido que QR**: 8 caracteres digitados em "Conectar com número de telefone" no celular

### Deploy
- ⚠️ Features novas (Drive + dashboard de planilhas) ainda **não estão em produção**
- Pendente: `git pull` no servidor + atualizar `.env` com `DRIVE_EXECUCOES_FOLDER_ID` + `up -d --force-recreate`
