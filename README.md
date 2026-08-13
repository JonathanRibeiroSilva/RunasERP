# 🏪 Runas ERP

> Sistema ERP completo para comércio de alimentos e bebidas com arquitetura de microsserviços

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![React](https://img.shields.io/badge/React-18-blue)
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

# 2. Suba todos os serviços
docker-compose up -d

# 3. Acesse
# - Frontend: http://localhost:3000
# - API Gateway: http://localhost:8000
# - Swagger: http://localhost:8000/docs
```

**Login padrão**: `admin@runas.com` / `Admin@123`

📖 **Guia completo**: [QUICK-START.md](./QUICK-START.md)

---

## 📊 Status Atual (Junho 2026)

### ✅ Módulos Completos

| Módulo | Backend | Frontend | Endpoints |
|--------|---------|----------|-----------|
| **API Gateway** | 🟢 100% | - | 15 |
| **Clientes** | 🟢 100% | 🟢 100% | 12 |
| **Produtos** | 🟢 100% | 🟢 100% | 25 |
| **Loja Online** | 🟢 100% | 🟢 100% | 26 |

**Total operacional**: 78 endpoints | ~15.000 linhas de código

### 🟡 Backend Pronto (Frontend Pendente)

| Módulo | Backend | Frontend | Prioridade |
|--------|---------|----------|------------|
| **Vendas/PDV** | 🟢 100% | 🔴 0% | 🔥 Alta |
| **Estoque** | 🟢 100% | 🔴 0% | 🔥 Alta |

### 🔴 Planejado

- Financeiro
- Notificações
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
- **FastAPI** 0.109 - Framework web moderno
- **SQLAlchemy** 2.0 - ORM assíncrono
- **PostgreSQL** 15 - Banco de dados
- **Redis** 7 - Cache e sessões
- **RabbitMQ** 3.12 - Mensageria

### Frontend
- **React** 18 - UI library
- **TypeScript** 5 - Type safety
- **React Bootstrap** - Componentes UI
- **SWR** - Data fetching
- **React Router** - Navegação

### DevOps
- **Docker** + **Docker Compose** - Containerização
- **Alembic** - Migrations
- **Git** - Versionamento

---

## 🎯 Próximas Implementações

Para um roadmap detalhado, consulte: [docs/01-visao-geral/roadmap.md](./docs/01-visao-geral/roadmap.md)

### Alta Prioridade
- **PDV (Vendas)** - Frontend para ponto de venda
- **Estoque** - Frontend para gestão de estoque
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

# Backend
cd services/[serviço]
alembic upgrade head              # Rodar migrations
python seed.py                    # Popular dados de teste
pytest                            # Rodar testes
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

**Versão 2.0.0** | Junho 2026

Desenvolvido por **Equipe DenebCorp**

[⬆ Voltar ao topo](#-runas-erp)

</div>
