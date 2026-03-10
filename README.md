# Sistema de Disparo para Inadimplentes

Sistema web full-stack desenvolvido para automatizar o envio de mensagens de cobrança para condomínios inadimplentes. A aplicação processa planilhas CSV e integra-se com uma API de mensageria externa, garantindo controle de acesso rigoroso e aprovação manual de novos usuários.

## Stack Tecnológica

- Backend: Python 3.13.11, Django 6.0.1, Django-Ninja 1.5.3
- Autenticação: PyJWT (JSON Web Tokens)
- Banco de Dados: PostgreSQL 16
- Frontend: Vue.js 3 (Composition API), Vuetify 3, Vite
- Infraestrutura: Docker, Docker Compose

## Pré-requisitos

- Docker v2+
- Docker Compose

## Configuração de Ambiente

O sistema utiliza variáveis de ambiente injetadas via Docker Compose. Certifique-se de configurar as chaves da API externa no arquivo `docker-compose.yml` antes da execução em produção:

- EXTERNAL_MESSAGING_API_URL
- EXTERNAL_MESSAGING_API_KEY
- DJANGO_SECRET_KEY

## Execução do Projeto

Para iniciar toda a infraestrutura (Banco de Dados, Backend e Frontend), execute o comando na raiz do projeto:

docker compose up --build -d

O script de inicialização do backend aplicará as migrações automaticamente e criará o usuário administrador padrão.

## Acesso ao Sistema

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/api/docs

## Credenciais Padrão (Administrador)

- E-mail: admin@admin.com
- Senha: admin123

## Fluxo de Utilização

1. Acesse o sistema e realize o login com a conta de administrador.
2. Novos usuários podem se cadastrar na tela inicial, mas o acesso será bloqueado até a aprovação.
3. O administrador deve acessar a aba "Administração" para aprovar os cadastros pendentes.
4. Usuários aprovados terão acesso ao Dashboard para realizar o upload da planilha CSV.
5. O sistema processará o arquivo e exibirá o balanço de mensagens enviadas com sucesso e falhas.