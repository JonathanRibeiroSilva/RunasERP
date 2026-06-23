# 🏪 Runas ERP

> Sistema ERP completo para comércio de alimentos e bebidas com arquitetura de microsserviços

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![React](https://img.shields.io/badge/React-18-blue)
![TypeScript](https://img.shields.io/badge/TypeScript-5-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Status](https://img.shields.io/badge/Status-Operacional-success)

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
│   API Gateway   │  ← JWT Auth + RBAC + Rate Limiting
│   (porta 8000)  │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┬──────────┐
    │         │        │        │          │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐ ┌───▼────┐
│Cliente│ │Produto│ │Estoque│ │Vendas│ │  Loja  │
│ 8001  │ │ 8002  │ │ 8003  │ │ 8004 │ │  3000  │
└───────┘ └───────┘ └───────┘ └──────┘ └────────┘
```

**5 microsserviços independentes** | **Database per Service** | **Event-Driven** | **Redis Cache**

---

## 📚 Documentação Essencial

### 🎯 Para Começar
- 📖 [O SISTEMA.md](./O%20SISTEMA.md) - Visão geral completa
- ⚡ [QUICK-START.md](./QUICK-START.md) - Setup em 5 minutos

### 💻 Para Desenvolver
- 🎨 [FRONTEND_IMPLEMENTACAO.md](./FRONTEND_IMPLEMENTACAO.md) - Guia de implementação frontend
- ✅ [CHECKLIST_DESENVOLVIMENTO.md](./CHECKLIST_DESENVOLVIMENTO.md) - Checklist de desenvolvimento

### 📁 Documentação Completa
- 📂 [docs/01-principal/](./docs/01-principal/) - Documentação principal
- 📂 [docs/02-desenvolvimento/](./docs/02-desenvolvimento/) - Guias técnicos
- 📂 [docs/03-changelogs/](./docs/03-changelogs/) - Histórico de mudanças
- 📂 [docs/04-configuracao/](./docs/04-configuracao/) - Configurações e integrações
- 📂 [docs/05-seguranca/](./docs/05-seguranca/) - Segurança e compliance

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

### Sprint 2 (1-2 semanas) - PDV 🔥
- [ ] Lista de vendas
- [ ] Interface PDV
- [ ] Confirmação de vendas
- [ ] Detalhes da venda

### Sprint 3 (1-2 semanas) - Estoque 🔥
- [ ] Lista de produtos em estoque
- [ ] Movimentações (entrada/saída)
- [ ] Ajustes de inventário
- [ ] Histórico de movimentações

📋 **Detalhes**: [FRONTEND_IMPLEMENTACAO.md](./FRONTEND_IMPLEMENTACAO.md)

---

## 📝 Comandos Úteis

```bash
# Desenvolvimento
docker-compose up -d              # Subir todos os serviços
docker-compose logs -f [serviço]  # Ver logs
docker-compose restart [serviço]  # Reiniciar serviço
docker-compose down               # Parar tudo

# Frontend
cd frontend
npm run dev                       # Rodar em desenvolvimento
npm run build                     # Build de produção

# Backend
cd services/[serviço]
alembic upgrade head              # Rodar migrations
python seed.py                    # Popular dados de teste
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
git checkout -b feature/nova-feature

# 2. Commit (seguindo Conventional Commits)
git commit -m "feat(modulo): adiciona nova funcionalidade"

# 3. Push e PR
git push origin feature/nova-feature
```

**Convenções**: Veja [.kiro/steering/git-conventions.md](./.kiro/steering/git-conventions.md)

---

## 📄 Licença

**Propriedade de Runas** - Todos os direitos reservados.

Este software é proprietário e confidencial.

📖 [LICENSE.md](./docs/01-principal/LICENSE.md)

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
