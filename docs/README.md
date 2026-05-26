# ERP Runas - Documentação

Sistema ERP completo para comércio de alimentos e bebidas, construído com arquitetura de microsserviços.

## 📚 Índice da Documentação

### 🚀 Para Começar

1. **[README Principal](../README.md)**
   - Quick start
   - Visão geral do projeto
   - Comandos básicos
   - Como acessar os serviços

2. **[Projeto Criado](../PROJETO-CRIADO.md)**
   - Resumo executivo
   - O que foi entregue
   - Status atual
   - Próximos passos

### 📖 Documentação Técnica

3. **[Especificação Técnica](./ESPECIFICACAO-TECNICA.md)**
   - Requisitos completos (1000 linhas)
   - Regras de negócio detalhadas
   - Modelos de dados
   - Endpoints de cada serviço

4. **[Arquitetura Visual](./ARQUITETURA-VISUAL.md)**
   - Diagramas de arquitetura
   - Fluxos de processo
   - Modelo de dados
   - Comunicação entre serviços

5. **[Sumário do Projeto](./SUMARIO-PROJETO.md)**
   - Visão geral completa
   - Estrutura de arquivos
   - Métricas do projeto
   - Checklist de entrega

6. **[Arquivos Criados](./ARQUIVOS-CRIADOS.md)**
   - Lista completa de 148 arquivos
   - Estatísticas detalhadas
   - Organização por categoria

### 🛠️ Para Desenvolvimento

7. **[Guia de Implementação](./GUIA-IMPLEMENTACAO.md)**
   - Passo a passo detalhado
   - Exemplos de código
   - Ordem de implementação
   - Boas práticas

8. **[Estimativa de Horas](./ESTIMATIVA-HORAS-MVP.md)**
   - Breakdown de 518 horas
   - Cronograma sugerido
   - Métricas por serviço
   - Estimativa com equipe

### 🔧 Setup e Configuração

9. **[Evolution API Setup](./EVOLUTION-API-SETUP.md)**
   - Configuração do WhatsApp
   - Templates de mensagens
   - Testes de envio
   - Troubleshooting

### 📁 Documentação Original

10. **[Documentação Original](./Documentacao-Original/)**
    - Catálogo de Vendas 2026
    - Apresentação ERP
    - Protótipo Baixo Nível
    - Documento Runas
    - Diagramas UML e ER

## 🚀 Quick Start

```bash
# 1. Clone o repositório
git clone <repo-url>
cd erp-runas

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas configurações

# 3. Suba os serviços
make up

# 4. Execute as migrations
make migrate

# 5. Popule com dados de teste (opcional)
make seed

# 6. Acesse a aplicação
# API Gateway: http://localhost:8000
# Documentação API: http://localhost:8000/docs
# pgAdmin: http://localhost:5050
# RabbitMQ: http://localhost:15672
```

## 🏗️ Estrutura do Projeto

```
erp-runas/
├── api-gateway/          # Gateway de autenticação e roteamento
├── services/
│   ├── clientes/         # Gestão de clientes e crédito
│   ├── produtos/         # Produtos, variantes e catálogo
│   ├── estoque/          # Controle de estoque
│   ├── vendas/           # Carrinho, pedidos e checkout
│   ├── financeiro/       # Contas a receber e pagamentos
│   └── notificacoes/     # Notificações via WhatsApp
├── shared/               # Código compartilhado
├── docs/                 # Documentação
├── docker-compose.yml    # Orquestração de containers
├── Makefile              # Comandos úteis
└── .env.example          # Exemplo de configuração
```

## 🛠️ Tecnologias

- **Linguagem**: Python 3.12
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.x (async)
- **Banco de Dados**: PostgreSQL 15
- **Mensageria**: RabbitMQ
- **Cache**: Redis
- **Tarefas Assíncronas**: Celery
- **Notificações**: Evolution API (WhatsApp)
- **Pagamentos**: Mercado Pago
- **Containerização**: Docker & Docker Compose

## 📦 Microsserviços

| Serviço | Porta | Descrição |
|---------|-------|-----------|
| API Gateway | 8000 | Autenticação JWT e roteamento |
| Clientes | 8001 | Gestão de clientes, crédito e endereços |
| Produtos | 8002 | Produtos, variantes, catálogo e fornecedores |
| Estoque | 8003 | Controle de estoque e movimentações |
| Vendas | 8004 | Carrinho, pedidos, checkout e pagamentos |
| Financeiro | 8005 | Contas a receber e pagamentos fiados |
| Notificações | 8006 | Envio de notificações via WhatsApp |

## 🔐 Autenticação

O sistema utiliza OAuth2 com JWT. Todos os endpoints (exceto públicos) requerem autenticação.

### Roles

- **ADMIN**: Acesso total a todos os endpoints
- **OPERADOR**: Acesso limitado (leitura de produtos, criação de pedidos, consulta de clientes)

### Endpoints Públicos

- `POST /auth/login` - Login
- `POST /auth/refresh` - Renovar token
- `GET /catalogo` - Catálogo de produtos
- `POST /carrinho/*` - Operações de carrinho
- `POST /carrinho/{token}/checkout` - Finalizar compra

## 📊 Monitoramento

- **pgAdmin**: http://localhost:5050 (admin@runas.local / admin123)
- **RabbitMQ Management**: http://localhost:15672 (guest / guest)
- **Evolution API**: http://localhost:8080

## 🧪 Testes

```bash
# Todos os testes
make test

# Teste de um serviço específico
make test-service SERVICE=clientes

# Com cobertura
docker-compose exec clientes pytest --cov=. --cov-report=html
```

## 📝 Comandos Úteis

```bash
make help              # Lista todos os comandos
make up                # Sobe todos os serviços
make down              # Para todos os serviços
make logs              # Mostra logs
make migrate           # Executa migrations
make seed              # Popula dados de teste
make test              # Executa testes
make lint              # Executa linting
make health            # Verifica saúde dos serviços
make backup-db         # Faz backup dos bancos
```

## 🔧 Desenvolvimento

Para desenvolvimento local sem Docker:

```bash
# 1. Suba apenas a infraestrutura
make dev

# 2. Crie um ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate  # Windows

# 3. Instale dependências
cd api-gateway
pip install -r requirements.txt

# 4. Execute o serviço
uvicorn main:app --reload --port 8000
```

## 📖 Documentação da API

Após subir os serviços, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🐛 Troubleshooting

Consulte o [Guia de Troubleshooting](./08-TROUBLESHOOTING.md) para problemas comuns.

## 📄 Licença

Propriedade de Runas - Todos os direitos reservados.

## 👥 Equipe

Desenvolvido por [Sua Equipe]

## 📞 Suporte

Para suporte, entre em contato: suporte@runas.com


---

## 🎯 Guia Rápido por Objetivo

### Quero entender o projeto
→ Leia: [README Principal](../README.md) + [Arquitetura Visual](./ARQUITETURA-VISUAL.md)

### Quero começar a desenvolver
→ Leia: [Guia de Implementação](./GUIA-IMPLEMENTACAO.md) + [Especificação Técnica](./ESPECIFICACAO-TECNICA.md)

### Quero estimar tempo/custo
→ Leia: [Estimativa de Horas](./ESTIMATIVA-HORAS-MVP.md)

### Quero configurar WhatsApp
→ Leia: [Evolution API Setup](./EVOLUTION-API-SETUP.md)

### Quero ver o que foi feito
→ Leia: [Projeto Criado](../PROJETO-CRIADO.md) + [Sumário](./SUMARIO-PROJETO.md)

---

## 📊 Status da Documentação

| Documento | Status | Páginas | Última Atualização |
|-----------|--------|---------|-------------------|
| README Principal | ✅ Completo | 3 | 2026-05-14 |
| Projeto Criado | ✅ Completo | 5 | 2026-05-14 |
| Especificação Técnica | ✅ Completo | 40 | 2026-05-14 |
| Arquitetura Visual | ✅ Completo | 8 | 2026-05-14 |
| Guia de Implementação | ✅ Completo | 12 | 2026-05-14 |
| Estimativa de Horas | ✅ Completo | 15 | 2026-05-14 |
| Evolution API Setup | ✅ Completo | 6 | 2026-05-14 |
| Sumário do Projeto | ✅ Completo | 8 | 2026-05-14 |
| Arquivos Criados | ✅ Completo | 6 | 2026-05-14 |

**Total**: ~103 páginas de documentação

---

## 🚀 Quick Start

```bash
# 1. Clone o repositório
git clone <repo-url>
cd erp-runas

# 2. Configure as variáveis de ambiente
cp .env.example .env
# Edite o .env com suas configurações

# 3. Suba os serviços
make up

# 4. Execute as migrations
make migrate

# 5. Popule com dados de teste (opcional)
make seed

# 6. Acesse a aplicação
# API Gateway: http://localhost:8000
# Documentação API: http://localhost:8000/docs
# pgAdmin: http://localhost:5050
# RabbitMQ: http://localhost:15672
```

---

## 🏗️ Arquitetura

O sistema é composto por **7 microsserviços independentes**:

```
API Gateway (8000) → Autenticação JWT + Roteamento
├── Clientes (8001) → Gestão de clientes e crédito
├── Produtos (8002) → Produtos, variantes e catálogo
├── Estoque (8003) → Controle de estoque
├── Vendas (8004) → Carrinho, pedidos e checkout
├── Financeiro (8005) → Contas a receber
└── Notificações (8006) → WhatsApp via Evolution API
```

Cada microsserviço possui:
- ✅ Banco de dados PostgreSQL dedicado
- ✅ API REST independente
- ✅ Comunicação assíncrona via RabbitMQ
- ✅ Cache com Redis

---

## 🛠️ Tecnologias

- **Linguagem**: Python 3.12
- **Framework**: FastAPI
- **ORM**: SQLAlchemy 2.x (async)
- **Banco de Dados**: PostgreSQL 15
- **Mensageria**: RabbitMQ
- **Cache**: Redis 7
- **Tasks**: Celery
- **Notificações**: Evolution API (WhatsApp)
- **Pagamentos**: Mercado Pago (PIX)
- **Containerização**: Docker + Docker Compose

---

## 📝 Comandos Úteis

```bash
make help              # Lista todos os comandos
make up                # Sobe todos os serviços
make down              # Para todos os serviços
make logs              # Mostra logs
make migrate           # Executa migrations
make seed              # Popula dados de teste
make test              # Executa testes
make lint              # Executa linting
make health            # Verifica saúde dos serviços
make backup-db         # Faz backup dos bancos
```

---

## 🧪 Testes

```bash
# Todos os testes
make test

# Teste de um serviço específico
make test-service SERVICE=clientes

# Com cobertura
docker-compose exec clientes pytest --cov=. --cov-report=html
```

---

## 📖 Documentação da API

Após subir os serviços, acesse:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

---

## 🔐 Autenticação

O sistema utiliza OAuth2 com JWT. Todos os endpoints (exceto públicos) requerem autenticação.

### Roles

- **ADMIN**: Acesso total a todos os endpoints
- **OPERADOR**: Acesso limitado (leitura de produtos, criação de pedidos, consulta de clientes)

### Login Padrão

```
Email: admin@runas.com
Senha: Admin@123
```

---

## 📞 Suporte

Para suporte, consulte:
- [Guia de Implementação](./GUIA-IMPLEMENTACAO.md)
- [Especificação Técnica](./ESPECIFICACAO-TECNICA.md)
- [Evolution API Setup](./EVOLUTION-API-SETUP.md)

---

**Última atualização**: 2026-05-14  
**Versão**: 1.0.0  
**Total de Documentação**: ~103 páginas
