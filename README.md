<div align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="landing-page/assets/img/brand/runas-white.png">
    <img src="landing-page/assets/img/brand/runas-black.png" alt="Runas ERP" width="320">
  </picture>
</div>

#  Runas ERP

> Sistema ERP completo para comércio de alimentos e bebidas com arquitetura de microsserviços

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.141-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![React](https://img.shields.io/badge/React-19-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Status](https://img.shields.io/badge/Status-Operacional-success)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-Propriet%C3%A1ria-red)

---

> ### ⚖️ Software proprietário — não é open source
>
> Copyright © 2026 **DenebCorp**. Todos os direitos reservados.
>
> Este repositório é **privado**. Quando o acesso de leitura é concedido — avaliação
> técnica, processo seletivo, due diligence — ele autoriza **apenas ler o código**.
> Nenhum direito de usar, executar, copiar, modificar ou distribuir é concedido.
>
> Detalhes em [LICENSE](./LICENSE). Vitrine pública do produto:
> [landing-page/](./landing-page/) · [runaserp.com.br](https://www.runaserp.com.br)

---

## 🚀 Quick Start

```bash
# 1. Clone e entre no diretório
git clone <repo-url>
cd RunasERP

# 2. Suba todos os serviços (não existe docker-compose.yml simples — sempre use -f)
docker-compose -f docker-compose.dev.yml up -d

# 3. Acesse
# - Frontend: http://localhost:3000
# - API Gateway: http://localhost:8000
# - Swagger: http://localhost:8000/docs
```

**Login padrão**: `admin@runas.com` / `Admin@123`

📖 **Guia completo**: [QUICK-START.md](./QUICK-START.md)

---

## 📊 Status Atual (Agosto 2026)

### ✅ Módulos Completos

Endpoints contados por serviço (decorators de rota em `api-gateway/` e `services/<serviço>/`):

| Módulo | Serviço | Backend | Frontend | Endpoints |
|--------|---------|---------|----------|-----------|
| **API Gateway** (auth, RBAC, proxy) | `api-gateway` | 🟢 100% | - | 27 |
| **Empresas** (multi-tenancy) | `empresas` | 🟢 100% | 🟢 100% | 8 |
| **Clientes** | `clientes` | 🟢 100% | 🟢 100% | 17 |
| **Produtos** (categorias, variantes, fornecedores, catálogo público) | `produtos` | 🟢 100% | 🟢 100% | 42 |
| **Estoque** | `estoque` | 🟢 100% | 🟢 100% | 19 |
| **Loja Online** (vitrine, carrinho, checkout, rastreio, pagamento) | `vendas` | 🟢 100% | 🟢 100% | 40 |

**Total operacional**: 153 endpoints | ~27.000 linhas Python + ~14.000 linhas TypeScript

### 🟡 Backend Pronto (Frontend Pendente)

| Módulo | Backend | Frontend | Prioridade |
|--------|---------|----------|------------|
| **Vendas/PDV** (interno) | 🟢 100% (serviço `vendas`) | 🔴 placeholder | 🔥 Alta |
| **Pedidos Online** (painel admin) | 🟢 100% (serviço `vendas`) | 🔴 placeholder | 🔥 Alta |

### 🔴 Planejado

- **Financeiro** - serviço criado, sem models/routers ainda (frontend é placeholder)
- **Notificações** - serviço criado, sem models/routers ainda
- Relatórios Avançados

---

## 🏗️ Arquitetura

```
┌─────────────────┐
│   API Gateway   │  ← JWT Auth + RBAC + Rate Limiting + multi-tenancy
│   (porta 8000)  │     injeta X-Empresa-Id em todo request proxiado
└────────┬────────┘
         │
    ┌────┴─────┬─────────┬────────┬────────────┬────────────┐
    │          │         │        │            │            │
┌───▼────┐ ┌──▼────┐ ┌──▼────┐ ┌─▼────┐ ┌─────▼─────┐ ┌────▼──────┐
│Clientes│ │Produtos│ │Estoque│ │Vendas│ │Financeiro │ │Notificações│
│  8001  │ │  8002  │ │ 8003  │ │ 8004 │ │   8005 🚧 │ │     🚧     │
└────────┘ └────────┘ └───────┘ └──────┘ └───────────┘ └───────────┘
                    + Empresas (tenancy, sem porta própria)
```

**7 serviços + gateway** | **Schema per Service** (um Postgres, um schema por serviço)
| **Event-Driven** (RabbitMQ) | **Redis Cache** | Frontend React na 3000

> 🚧 = serviço criado, implementação pendente. Um serviço nunca consulta o schema
> de outro, e nenhum aceita request direto na própria porta — só via gateway.

---

## 📚 Documentação Essencial

### 🎯 Para Começar
- 📖 [O SISTEMA.md](./O%20SISTEMA.md) - Visão geral completa
- ⚡ [QUICK-START.md](./QUICK-START.md) - Setup em 5 minutos

### 💻 Para Desenvolver
- ✅ [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md) - Checklist completo
- 🎨 [FRONTEND_IMPLEMENTACAO.md](./FRONTEND_IMPLEMENTACAO.md) - Guia de implementação frontend
- ⚡ [GUIA_PERFORMANCE.md](./GUIA_PERFORMANCE.md) - Otimização e performance
- 📋 [docs/02-desenvolvimento/](./docs/02-desenvolvimento/) - Guias técnicos
- 🔧 [CLAUDE.md](./CLAUDE.md) - Convenções

### 📁 Documentação Completa
- 📂 [docs/01-principal/](./docs/01-principal/) - Documentação principal
- 📂 [docs/03-arquitetura/](./docs/03-arquitetura/) - Arquitetura do sistema
- 📂 [docs/04-backend/](./docs/04-backend/) - Backend e APIs
- 📂 [docs/05-frontend/](./docs/05-frontend/) - Frontend React
- 📂 [docs/10-api-reference/](./docs/10-api-reference/) - Referência completa de APIs
- 📂 [docs/11-regras-negocio/](./docs/11-regras-negocio/) - Regras de negócio
- 🌐 [landing-page/](./landing-page/) - Site institucional do produto (HTML/CSS/JS estático)

---

## 🛠️ Tecnologias

### Backend
- **FastAPI** 0.141 - Framework web moderno
- **SQLAlchemy** 2.0 - ORM assíncrono
- **PostgreSQL** 15 - Banco de dados
- **Redis** 7 - Cache e sessões
- **RabbitMQ** 3.12 - Mensageria

### Frontend
- **React** 19 - UI library
- **TypeScript** 5 - Type safety
- **Vite** 8 - Build e dev server
- **React Bootstrap** 2 + **Bootstrap** 5 - Componentes UI
- **TanStack Query** 5 - Data fetching e cache
- **Axios** - Cliente HTTP
- **React Hook Form** + **Zod** - Formulários e validação
- **React Router** 7 - Navegação

### DevOps
- **Docker** + **Docker Compose** - Containerização
- **Alembic** - Migrations
- **Vitest** - Testes de frontend
- **Git** - Versionamento

---

## 🎯 Próximas Implementações

Para um roadmap detalhado, consulte: [docs/01-visao-geral/roadmap.md](./docs/01-visao-geral/roadmap.md)

### Alta Prioridade
- **PDV (Vendas)** - Frontend para ponto de venda
- **Pedidos Online** - Painel admin para pedidos da loja online
- **Relatórios** - Dashboards e relatórios

### Médio Prazo
- **Financeiro** - Gestão financeira completa
- **Notificações** - Sistema de notificações WhatsApp
- **Analytics** - Métricas e análises avançadas

📋 **Guia de desenvolvimento**: [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md)

---

## 📝 Comandos Úteis

```bash
# Desenvolvimento
docker-compose -f docker-compose.dev.yml up -d                # Subir todos os serviços
docker-compose -f docker-compose.dev.yml logs -f [serviço]    # Ver logs
docker-compose -f docker-compose.dev.yml restart [serviço]    # Reiniciar serviço
docker-compose -f docker-compose.dev.yml down                 # Parar tudo

# Cloudflare Tunnel (acesso externo)
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d

# Frontend
cd frontend
npm run dev                       # Rodar em desenvolvimento
npm run build                     # Build de produção

# Backend (rodam dentro do container — cada serviço tem seu próprio Alembic)
docker exec -it erp-[serviço]-dev alembic upgrade head    # Rodar migrations
docker-compose -f docker-compose.dev.yml exec [serviço] python seed.py   # Popular dados
pytest                            # Testes de integração (da raiz do repo, serviços no ar)
```

---

## 🔐 Autenticação

O sistema utiliza **OAuth2 com JWT** e **RBAC**:

| Role | Permissões |
|------|-----------|
| **ADMIN** | Acesso total |
| **GERENTE** | Gestão de produtos, clientes, vendas |
| **VENDEDOR** | Criar vendas, consultar dados |
| **OPERADOR** | Apenas leitura |

---

## 🤝 Contribuindo

```bash
# 1. Crie uma branch
git checkout -b feat/nova-feature

# 2. Desenvolva e commit (seguindo Conventional Commits)
git commit -m "feat(modulo): adiciona nova funcionalidade"

# 3. Push e PR
git push origin feat/nova-feature
```

**Convenções**: Veja [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md) e [CLAUDE.md](./CLAUDE.md)

---

## 📄 Licença

**Copyright © 2026 DenebCorp — todos os direitos reservados.** Software proprietário.

| Documento | Aplica-se a | O que concede |
|-----------|-------------|---------------|
| [LICENSE](./LICENSE) | quem tem acesso de leitura ao repositório | leitura e avaliação técnica apenas — **nenhum direito de uso** |
| [EULA comercial](./docs/01-principal/EULA-comercial.md) | clientes sob contrato | uso do sistema nos termos do contrato |

Para licenciar ou pedir permissão: **legal@runas.com**

Dependências de terceiros permanecem sob suas licenças originais.

---

## 📞 Contato

- **Email**: dev@runas.com.br
- **Documentação**: [docs/](./docs/)

---

<div align="center">

**Versão 1.0.0** | Agosto 2026

Desenvolvido por **Equipe DenebCorp**

[⬆ Voltar ao topo](#-runas-erp)

</div>
