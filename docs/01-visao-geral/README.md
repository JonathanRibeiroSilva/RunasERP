# 🎯 Visão Geral - Runas

Bem-vindo à documentação do **Runas**, um ERP SaaS multi-tenant para pequenos
comércios brasileiros.

> Toda afirmação técnica abaixo foi conferida contra o código em **2026-09-25** e
> traz a evidência (`arquivo:linha`) quando não é óbvia. O que não pôde ser
> confirmado está marcado como **A CONFIRMAR** em vez de afirmado.

---

## 📖 Sobre o Projeto

O Runas é um ERP (Enterprise Resource Planning) multi-tenant: uma instalação
atende vários lojistas, e há um plano de controle separado para o dono da
plataforma administrar esses lojistas (ver
[Plataforma](../03-arquitetura/plataforma.md)).

Domínios cobertos pelos serviços do repositório (`services/`):

- 🏢 **Empresas** - Tenants, usuários e assinaturas
- 👥 **Clientes** - Cadastro, crédito e histórico
- 📦 **Produtos** - Catálogo, variantes e fornecedores
- 📊 **Estoque** - Controle, movimentações e lotes
- 🛒 **Vendas** - Carrinho, pedidos e pagamentos
- 💰 **Financeiro** - Contas a receber e vendas fiadas
- 📱 **Notificações** - Mensageria para o cliente final

> ⚠️ Domínio implementado ≠ serviço pronto. **Financeiro** e **Notificações**
> hoje são cascas: `services/financeiro/routers/__init__.py` e
> `services/notificacoes/routers/__init__.py` têm 22 bytes (vazios) e nenhum
> `include_router` é chamado — os dois expõem só `/health`. O estado real de
> cada peça está no [Roadmap](./roadmap.md).

---

## 🎯 Objetivos

### Simplicidade
- Interface intuitiva e fácil de usar
- Processos diretos sem complexidade desnecessária
- Onboarding rápido para novos usuários

### Acessibilidade
- Solução de baixo custo
- Hospedagem em VPS única (Coolify + Cloudflare)

### Controle
- Rastreabilidade das operações: o gateway grava auditoria de requisição
  (`api-gateway/middleware/auditoria_middleware.py`)
- Isolamento por tenant no gateway, antes de chegar ao serviço

### Flexibilidade
- Adaptável a diferentes tipos de negócio
- Integrações com serviços externos (Mercado Pago, ViaCEP)

---

## 🏗️ Arquitetura

```
Frontend (React) → API Gateway (FastAPI) → 7 microsserviços (FastAPI)
                                          ↓
                                  PostgreSQL + Redis + RabbitMQ
```

### Componentes Principais

- **Frontend**: React 19 + TypeScript + Vite, servido por nginx dentro da própria
  imagem (`docker-compose.prod.yml:506`)
- **API Gateway**: FastAPI com autenticação JWT (`api-gateway/auth/jwt.py`) e
  rate limiting (`api-gateway/main.py`)
- **Microsserviços**: **7** serviços independentes em Python — `clientes`,
  `empresas`, `estoque`, `financeiro`, `notificacoes`, `produtos`, `vendas`
  (`ls services/`) — mais o `api-gateway`, totalizando 8 aplicações FastAPI
- **Banco de Dados**: **um** PostgreSQL com **um schema por serviço**, não um
  banco por serviço. O container `db-init` cria os schemas `gateway`, `empresas`,
  `clientes`, `produtos`, `estoque`, `vendas`, `financeiro`, `notificacoes` e
  `evolution` (`docker-compose.prod.yml`), e cada serviço fixa o seu via
  `search_path` (`services/clientes/database.py:19`)
- **Cache**: Redis, usado pelo gateway (`api-gateway/main.py`) e pelo middleware
  de inadimplência
- **Mensageria**: RabbitMQ sobe no compose e os 7 serviços têm
  `events/publisher.py` com a classe `EventPublisher`, mas **nenhum arquivo
  importa o publisher** — zero chamadas a `publish()` no repositório. A
  comunicação entre serviços hoje é 100% HTTP síncrono via `httpx`. Escrito e
  desligado, não em uso.

---

## 🚀 Tecnologias

### Backend
- **Python 3.12** - `services/clientes/Dockerfile:2`, `api-gateway/Dockerfile:2`
- **FastAPI** - Framework web
- **SQLAlchemy** - ORM (async)
- **Alembic** - Migrações de banco
- **Pydantic** - Validação de dados
- **Pytest** - 62 arquivos `test_*.py` no repositório

> `celery==5.6.3` aparece nos `requirements.txt` dos 7 serviços, mas **nenhum
> código Python instancia um app Celery**. Não há worker Celery rodando; as
> rotinas em `services/vendas/jobs/` são scripts. **A CONFIRMAR**: como esses
> jobs são agendados em produção.

### Frontend
- **React 19** (`frontend/package.json`)
- **TypeScript** + **Vite**
- **Bootstrap 5** + **react-bootstrap** + **Sass** — o projeto **não** usa
  Tailwind CSS
- **React Router 7** - Roteamento
- **TanStack React Query 5** - Estado de servidor
- **React Hook Form** + **Zod** - Formulários e validação
- **Axios** - Cliente HTTP
- **Chart.js** / **react-chartjs-2** - Gráficos
- **Vitest** + **Testing Library** - Testes

### Infraestrutura
- **Docker** / **Docker Compose** - Containerização e orquestração
- **PostgreSQL 15** (`postgres:15-alpine`)
- **Redis 7** (`redis:7-alpine`)
- **RabbitMQ 3.12** (`rabbitmq:3.12-management-alpine`)
- **Coolify** - Deploy na VPS
- **Cloudflare** - TLS e borda; não há nginx-proxy nem Let's Encrypt em produção
  (`docker-compose.prod.yml:9`)

### Integrações
- **Mercado Pago** - Pagamentos PIX, no serviço `vendas`
  (`services/vendas/config.py`, `services/vendas/routers/webhook.py`)
- **OAuth2 Google e Microsoft** - Credenciais previstas em
  `api-gateway/config.py:36-43`, fluxo em `api-gateway/routers/auth_cliente.py`
- **Evolution API (WhatsApp)** - Há um schema `evolution` no banco e menção em
  `services/notificacoes/interno.py:39`, mas o serviço de notificações é casca.
  **A CONFIRMAR**: se existe envio de WhatsApp funcionando hoje.

---

## 📊 Status do Projeto

O estado real de cada peça vive em um lugar só, com evidência por item:
**[Roadmap](./roadmap.md)**. Não há tabela de percentuais aqui — a anterior
dizia "Clientes 5% planejado" enquanto o serviço já existia e rodava no CI.

---

## 👥 Equipe

**Desenvolvido por**: Equipe DenebCorp
**Contato**: [contato@denebcorp.com](mailto:contato@denebcorp.com)

---

## 📚 Documentos Relacionados

- **[Arquitetura Completa](../03-arquitetura/)** - Especificação técnica detalhada
  - [Visão Geral](../03-arquitetura/visao-geral.md)
  - [Microsserviços](../03-arquitetura/microsservicos.md)
  - [Plataforma / SaaS](../03-arquitetura/plataforma.md)
- [Glossário](./glossario.md) - Termos técnicos e conceitos
- [FAQ](./faq.md) - Perguntas frequentes
- [Roadmap](./roadmap.md) - O que falta, com evidência
- [Referência de API](../10-api-reference/) - Rotas e contratos
- [Regras de Negócio](../11-regras-negocio/README.md)
- [Operação](../06-operacao/runbook-producao.md) - Runbook de produção
- [Deploy](../06-operacao/deploy.md)
- [Workflow do Graphify](../02-desenvolvimento/GRAPHIFY_WORKFLOW.md)
- [Hooks de Segurança](../02-desenvolvimento/SECURITY_HOOKS.md)

---

## 📄 Licença

Este projeto está sob licença proprietária da DenebCorp.
Todos os direitos reservados © 2026 DenebCorp.

---

**Última verificação contra o código**: 2026-09-25
