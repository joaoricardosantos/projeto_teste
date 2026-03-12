# 📋 Sistema de Disparo para Inadimplentes

Sistema web full-stack para automatizar cobranças de condomínios inadimplentes via WhatsApp. Integra-se com a **API Superlógica** para buscar dados de inadimplência, gera relatórios em Excel e dispara mensagens personalizadas via **Evolution API (WhatsApp)**, com controle de acesso e aprovação manual de usuários.

---

## 🚀 Funcionalidades

- **Relatórios de Inadimplência** — Gera planilhas Excel (`.xlsx`) com abas *Resumo* e *Detalhado*, consultando diretamente a API Superlógica por condomínio e data de posição
- **Disparo de Mensagens WhatsApp** — Envia cobranças personalizadas para todos os números da planilha via Evolution API, com delay configurável entre envios
- **Templates de Mensagem** — Crie, edite e reutilize templates com variáveis dinâmicas (`{{nome}}`, `{{condominio}}`, `{{valor}}`, `{{vencimento}}`, `{{competencia}}`)
- **Upload de Planilha** — Aceita arquivos `.csv` e `.xlsx` para disparo em lote
- **Controle de Acesso** — Cadastro de usuários com aprovação manual pelo administrador
- **Autenticação JWT** — Sessões seguras com tokens de acesso
- **Painel Administrativo** — Gerencie usuários, permissões e aprovações pela interface web

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

---

## 📁 Estrutura do Projeto

```
.
├── projeto_disparador/        # Backend Django
│   └── core/
│       ├── models.py          # User, MessageTemplate
│       ├── auth.py            # Autenticação JWT
│       ├── api.py             # Rotas de autenticação
│       ├── admin_api.py       # Rotas administrativas
│       ├── message_api.py     # Rotas de disparo de mensagens
│       ├── template_api.py    # CRUD de templates
│       ├── services.py        # Processamento de planilhas
│       ├── evolution_service.py # Integração Evolution API
│       ├── superlogica.py     # Integração API Superlógica
│       └── settings.py        # Configurações Django
├── frontend/                  # Frontend Vue.js
│   └── src/views/
│       ├── DashboardView.vue  # Enviar mensagens
│       ├── ReportsView.vue    # Gerar relatórios
│       ├── TemplatesView.vue  # Gerenciar templates
│       ├── AdminView.vue      # Administração de usuários
│       └── AuthView.vue       # Login / Cadastro
├── docker-compose.yml
└── README.md
```

---

## ⚙️ Configuração de Ambiente

As variáveis de ambiente são injetadas via `docker-compose.yml`. Configure as seguintes antes de subir em produção:

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
| `POST` | `/api/auth/register` | Cadastrar novo usuário |
| `POST` | `/api/auth/login` | Login e obtenção do token JWT |

### Mensagens
| Método | Rota | Descrição |
|---|---|---|
| `POST` | `/api/messages/dispatch-excel` | Disparo via planilha `.xlsx` ou `.csv` do relatório |
| `POST` | `/api/messages/upload-defaulters` | Disparo via CSV legado (colunas: `condominio`, `contato`, `valor_debito`) |
| `POST` | `/api/messages/upload-defaulters-template` | Idem com template selecionado |

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
| `PATCH` | `/api/admin/users/{id}/approve` | Aprovar/revogar acesso |
| `GET` | `/api/admin/export-defaulters` | Gerar e baixar relatório Excel |

---

## 📊 Fluxo de Uso

```
1. Administrador faz login
        ↓
2. [Opcional] Cria templates de mensagem com variáveis dinâmicas
        ↓
3. Em "Relatórios" → Exporta planilha Excel da Superlógica
        ↓
4. Em "Enviar Mensagens" → Faz upload do Excel gerado
        ↓
5. Seleciona template (opcional) e clica em "Processar e Enviar"
        ↓
6. Sistema envia WhatsApp para cada número da coluna "Telefones"
        ↓
7. Exibe resumo: ✅ Enviados | ❌ Erros | 📋 Falhas detalhadas
```

---

## 💬 Variáveis de Template

Use as variáveis abaixo no corpo dos templates para personalizar as mensagens:

| Variável | Substituído por |
|---|---|
| `{{nome}}` | Nome/Unidade do condômino |
| `{{condominio}}` | Nome do condomínio |
| `{{valor}}` | Valor total com encargos (ex: `R$ 1.234,56`) |
| `{{vencimento}}` | Data de vencimento |
| `{{competencia}}` | Competência da cobrança |

**Exemplo de template:**
```
Olá, *{{nome}}*!

Identificamos um débito em aberto no *{{condominio}}*.
Competência: {{competencia}} | Vencimento: {{vencimento}}
Valor atualizado: *{{valor}}*

Regularize para evitar novos encargos.
Caso já tenha pago, desconsidere esta mensagem.
```

---

## 🔒 Segurança

- Todos os endpoints (exceto login e cadastro) exigem autenticação via JWT
- Operações administrativas (criar/editar templates, gerenciar usuários) são restritas a `is_staff` ou `is_superuser`
- Novos usuários ficam bloqueados até aprovação manual pelo administrador
- Senhas armazenadas com hash via Django Auth

---

## 📄 Licença

MIT © 2026 João Ricardo
