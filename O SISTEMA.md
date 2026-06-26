# 🏪 Runas

> Sistema ERP completo para comércio de alimentos e bebidas com arquitetura de microsserviços

![Python](https://img.shields.io/badge/Python-3.12-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue)
![Docker](https://img.shields.io/badge/Docker-Ready-blue)
![Status](https://img.shields.io/badge/MVP-100%25%20Funcional-success)
![License](https://img.shields.io/badge/License-Proprietary-red)

---

## 📋 Sobre o Projeto

O **Runas** é uma solução completa para gestão de pequenos e médios comércios de alimentos e bebidas, oferecendo:

- ✅ **Gestão de Clientes** com crédito fiado e múltiplos endereços
- ✅ **Catálogo de Produtos** com variantes e fornecedores
- ✅ **Controle de Estoque** em tempo real
- ✅ **Sistema de Vendas** (balcão e online)
- ✅ **Gestão Financeira** e cobranças automatizadas
- ✅ **Notificações via WhatsApp** (Evolution API)
- ✅ **Pagamentos via PIX** (Mercado Pago)

---

## 🚀 Quick Start

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

**Pronto!** O sistema está rodando. 🎉

### Acessar a Aplicação

**Desenvolvimento Local**:
- **Frontend**: http://localhost:3000
- **API Gateway**: http://localhost:8000
- **Documentação API (Swagger)**: http://localhost:8000/docs

**Com Cloudflare Tunnel**:
- **Frontend**: https://www.runaserp.com.br
- **API Gateway**: https://www.runaserp.com.br/api
- **Documentação API**: https://www.runaserp.com.br/api/docs

### Login Padrão

```
Email: admin@runas.com
Senha: Admin@123
```

📖 **Guia completo**: [QUICK-START.md](./QUICK-START.md)

---

## 🏗️ Arquitetura

O sistema é composto por **8 serviços** (1 API Gateway + 7 microsserviços):

```
┌─────────────────┐
│   API Gateway   │  ← Autenticação JWT + Roteamento + OAuth2
│   (porta 8000)  │
└────────┬────────┘
         │
    ┌────┴────┬────────┬─────────┬──────────┬────────────┬─────────┐
    │         │        │         │          │            │         │
┌───▼───┐ ┌──▼────┐ ┌──▼────┐ ┌──▼───┐ ┌────▼────┐ ┌─────▼─────┐ ┌───▼───┐
│Empresa│ │Cliente│ │Produto│ │Estoque│ │Financeiro│ │Notificação│ │Vendas │
│ 8001  │ │ 8002  │ │ 8003  │ │ 8004  │ │  8005   │ │   8006   │ │ 8007  │
└───────┘ └───────┘ └───────┘ └───────┘ └─────────┘ └──────────┘ └───────┘
    │         │         │         │          │            │          │
    └─────────┴─────────┴─────────┴──────────┴────────────┴──────────┘
                                  │
                       ┌──────────┴──────────┐
                       │                     │
                  ┌────▼────┐          ┌─────▼────┐
                  │RabbitMQ │          │  Redis   │
                  └─────────┘          └──────────┘
```

### Características Técnicas

- ✅ **8 Serviços** - 1 API Gateway + 7 microsserviços independentes
- ✅ **Database per Service** - Cada microsserviço tem seu próprio schema PostgreSQL
- ✅ **Multi-tenancy** - Isolamento de dados por empresa_id
- ✅ **Event-Driven** - Comunicação assíncrona via RabbitMQ
- ✅ **Cache Distribuído** - Redis para sessões e blacklist de tokens
- ✅ **API Gateway** - Ponto único de entrada com autenticação centralizada (OAuth2 + JWT)
- ✅ **Health Checks** - Monitoramento de saúde de todos os serviços
- ✅ **Docker Compose** - Orquestração completa de containers
- ✅ **Cloudflare Tunnel** - Acesso externo seguro (www.runaserp.com.br)

---

## 📊 Status do Sistema (Junho 2026)

### ✅ Componentes Completos (Backend + Frontend)

| Componente | Status | Endpoints | Descrição |
|------------|--------|-----------|-----------|
| **API Gateway** | 🟢 100% | 15 | Autenticação JWT, OAuth2, RBAC, Proxy, Rate Limiting |
| **Serviço Empresas** | 🟢 100% | 8 | CRUD de empresas, multi-tenancy |
| **Serviço Clientes** | 🟢 100% | 12 | CRUD de clientes (PF/PJ), endereços, crédito |
| **Serviço Produtos** | 🟢 100% | 25 | CRUD de produtos, categorias, variantes, fornecedores |
| **Loja Online** | 🟢 100% | 26 | Catálogo público, carrinho, checkout, rastreamento |
| **Infraestrutura** | 🟢 100% | - | PostgreSQL unificado com schemas, Redis, RabbitMQ |

**Total Backend**: 86 endpoints REST funcionais | ~18.000 linhas de código  
**Total Frontend**: Interface completa com React + TypeScript

### 🟡 Componentes Backend Completos (Frontend Pendente)

| Serviço | Backend | Frontend | Prioridade |
|---------|---------|----------|------------|
| **Vendas/PDV** | 🟢 100% | 🔴 0% | 🔥 Alta |
| **Estoque** | 🟢 100% | 🔴 0% | 🔥 Alta |

### 🔴 Próximos Módulos

| Serviço | Prioridade | Status |
|---------|-----------|--------|
| **Financeiro** | Média | 🔴 Planejado |
| **Notificações** | Média | 🔴 Planejado |
| **Testes Unitários** | Alta | 🔴 Planejado |

📖 **Status detalhado**: [docs/mvp/STATUS-FINAL.md](./docs/mvp/STATUS-FINAL.md)

---

## 🛠️ Tecnologias

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

## 📦 Estrutura do Projeto

```
erp-runas/
├── 📄 README.md                    # Documentação principal
├── 📄 LEIA-ME-PRIMEIRO.md          # Ponto de entrada
├── 📄 QUICK-START.md               # Guia rápido
├── 📄 LICENSE.md                   # Licença
├── 📄 docker-compose.yml           # Orquestração
├── 📄 Makefile                     # Comandos úteis
├── 📄 .env                         # Variáveis de ambiente
│
├── 📁 api-gateway/                 # Gateway de autenticação
│   ├── auth/                       # JWT e OAuth2
│   ├── middleware/                 # Rate limit e logging
│   ├── models/                     # Modelo de usuário
│   ├── routers/                    # Endpoints
│   └── main.py
│
├── 📁 services/                    # Microsserviços
│   ├── empresas/                   # Multi-tenancy (empresas)
│   ├── clientes/                   # Gestão de clientes
│   ├── produtos/                   # Produtos e catálogo
│   ├── estoque/                    # Controle de estoque
│   ├── vendas/                     # Carrinho e pedidos
│   ├── financeiro/                 # Contas a receber
│   └── notificacoes/               # WhatsApp
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

## 🧪 Testes

### Testes Automatizados

```bash
# Executar todos os testes do MVP
bash tests/test-mvp.sh
```

O script testa automaticamente:
- ✅ Health checks de todos os serviços
- ✅ Autenticação e geração de tokens
- ✅ CRUD de clientes via gateway
- ✅ CRUD de produtos via gateway
- ✅ Logout e blacklist de tokens

### Testes Manuais

Consulte o guia completo com exemplos de cURL:
- 📖 [docs/mvp/TESTE-MANUAL.md](./docs/mvp/TESTE-MANUAL.md)
- 📋 [docs/mvp/CHECKLIST-VALIDACAO.md](./docs/mvp/CHECKLIST-VALIDACAO.md)

---

## 🔐 Autenticação e Autorização

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

## 📝 Comandos Úteis

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

## 🔄 Fluxos Principais

### Fluxo de Venda à Vista

1. Cliente adiciona produtos ao carrinho
2. Cliente finaliza checkout escolhendo PIX
3. Sistema gera QR Code do Mercado Pago
4. Cliente paga
5. Webhook confirma pagamento
6. Sistema dá baixa no estoque
7. Notificação enviada via WhatsApp

### Fluxo de Venda Fiada

1. Cliente adiciona produtos ao carrinho
2. Cliente finaliza checkout escolhendo "Fiado"
3. Sistema verifica crédito disponível
4. Sistema debita crédito do cliente
5. Sistema cria conta a receber
6. Pedido confirmado automaticamente
7. Baixa no estoque
8. Notificação enviada

---

## 🌐 Integrações

### Mercado Pago (Pagamentos PIX)

- Ambiente: Sandbox (desenvolvimento) / Produção
- Webhook para confirmação automática
- Validação HMAC-SHA256

### Evolution API (WhatsApp)

- Envio de notificações
- Confirmação de pedidos
- Lembretes de cobrança
- Alertas de estoque

📖 **Configuração**: [docs/EVOLUTION-API-SETUP.md](./docs/EVOLUTION-API-SETUP.md)

---

## 📚 Documentação

### Documentação Essencial

- 📖 [LEIA-ME-PRIMEIRO.md](./LEIA-ME-PRIMEIRO.md) - Ponto de entrada
- ⚡ [QUICK-START.md](./QUICK-START.md) - Guia rápido de 5 minutos
- 📊 [docs/mvp/RESUMO-EXECUTIVO.md](./docs/mvp/RESUMO-EXECUTIVO.md) - Visão geral do MVP
- ✅ [docs/mvp/STATUS-FINAL.md](./docs/mvp/STATUS-FINAL.md) - Status detalhado

### Documentação Técnica

- 🏗️ [docs/ARQUITETURA-COMUNICACAO.md](./docs/ARQUITETURA-COMUNICACAO.md) - Arquitetura
- 📐 [docs/ESPECIFICACAO-TECNICA.md](./docs/ESPECIFICACAO-TECNICA.md) - Especificações
- 🗺️ [docs/MAPEAMENTO-ROTAS.md](./docs/MAPEAMENTO-ROTAS.md) - Endpoints
- 💻 [docs/GUIA-IMPLEMENTACAO.md](./docs/GUIA-IMPLEMENTACAO.md) - Guia de desenvolvimento

### Testes

- 🧪 [docs/mvp/TESTE-MANUAL.md](./docs/mvp/TESTE-MANUAL.md) - Guia de testes
- 📋 [docs/mvp/CHECKLIST-VALIDACAO.md](./docs/mvp/CHECKLIST-VALIDACAO.md) - Checklist

---

## 🤝 Contribuindo

Este é um projeto proprietário. Para contribuir:

1. Crie uma branch: `git checkout -b feature/nova-feature`
2. Commit suas mudanças: `git commit -m 'Add nova feature'`
3. Push para a branch: `git push origin feature/nova-feature`
4. Abra um Pull Request

---

## 📄 Licença

**Propriedade de Runas** - Todos os direitos reservados.

Este software é proprietário e confidencial. Uso não autorizado é estritamente proibido.

📖 **Licença completa**: [LICENSE.md](./LICENSE.md)

---

## 👥 Equipe

Desenvolvido por **Runas**

---

## 📞 Suporte

Para suporte técnico:

- **Email**: suporte@runas.com
- **Documentação**: [docs/](./docs/)
- **Issues**: Abra uma issue no repositório

---

## 🎯 Roadmap

### Q2 2026
- [x] MVP com Gateway, Clientes e Produtos
- [x] Loja Online completa (catálogo, carrinho, checkout)
- [x] API de Vendas completa
- [x] API de Estoque completa
- [ ] Frontend Vendas/PDV
- [ ] Frontend Estoque
- [ ] Testes unitários (80% coverage)

### Q3 2026
- [ ] Serviço Financeiro
- [ ] Serviço de Notificações
- [ ] Integração Mercado Pago completa
- [ ] Integração WhatsApp (Evolution API)

### Q4 2026
- [ ] Dashboard administrativo completo
- [ ] Relatórios e analytics
- [ ] App mobile
- [ ] CI/CD completo

📖 **Estimativas**: [docs/ESTIMATIVA-HORAS-MVP.md](./docs/ESTIMATIVA-HORAS-MVP.md)

---

## 📊 Métricas do Projeto

- **Linhas de código**: ~18.000 linhas Python
- **Arquivos criados**: ~200 arquivos
- **Endpoints REST**: 86 endpoints funcionais
- **Microsserviços**: 8 serviços (1 Gateway + 7 microsserviços)
- **Banco de dados**: 1 PostgreSQL com 8 schemas isolados
- **Frontend**: React + TypeScript com Loja Online completa
- **Multi-tenancy**: 100% implementado (isolamento por empresa_id)
- **Cobertura de testes**: Em desenvolvimento

---

**Versão**: 2.0.0  
**Última atualização**: 23 de Junho de 2026  
**Status**: ✅ Sistema Operacional com Loja Online Completa

---

<div align="center">

**[⬆ Voltar ao topo](#-runas)**

Desenvolvido por **Equipe DenebCorp**

</div>
