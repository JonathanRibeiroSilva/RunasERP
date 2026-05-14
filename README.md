# ERP Runas

> Sistema ERP completo para comércio de alimentos e bebidas com arquitetura de microsserviços

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Status](https://img.shields.io/badge/MVP-100%25%20Funcional-success)
![License](https://img.shields.io/badge/License-Proprietary-red)

---

## Sobre o Projeto

O **ERP Runas** é uma solução completa para gestão de pequenos e médios comércios de alimentos e bebidas, oferecendo:

-  **Gestão de Clientes** com crédito fiado e múltiplos endereços
-  **Catálogo de Produtos** com variantes e fornecedores
-  **Controle de Estoque** em tempo real com lotes e validade
-  **Sistema de Vendas** (balcão e online) - Em desenvolvimento
-  **Gestão Financeira** e cobranças automatizadas - Em desenvolvimento
-  **Notificações via WhatsApp** (Evolution API) - Em desenvolvimento
-  **Pagamentos via PIX** (Mercado Pago) - Em desenvolvimento

---

## Quick Start

### Pré-requisitos

- Docker 20.10+
- Docker Compose 2.0+
- Git Bash (Windows) ou terminal Unix-like

### Instalação em 3 Passos

```bash
# 1. Clone o repositório
git clone <repo-url>
cd erp-runas

# 2. Suba todos os serviços
docker-compose up -d

# 3. Execute os testes
bash tests/test-mvp.sh
```

**Pronto!** O sistema está rodando. 

### Acessar a Aplicação

- **API Gateway**: http://localhost:8000/docs
- **Serviço Clientes**: http://localhost:8001/docs
- **Serviço Produtos**: http://localhost:8002/docs
- **Serviço Estoque**: http://localhost:8003/docs
- **pgAdmin**: http://localhost:5050 (admin@runas.local / admin123)
- **RabbitMQ Management**: http://localhost:15672 (guest / guest)

### Login Padrão

```
Email: admin@runas.com
Senha: Admin@123
```

 **Guia completo**: [QUICK-START.md](./QUICK-START.md)  
 **Teste de Estoque**: [TESTE-ESTOQUE.md](./TESTE-ESTOQUE.md)

---

## Arquitetura

O sistema é composto por **7 microsserviços independentes**:

```
┌─────────────────┐
│   API Gateway   │  ← Autenticação JWT + Roteamento
│   (porta 8000)  │
└────────┬────────┘
         │
    ┌────┴────┬────────┬────────┬──────────┬────────────┐
    │         │        │        │          │            │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌──▼───┐ ┌────▼────┐ ┌────▼─────┐
│Cliente│ │Produto│ │Estoque│ │Vendas│ │Financeiro│ │Notificação│
│ 8001  │ │ 8002  │ │ 8003  │ │ 8004 │ │  8005   │ │   8006   │
│  ✅   │ │  ✅   │ │  ✅   │ │  🔴  │ │   🔴    │ │   🔴     │
└───────┘ └───────┘ └───────┘ └──────┘ └─────────┘ └──────────┘
    │         │         │         │          │            │
    └─────────┴─────────┴─────────┴──────────┴────────────┘
                         │
              ┌──────────┴──────────┐
              │                     │
         ┌────▼────┐          ┌────▼────┐
         │RabbitMQ │          │  Redis  │
         └─────────┘          └─────────┘
```

### Características Técnicas

- **Database per Service** - Cada microsserviço tem seu próprio PostgreSQL
- **Event-Driven** - Comunicação assíncrona via RabbitMQ
- **Cache Distribuído** - Redis para sessões e blacklist de tokens
- **API Gateway** - Ponto único de entrada com autenticação centralizada
- **Service-to-Service Communication** - HTTP para comunicação síncrona
- **Health Checks** - Monitoramento de saúde de todos os serviços
- **Docker Compose** - Orquestração completa de containers

---

## Status do MVP

### Componentes Implementados (100%)

| Componente | Status | Endpoints | Descrição |
|------------|--------|-----------|-----------|
| **API Gateway** | 🟢 100% | 15 | Autenticação JWT, RBAC, Proxy, Rate Limiting |
| **Serviço Clientes** | 🟢 100% | 12 | CRUD de clientes (PF/PJ), endereços, crédito |
| **Serviço Produtos** | 🟢 100% | 25 | CRUD de produtos, categorias, variantes, fornecedores |
| **Serviço Estoque** | 🟢 100% | 18 | Controle de estoque, movimentações, lotes, inventário |
| **Infraestrutura** | 🟢 100% | - | 8 bancos PostgreSQL, Redis, RabbitMQ, pgAdmin |

**Total**: 70 endpoints REST funcionais | ~15.000 linhas de código

### Próximos Passos

| Serviço | Prioridade | Status |
|---------|-----------|--------|
| **Vendas** | Alta | 🔴 Próximo na fila |
| **Financeiro** | Média | 🔴 Planejado |
| **Notificações** | Média | 🔴 Planejado |
| **Testes Unitários** | Alta | 🔴 Planejado |

📖 **Roadmap completo**: [FEATURES-FUTURAS.md](./FEATURES-FUTURAS.md)

---

## Tecnologias

| Categoria | Tecnologia | Versão |
|-----------|-----------|--------|
| **Linguagem** | Python | 3.12 |
| **Framework** | FastAPI | 0.109 |
| **ORM** | SQLAlchemy (async) | 2.0 |
| **Banco de Dados** | PostgreSQL | 15 |
| **Migrations** | Alembic | 1.13 |
| **Mensageria** | RabbitMQ | 3.12 |
| **Cache** | Redis | 7 |
| **Tasks** | Celery | 5.3 |
| **Validação** | Pydantic | 2.5 |
| **Autenticação** | OAuth2 + JWT | - |
| **Notificações** | Evolution API | latest |
| **Pagamentos** | Mercado Pago | - |
| **Containerização** | Docker + Compose | - |
| **Testes** | Pytest | - |

---

## Estrutura do Projeto

```
erp-runas/
├── 📄 README.md                    # Documentação principal
├── 📄 QUICK-START.md               # Guia rápido
├── 📄 TESTE-ESTOQUE.md             # Guia de teste do estoque
├── 📄 FEATURES-FUTURAS.md          # Roadmap e features
├── 📄 LICENSE.md                   # Licença
├── 📄 docker-compose.yml           # Orquestração
├── 📄 Makefile                     # Comandos úteis
├── 📄 .env                         # Variáveis de ambiente
│
├── 📁 api-gateway/                 # Gateway de autenticação ✅
│   ├── auth/                       # JWT e OAuth2
│   ├── middleware/                 # Rate limit e logging
│   ├── models/                     # Modelo de usuário
│   ├── routers/                    # Endpoints
│   └── main.py
│
├── 📁 services/                    # Microsserviços
│   ├── clientes/                   # Gestão de clientes ✅
│   ├── produtos/                   # Produtos e catálogo ✅
│   ├── estoque/                    # Controle de estoque ✅
│   ├── vendas/                     # Carrinho e pedidos 🔴
│   ├── financeiro/                 # Contas a receber 🔴
│   └── notificacoes/               # WhatsApp 🔴
│
├── 📁 docs/                        # Documentação
│   ├── mvp/                        # Docs do MVP
│   ├── historico/                  # Histórico
│   └── Documentacao-Original/      # Docs originais
│
├── 📁 tests/                       # Testes
│   ├── test-mvp.sh                 # Testes automatizados
│   └── ...
│
├── 📁 scripts/                     # Scripts utilitários
│   └── ...
│
└── 📁 shared/                      # Código compartilhado
    ├── events/                     # Eventos de domínio
    ├── exceptions.py               # Exceções customizadas
    └── pagination.py               # Paginação padrão
```

---

## Testes

### Testes Automatizados

```bash
# Executar todos os testes do MVP
bash tests/test-mvp.sh
```

O script testa automaticamente:
- Health checks de todos os serviços
- Autenticação e geração de tokens
- CRUD de clientes via gateway
- CRUD de produtos via gateway
- Logout e blacklist de tokens

### Testes Manuais

Consulte os guias completos:
- [QUICK-START.md](./QUICK-START.md) - Testes básicos
- [TESTE-ESTOQUE.md](./TESTE-ESTOQUE.md) - Testes de estoque
- [docs/mvp/TESTE-MANUAL.md](./docs/mvp/TESTE-MANUAL.md) - Testes completos

---

## Autenticação e Autorização

O sistema utiliza **OAuth2 com JWT** e **RBAC (Role-Based Access Control)**.

### Roles Disponíveis

| Role | Permissões |
|------|-----------|
| **ADMIN** | Acesso total a todos os endpoints |
| **GERENTE** | Gestão de produtos, clientes, vendas e relatórios |
| **VENDEDOR** | Criação de vendas, consulta de clientes e produtos |
| **OPERADOR** | Apenas leitura de produtos e criação de pedidos |

### Fluxo de Autenticação

```bash
# 1. Login
POST /auth/login
Body: username=admin@runas.com&password=Admin@123

# 2. Usar token
GET /api/clientes
Header: Authorization: Bearer {access_token}

# 3. Renovar token (antes de expirar)
POST /auth/refresh
Body: refresh_token={refresh_token}

# 4. Logout
POST /auth/logout
Header: Authorization: Bearer {access_token}
```

**Tokens**:
- `access_token`: Expira em 30 minutos
- `refresh_token`: Expira em 7 dias

---

## Comandos Úteis

```bash
# Gerenciamento de Containers
make up                # Subir todos os serviços
make down              # Parar todos os serviços
make restart           # Reiniciar todos os serviços
make ps                # Ver status dos containers
make logs              # Ver logs de todos os serviços
make logs-gateway      # Logs do API Gateway
make logs-clientes     # Logs do serviço de clientes
make logs-produtos     # Logs do serviço de produtos
make logs-estoque      # Logs do serviço de estoque

# Testes
make test              # Executar testes automatizados
make health            # Verificar saúde dos serviços

# Banco de Dados
make migrate           # Executar migrations
make seed              # Popula dados de teste
make backup-db         # Fazer backup dos bancos

# Limpeza
make clean             # Remove tudo (containers, volumes, imagens)

# Ajuda
make help              # Lista todos os comandos disponíveis
```

---

## Documentação

### Documentação Essencial

- [QUICK-START.md](./QUICK-START.md) - Guia rápido de 5 minutos
- [TESTE-ESTOQUE.md](./TESTE-ESTOQUE.md) - Guia de teste do estoque
- [FEATURES-FUTURAS.md](./FEATURES-FUTURAS.md) - Roadmap e features planejadas
- [docs/mvp/RESUMO-EXECUTIVO.md](./docs/mvp/RESUMO-EXECUTIVO.md) - Visão geral do MVP
- [docs/mvp/STATUS-FINAL.md](./docs/mvp/STATUS-FINAL.md) - Status detalhado

### Documentação Técnica

- [docs/ARQUITETURA-COMUNICACAO.md](./docs/ARQUITETURA-COMUNICACAO.md) - Arquitetura
- [docs/ESPECIFICACAO-TECNICA.md](./docs/ESPECIFICACAO-TECNICA.md) - Especificações
- [docs/MAPEAMENTO-ROTAS.md](./docs/MAPEAMENTO-ROTAS.md) - Endpoints
- [docs/GUIA-IMPLEMENTACAO.md](./docs/GUIA-IMPLEMENTACAO.md) - Guia de desenvolvimento

### Testes

- [docs/mvp/TESTE-MANUAL.md](./docs/mvp/TESTE-MANUAL.md) - Guia de testes
- [docs/mvp/CHECKLIST-VALIDACAO.md](./docs/mvp/CHECKLIST-VALIDACAO.md) - Checklist

---

## Contribuindo

Este é um projeto proprietário. Para contribuir:

1. Crie uma branch: `git checkout -b feature/nova-feature`
2. Commit suas mudanças: `git commit -m 'Add nova feature'`
3. Push para a branch: `git push origin feature/nova-feature`
4. Abra um Pull Request

---

## Licença

**Propriedade de Runas** - Todos os direitos reservados.

Este software é proprietário e confidencial. Uso não autorizado é estritamente proibido.

**Licença completa**: [LICENSE.md](./LICENSE.md)

---

## Equipe

Desenvolvido por **DenebCorp**

---

## 📞 Suporte

Para suporte técnico:

- **Email**: suporte@runas.com
- **Documentação**: [docs/](./docs/)
- **Issues**: Abra uma issue no repositório

---

## Roadmap

### Q2 2026 (Atual - Maio/Junho)
- [x] MVP com Gateway, Clientes e Produtos
- [x] Serviço de Estoque
- [ ] Serviço de Vendas
- [ ] Testes unitários (80% coverage)

### Q3 2026 (Julho-Setembro)
- [ ] Serviço Financeiro
- [ ] Serviço de Notificações
- [ ] Integração Mercado Pago
- [ ] Integração WhatsApp

### Q4 2026 (Outubro-Dezembro)
- [ ] Dashboard administrativo
- [ ] Relatórios e analytics
- [ ] App mobile
- [ ] CI/CD completo

📖 **Estimativas**: [docs/ESTIMATIVA-HORAS-MVP.md](./docs/ESTIMATIVA-HORAS-MVP.md)

---

## Métricas do Projeto

- **Linhas de código**: ~15.000 linhas Python
- **Arquivos criados**: ~150 arquivos
- **Endpoints REST**: 70 endpoints funcionais
- **Microsserviços**: 4 funcionais + 3 planejados
- **Bancos de dados**: 8 PostgreSQL
- **Cobertura de testes**: Em desenvolvimento

---

**Versão**: 1.0.0-MVP  
**Última atualização**: 2026-05-14  
**Status**: MVP 100% Funcional e Pronto para Testes

---

<div align="center">

**[⬆ Voltar ao topo](#-erp-runas)**

Feito com ❤️ pela equipe **DenebCorp**

</div>
