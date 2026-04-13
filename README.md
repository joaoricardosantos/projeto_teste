# 📋 Sistema de Gestão de Cobranças — Pratika

Plataforma web full-stack para gestão completa de cobranças de condomínios: inadimplência, jurídico, financeiro, recebimentos, agenda e disparo automatizado via WhatsApp. Integra **API Superlógica**, **Evolution API (WhatsApp)** e **Google Sheets**, com controle de acesso e aprovação manual de usuários.

---

## 🚀 Funcionalidades

### Dashboard (Inadimplência)
- **Visão geral consolidada** — KPI cards com total de inadimplentes, condomínios ativos, maior devedor e unidades sem número cadastrado
- **Ranking de condomínios** — ordenado por valor total de inadimplência com barras percentuais proporcionais
- **Filtro "Últimos 5 anos"** — exibe apenas inadimplências com vencimento nos últimos 5 anos, com cache separado por filtro
- **Cache local + servidor** — TTL de 30 minutos, chave separada por filtro (`_5a` / `_all`), pré-carregamento em background e botão "Forçar" para limpar

### Jurídico
- **Dashboard consolidado** — KPIs de total em dívida, total de processos, unidades com/sem processo, movimentações na semana, condomínios e advogados
- **CRUD de advogados** — cada advogado tem uma planilha Google Sheets associada (`spreadsheet_id` + aba)
- **Top 20 devedores** — ranking consolidado a partir das planilhas dos advogados
- **Análise por situação judicial** — agrupamentos por advogado e condomínio

### Financeiro
- **Despesas via Superlógica** — resumo por categoria, fornecedor e mês
- **Liquidação de despesas** — baixa direto pelo Superlógica
- **Despesas locais** — CRUD próprio para despesas fora do Superlógica
- **Fila de pagamento** — controle da ordem e status dos pagamentos

### Recebimentos (Google Sheets)
- **Dashboard com 4 blocos** — Geral, COSERN Loja 71, COSERN Loja 114 e Diversos
- **Previsto vs Recebido vs Pendente** — KPI de % de recebimento
- **Fluxo de caixa** — série temporal por data
- **Setores configuráveis** — permite mapear setores financeiros personalizados

### Agenda / Horário
- **Calendário de tarefas** — CRUD com checklist por tarefa
- **Insights mensais** — despesas (pendentes, pagas no mês, vencendo em 7 dias, vencidas)
- **Inadimplência consolidada** — variação mensal/anual, projeção e top condomínios

### Execução de Cobrança
- **Geração em lote** — DOCX e PDF de documentos de execução por unidade, entregues em ZIP

### Síndicos
- **Planilha de clientes** — consulta à base "CLIENTES PRATIKA 2026"

### Relatórios
- **Exportação Excel (.xlsx)** — abas *Resumo* e *Detalhado*, processamento assíncrono com polling de status
- **Exportação PDF** — relatório formatado com logo, tabela por condomínio, linha de totais, efeito zebrado
- **Filtro "Últimos 5 anos"** — aplicável a Excel e PDF
- **Ordenação decrescente** — botão "Maior valor primeiro"
- **Filtros por condomínio e por data de posição**

### Mensagens WhatsApp
- **Disparo em lote** — envia para todos os números do Excel (colunas *Telefone 1* e *Telefone 2*)
- **Templates personalizados** — variáveis dinâmicas ou mensagem padrão
- **Reenvio seletivo** — reenvie apenas mensagens aguardando resposta
- **Histórico de campanhas** — enviados, respondidos e erros por campanha

### Interface
- **Sidebar retrátil** — modo rail com ícones ou expandida com labels, estado persistente
- **Tema claro/escuro** — persistência no `localStorage`
- **Login seguro** — sidebar não renderiza na tela de login

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologias |
|---|---|
| **Backend** | Python 3.13, Django 6.0, Django-Ninja 1.5 |
| **Autenticação** | PyJWT (JSON Web Tokens) |
| **Banco de Dados** | PostgreSQL 16 |
| **Frontend** | Vue.js 3 (Composition API), Vuetify 3, Vite |
| **Infraestrutura** | Docker, Docker Compose |
| **Integrações** | API Superlógica, Evolution API (WhatsApp), Google Sheets API |
| **Relatórios** | openpyxl (Excel), ReportLab (PDF), python-docx (DOCX) |

---

## 📁 Estrutura do Projeto

```
.
├── projeto_disparador/              # Backend Django
│   └── core/
│       ├── models.py                # User, MessageTemplate, Campanha, MensagemEnviada, AdvogadoPlanilha
│       ├── auth.py                  # Autenticação JWT
│       ├── api.py                   # Rotas de autenticação
│       ├── admin_api.py             # Dashboard, relatórios, exportação, usuários
│       ├── campanha_api.py          # Campanhas e reenvio de mensagens
│       ├── message_api.py           # Disparo de mensagens via planilha
│       ├── template_api.py          # CRUD de templates
│       ├── juridico_api.py          # Dashboard jurídico + CRUD advogados
│       ├── financeiro_api.py        # Despesas Superlógica, locais e fila de pagamento
│       ├── sheets_api.py            # Integração Google Sheets (recebimentos, fluxo)
│       ├── agenda_api.py            # Tarefas e insights combinados
│       ├── execucao_api.py          # Geração de DOCX/PDF de execuções
│       ├── sindico_api.py           # Planilha de clientes/síndicos
│       ├── webhook_api.py           # Webhooks
│       ├── services.py              # Processamento de planilhas
│       ├── evolution_service.py     # Integração Evolution API
│       ├── superlogica.py           # Integração API Superlógica
│       ├── sheets_service.py        # Cliente Google Sheets API
│       └── settings.py              # Configurações Django
├── frontend/
│   └── src/
│       ├── App.vue                  # Sidebar retrátil, tema claro/escuro
│       ├── main.js                  # Temas pratikaLight / pratikaDark
│       └── views/
│           ├── AuthView.vue         # Login
│           ├── DashboardView.vue    # Dashboard de inadimplência
│           ├── ReportsView.vue      # Relatórios Excel/PDF
│           ├── CampanhasAba.vue     # Histórico de campanhas
│           ├── TemplatesView.vue    # Gerenciar templates
│           ├── AdminView.vue        # Administração de usuários
│           ├── JuridicoView.vue     # Dashboard jurídico + advogados
│           ├── FinanceiroView.vue   # Despesas Superlógica
│           ├── AgendaView.vue       # Calendário + insights
│           ├── SheetsView.vue       # Recebimentos (Google Sheets)
│           ├── ExecucaoView.vue     # Geração de execuções
│           ├── SindicosView.vue     # Planilha de síndicos
│           ├── LevantamentoView.vue
│           └── PainelView.vue
├── credentials/
│   └── google-sheets.json           # Credenciais da Google Sheets API
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Configuração de Ambiente

Variáveis injetadas via `docker-compose.yml` ou `.env`:

| Variável | Descrição |
|---|---|
| `DJANGO_SECRET_KEY` | Chave secreta do Django |
| `SUPERLOGICA_BASE_URL` | URL base da API Superlógica |
| `SUPERLOGICA_APP_TOKEN` | App token da Superlógica |
| `SUPERLOGICA_ACCESS_TOKEN` | Access token da Superlógica |
| `SUPERLOGICA_MAX_ID` | ID máximo de condomínios a varrer (padrão: `100`) |
| `EVOLUTION_BASE_URL` | URL da instância Evolution API |
| `EVOLUTION_INSTANCE` | Nome da instância WhatsApp |
| `EVOLUTION_API_KEY` | Chave de API da Evolution |
| `GOOGLE_SHEETS_CREDENTIALS` | Caminho para `credentials/google-sheets.json` |
| `DB_NAME` / `DB_USER` / `DB_PASSWORD` | Conexão PostgreSQL |

---

## 🐳 Execução com Docker

### Pré-requisitos
- [Docker](https://docs.docker.com/get-docker/) v2+
- [Docker Compose](https://docs.docker.com/compose/)

### Subindo o projeto
```bash
docker compose up --build -d
```

O script de inicialização aplica as migrações automaticamente e cria o usuário administrador padrão.

### Parando o projeto
```bash
docker compose down
```

---

## 🌐 Acesso

| Serviço | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API (docs) | http://localhost:8000/api/docs |

### Credenciais padrão (Administrador)
```
E-mail: admin@admin.com
Senha:  admin123
```

> ⚠️ Troque a senha padrão antes de usar em produção.

---

## 🔌 API — Endpoints Principais

### Autenticação
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/auth/login` | Login e obtenção do token JWT |

### Dashboard (Inadimplência)
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/admin/dashboard` | Dados do dashboard (`?ultimos_5_anos=true`) |
| `POST` | `/api/admin/dashboard/clear-cache` | Limpa o cache do servidor |
| `GET` | `/api/admin/condominios` | Lista condomínios válidos da Superlógica |

### Relatórios
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/admin/export-defaulters/start` | Inicia geração do Excel (`?ultimos_5_anos=true&ordenar_desc=true`) |
| `GET` | `/api/admin/export-defaulters/status/{job_id}` | Consulta status |
| `GET` | `/api/admin/export-defaulters/download/{job_id}` | Baixa o Excel |
| `POST` | `/api/admin/export-pdf/start` | Inicia geração do PDF |
| `GET` | `/api/admin/export-pdf/status/{job_id}` | Consulta status |
| `GET` | `/api/admin/export-pdf/download/{job_id}` | Baixa o PDF |

### Jurídico
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/juridico/dashboard` | KPIs consolidados e rankings |
| `GET` | `/api/juridico/advogados` | Listar advogados |
| `POST` | `/api/juridico/advogados` | Criar advogado |
| `PUT` | `/api/juridico/advogados/{id}` | Atualizar |
| `DELETE` | `/api/juridico/advogados/{id}` | Remover |
| `GET` | `/api/juridico/advogados/{id}/dados` | Dados da planilha do advogado |

### Financeiro
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/financeiro/despesas/{id_condominio}` | Resumo + detalhes |
| `POST` | `/api/financeiro/liquidar` | Liquida despesa no Superlógica |
| `GET`/`POST`/`PUT`/`DELETE` | `/api/financeiro/locais` | CRUD de despesas locais |
| `GET`/`POST`/`PUT`/`DELETE` | `/api/financeiro/fila-pagamento` | CRUD da fila de pagamento |

### Google Sheets (Recebimentos)
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/sheets/dashboard/recebimentos/{spreadsheet_id}` | 4 blocos (Geral, COSERN 71/114, Diversos) |
| `GET` | `/api/sheets/dashboard/fluxo-caixa` | Série temporal de fluxo |
| `POST` | `/api/sheets/setores` | Gerenciar setores |

### Agenda
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/agenda/insights` | Despesas + inadimplência consolidadas |
| `GET`/`POST`/`PUT`/`DELETE` | `/api/agenda/tarefas` | CRUD de tarefas com checklist |

### Execução
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/execucao/gerar-docx` | Gera ZIP com DOCX por unidade |
| `POST` | `/api/execucao/gerar-pdf` | Gera ZIP com PDF por unidade |

### Mensagens
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/messages/dispatch-excel` | Disparo via planilha `.xlsx` ou `.csv` |
| `POST` | `/api/messages/upload-defaulters` | Disparo via CSV legado |

### Campanhas
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/campanhas/` | Listar campanhas |
| `GET` | `/api/campanhas/{id}/mensagens` | Mensagens de uma campanha |
| `POST` | `/api/campanhas/{id}/reenviar` | Reenviar mensagens selecionadas |
| `DELETE` | `/api/campanhas/{id}` | Remover campanha |
| `PATCH` | `/api/campanhas/{id}/renomear` | Renomear campanha |

### Templates
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/templates` | Listar templates |
| `POST` | `/api/templates` | Criar template *(admin)* |
| `PUT` | `/api/templates/{id}` | Atualizar *(admin)* |
| `DELETE` | `/api/templates/{id}` | Excluir *(admin)* |

### Administração
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/admin/users` | Listar usuários |
| `POST` | `/api/admin/approve-user` | Aprovar/revogar acesso |
| `POST` | `/api/admin/create-user` | Criar usuário *(admin)* |
| `POST` | `/api/admin/set-admin` | Conceder/revogar admin |
| `DELETE` | `/api/admin/delete-user` | Remover usuário |

---

## 📊 Fluxo de Uso

```
1. Administrador faz login
        ↓
2. Dashboard — visualiza inadimplência por condomínio
   [Opcional] Ativa filtro "Últimos 5 anos"
        ↓
3. Relatórios → configura filtros e exporta Excel ou PDF
        ↓
4. Faz upload do Excel gerado na seção de disparo
        ↓
5. Seleciona template (opcional) e envia mensagens
        ↓
6. Sistema envia WhatsApp para Telefone 1 e Telefone 2
        ↓
7. Resumo: ✅ Enviados | ❌ Erros | 📵 Sem número
        ↓
8. Campanhas → acompanha respostas e reenvia
```

Em paralelo:
- **Jurídico** centraliza processos por advogado (planilhas Google Sheets)
- **Financeiro** consolida despesas do Superlógica + despesas locais + fila de pagamento
- **Recebimentos** acompanha previsto vs recebido em tempo real via Google Sheets
- **Agenda** combina tarefas do dia com insights mensais de despesas e inadimplência

---

## 💬 Variáveis de Template

| Variável | Substituído por |
|---|---|
| `{{nome}}` | Nome do proprietário/sacado |
| `{{condominio}}` | Nome do condomínio |
| `{{unidade}}` | Código da unidade (ex: `315 SALA`) |
| `{{valor}}` | Valor total com encargos (ex: `R$ 1.234,56`) |
| `{{vencimento}}` | Data de vencimento |
| `{{competencia}}` | Competência da cobrança |
| `{{qtd}}` | Quantidade de inadimplências em aberto |

---

## 🔒 Segurança

- Todos os endpoints (exceto login) exigem autenticação via JWT
- Operações administrativas restritas a `is_staff` ou `is_superuser`
- Novos usuários ficam bloqueados até aprovação manual pelo administrador
- Senhas armazenadas com hash via Django Auth
- Credenciais do Google Sheets isoladas em `credentials/` (fora do versionamento)

---

## 📄 Licença

MIT © 2026 João Ricardo
