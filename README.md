# 📋 Sistema de Disparo para Inadimplentes — Pratika Cobranças

Sistema web full-stack para automatizar cobranças de condomínios inadimplentes via WhatsApp. Integra-se com a **API Superlógica** para buscar dados de inadimplência, gera relatórios em Excel e PDF, e dispara mensagens personalizadas via **Evolution API (WhatsApp)**, com controle de acesso e aprovação manual de usuários.

---

## 🚀 Funcionalidades

### Dashboard
- **Visão geral consolidada** — KPI cards com total de inadimplência, condomínios ativos, maior devedor e unidades sem número cadastrado
- **Ranking de condomínios** — ordenado por valor total de inadimplência com barras percentuais proporcionais
- **Filtro "Últimos 5 anos"** — exibe apenas inadimplências com vencimento nos últimos 5 anos, com cache separado por filtro
- **Cache local no frontend** — ao alternar o filtro pela segunda vez, os dados aparecem instantaneamente sem nova requisição à API
- **Pré-carregamento em background** — ao ativar o filtro, o sistema já busca silenciosamente o estado oposto para troca instantânea
- **Cache no servidor** — TTL de 30 minutos com chave separada por filtro (`_5a` / `_all`), botão "Forçar" limpa tudo
- **Animação de transição** — ao trocar o filtro, dados antigos somem e novos aparecem com fade suave
- **Campanhas** — histórico completo de disparos com status por mensagem, reenvio seletivo e filtro por status

### Relatórios
- **Exportação Excel (.xlsx)** — planilha com abas *Resumo* e *Detalhado*, processamento assíncrono em background com polling de status
- **Exportação PDF** — relatório formatado com logo, tabela por condomínio, linha de totais e total geral
- **Filtro "Últimos 5 anos"** — filtra vencimentos a partir de 5 anos atrás na data atual, tanto no Excel quanto no PDF
- **Ordenação decrescente** — botão "Maior valor primeiro" ordena unidades por Total (desc) em ambos os formatos
- **Efeito zebrado no PDF** — linhas alternadas em branco e cinza claro para melhor legibilidade
- **Unidades zeradas excluídas** — unidades cujo total ficou R$ 0,00 após filtro de período são omitidas do relatório
- **Filtro por condomínio** — exporta apenas um condomínio específico ou todos
- **Filtro por data de posição** — define a data de referência para cálculo de encargos

### Mensagens WhatsApp
- **Disparo em lote** — envia cobranças para todos os números do Excel gerado (colunas *Telefone 1* e *Telefone 2*)
- **Templates personalizados** — selecione um template com variáveis dinâmicas ou use a mensagem padrão
- **Reenvio seletivo** — reenvie apenas mensagens aguardando resposta de uma campanha
- **Histórico de campanhas** — acompanhe enviados, respondidos e erros por campanha

### Interface
- **Sidebar retrátil** — modo rail com ícones ou expandida com labels, persistência do estado
- **Tema claro/escuro** — alternância com persistência no `localStorage`
- **Login seguro** — sidebar não renderiza na tela de login, independente do estado de autenticação

---

## 🛠️ Stack Tecnológica

| Camada | Tecnologias |
|---|---|
| **Backend** | Python 3.13, Django 6.0, Django-Ninja 1.5 |
| **Autenticação** | PyJWT (JSON Web Tokens) |
| **Banco de Dados** | PostgreSQL 16 |
| **Frontend** | Vue.js 3 (Composition API), Vuetify 3, Vite |
| **Infraestrutura** | Docker, Docker Compose |
| **Integrações** | API Superlógica (inadimplência), Evolution API (WhatsApp) |
| **Relatórios** | openpyxl (Excel), ReportLab (PDF) |

---

## 📁 Estrutura do Projeto

```
.
├── projeto_disparador/        # Backend Django
│   └── core/
│       ├── models.py          # User, MessageTemplate, Campanha, MensagemEnviada
│       ├── auth.py            # Autenticação JWT
│       ├── api.py             # Rotas de autenticação
│       ├── admin_api.py       # Dashboard, relatórios, exportação, usuários
│       ├── campanha_api.py    # Campanhas e reenvio de mensagens
│       ├── message_api.py     # Disparo de mensagens via planilha
│       ├── template_api.py    # CRUD de templates
│       ├── services.py        # Processamento de planilhas
│       ├── evolution_service.py # Integração Evolution API
│       ├── superlogica.py     # Integração API Superlógica (Excel + PDF)
│       └── settings.py        # Configurações Django
├── frontend/
│   └── src/
│       ├── App.vue            # Sidebar retrátil, tema claro/escuro
│       ├── main.js            # Temas pratikaLight / pratikaDark
│       └── views/
│           ├── AuthView.vue       # Login
│           ├── DashboardView.vue  # Dashboard com filtro 5 anos e cache
│           ├── ReportsView.vue    # Relatórios Excel/PDF com filtros
│           ├── CampanhasAba.vue   # Histórico de campanhas
│           ├── TemplatesView.vue  # Gerenciar templates
│           └── AdminView.vue      # Administração de usuários
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Configuração de Ambiente

As variáveis de ambiente são injetadas via `docker-compose.yml` ou arquivo `.env`:

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
| `DB_NAME` | Nome do banco PostgreSQL |
| `DB_USER` | Usuário do banco |
| `DB_PASSWORD` | Senha do banco |

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

### Dashboard
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/admin/dashboard` | Dados do dashboard (`?ultimos_5_anos=true`) |
| `POST` | `/api/admin/dashboard/clear-cache` | Limpa o cache do servidor |
| `GET` | `/api/admin/condominios` | Lista condomínios válidos da Superlógica |

### Relatórios
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/admin/export-defaulters/start` | Inicia geração do Excel em background (`?ultimos_5_anos=true&ordenar_desc=true`) |
| `GET` | `/api/admin/export-defaulters/status/{job_id}` | Consulta status do job |
| `GET` | `/api/admin/export-defaulters/download/{job_id}` | Baixa o Excel gerado |
| `POST` | `/api/admin/export-pdf/start` | Inicia geração do PDF em background (`?ultimos_5_anos=true&ordenar_desc=true`) |
| `GET` | `/api/admin/export-pdf/status/{job_id}` | Consulta status do job PDF |
| `GET` | `/api/admin/export-pdf/download/{job_id}` | Baixa o PDF gerado |

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
| `PUT` | `/api/templates/{id}` | Atualizar template *(admin)* |
| `DELETE` | `/api/templates/{id}` | Excluir template *(admin)* |

### Administração
| Método | Rota | Descrição |
|---|---|---|
| `GET` | `/api/admin/users` | Listar usuários |
| `POST` | `/api/admin/approve-user` | Aprovar/revogar acesso |
| `POST` | `/api/admin/create-user` | Criar usuário *(admin)* |
| `POST` | `/api/admin/set-admin` | Conceder/revogar permissão admin |
| `DELETE` | `/api/admin/delete-user` | Remover usuário |

---

## 📊 Fluxo de Uso

```
1. Administrador faz login
        ↓
2. Dashboard — visualiza total de inadimplência por condomínio
   [Opcional] Ativa filtro "Últimos 5 anos" para ver inadimplência recente
        ↓
3. Em "Relatórios" → configura filtros (período, ordenação) e exporta Excel ou PDF
        ↓
4. Em "Relatórios" → faz upload do Excel gerado na seção de disparo
        ↓
5. Seleciona template (opcional) e clica em "Enviar mensagens"
        ↓
6. Sistema envia WhatsApp para cada número das colunas Telefone 1 e Telefone 2
        ↓
7. Exibe resumo: ✅ Enviados | ❌ Erros | 📵 Sem número
        ↓
8. Em "Campanhas" → acompanha respostas e reenvia para quem não respondeu
```

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
- Sidebar não renderiza na tela de login

---

## 📄 Licença

MIT © 2026 João Ricardo