# Stack Tecnológico - Runas

> **Tecnologias, versões e justificativas técnicas**

---

## 🎯 Visão Geral

O Runas utiliza uma stack moderna e robusta, focada em **performance**, **escalabilidade** e **manutenibilidade**. Todas as tecnologias foram escolhidas com base em critérios de maturidade, comunidade ativa e adequação ao contexto de pequenos comércios.

---

## 🐍 Backend

### Linguagem e Framework

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **Python** | 3.12+ | Linguagem moderna, tipagem forte, ecossistema rico |
| **FastAPI** | 0.104+ | Framework assíncrono, alta performance, documentação automática |
| **Uvicorn** | 0.24+ | Servidor ASGI de alta performance |

**Por que Python?**
- Sintaxe clara e produtiva
- Ecossistema maduro para APIs
- Excelente suporte a async/await
- Comunidade ativa e bibliotecas de qualidade

**Por que FastAPI?**
- Performance comparável a Node.js e Go
- Validação automática com Pydantic
- Documentação OpenAPI/Swagger automática
- Suporte nativo a async/await
- Type hints e autocompletar no IDE

### Banco de Dados

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **PostgreSQL** | 15+ | Banco relacional robusto, ACID compliant, JSON support |
| **SQLAlchemy** | 2.0+ | ORM moderno com suporte async |
| **Alembic** | 1.12+ | Migrations versionadas e reversíveis |
| **asyncpg** | 0.29+ | Driver PostgreSQL assíncrono de alta performance |

**Por que PostgreSQL?**
- ACID compliant (transações seguras)
- Suporte a JSON (flexibilidade)
- Extensões poderosas (UUID, full-text search)
- Performance excelente
- Open source e gratuito

**Por que SQLAlchemy 2.0?**
- Suporte completo a async/await
- Type hints nativos
- Queries type-safe
- Migrations automáticas com Alembic

### Validação e Serialização

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **Pydantic** | 2.5+ | Validação de dados com type hints |
| **email-validator** | 2.1+ | Validação de emails |
| **python-cpf** | 1.0+ | Validação de CPF |
| **phonenumbers** | 8.13+ | Validação de telefones (formato E.164) |

**Por que Pydantic v2?**
- Performance 5-50x mais rápida que v1
- Validação em tempo de compilação
- Integração perfeita com FastAPI
- Mensagens de erro claras

### Autenticação e Segurança

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **python-jose** | 3.3+ | JWT encoding/decoding |
| **passlib** | 1.7+ | Hashing de senhas (bcrypt) |
| **python-multipart** | 0.0.6+ | Upload de arquivos |

**Por que JWT?**
- Stateless (escalável)
- Payload customizável
- Suporte a refresh tokens
- Padrão da indústria

**Por que bcrypt?**
- Algoritmo de hashing seguro
- Resistente a ataques de força bruta
- Custo computacional ajustável

### Cache e Sessões

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **Redis** | 7.0+ | Cache in-memory, sessões, rate limiting |
| **redis-py** | 5.0+ | Cliente Python para Redis |

**Por que Redis?**
- Performance extrema (in-memory)
- Estruturas de dados ricas
- TTL automático
- Pub/Sub para eventos

### Mensageria e Tarefas Assíncronas

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **RabbitMQ** | 3.12+ | Message broker robusto |
| **Celery** | 5.3+ | Tarefas assíncronas e agendadas |
| **aio-pika** | 9.3+ | Cliente RabbitMQ assíncrono |

**Por que RabbitMQ?**
- Garantia de entrega de mensagens
- Routing flexível (topic exchange)
- Dead letter queues
- Painel de administração

**Por que Celery?**
- Tarefas agendadas (Celery Beat)
- Retry automático
- Monitoramento (Flower)
- Integração com Redis/RabbitMQ

### Testes

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **pytest** | 7.4+ | Framework de testes moderno |
| **pytest-asyncio** | 0.21+ | Suporte a testes assíncronos |
| **pytest-cov** | 4.1+ | Cobertura de código |
| **httpx** | 0.25+ | Cliente HTTP assíncrono para testes |
| **faker** | 20.0+ | Geração de dados fake |

**Por que pytest?**
- Sintaxe simples e clara
- Fixtures poderosas
- Plugins ricos
- Relatórios detalhados

### Logging e Monitoramento

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **structlog** | 23.2+ | Logging estruturado (JSON) |
| **python-json-logger** | 2.0+ | Formatação JSON para logs |

**Por que logging estruturado?**
- Logs parseáveis por ferramentas
- Contexto rico (request_id, user_id)
- Facilita debugging
- Integração com ELK/Grafana

---

## ⚛️ Frontend

### Core

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **React** | 18.2+ | Biblioteca UI moderna e madura |
| **TypeScript** | 5.0+ | Type safety e autocompletar |
| **Vite** | 5.0+ | Build tool rápido |
| **React Router** | 6.20+ | Roteamento declarativo |

**Por que React?**
- Ecossistema maduro
- Componentes reutilizáveis
- Virtual DOM (performance)
- Comunidade gigante

**Por que TypeScript?**
- Detecção de erros em tempo de desenvolvimento
- Refatoração segura
- Documentação viva (types)
- Autocompletar no IDE

**Por que Vite?**
- Dev server instantâneo (HMR)
- Build otimizado (Rollup)
- Suporte nativo a TypeScript
- Plugins ricos

### UI e Estilo

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **Tailwind CSS** | 3.4+ | Utility-first CSS framework |
| **Headless UI** | 1.7+ | Componentes acessíveis sem estilo |
| **React Icons** | 4.12+ | Biblioteca de ícones |
| **Framer Motion** | 10.16+ | Animações fluidas |

**Por que Tailwind CSS?**
- Desenvolvimento rápido
- Design system consistente
- Tree-shaking automático
- Dark mode nativo

**Por que Headless UI?**
- Acessibilidade (WCAG AA)
- Keyboard navigation
- Screen reader support
- Sem opiniões de estilo

### State Management

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **React Query** | 5.0+ | Server state management |
| **Zustand** | 4.4+ | Client state management |
| **Context API** | Built-in | Global state simples |

**Por que React Query?**
- Cache automático
- Refetch inteligente
- Optimistic updates
- Devtools poderoso

**Por que Zustand?**
- API minimalista
- Performance excelente
- Sem boilerplate
- TypeScript first

### Forms e Validação

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **React Hook Form** | 7.49+ | Gerenciamento de formulários |
| **Zod** | 3.22+ | Schema validation |
| **@hookform/resolvers** | 3.3+ | Integração RHF + Zod |

**Por que React Hook Form?**
- Performance (uncontrolled inputs)
- API simples
- Validação flexível
- Integração com Zod

**Por que Zod?**
- Type inference automático
- Mensagens de erro customizáveis
- Composição de schemas
- Runtime validation

### HTTP e API

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **Axios** | 1.6+ | Cliente HTTP |
| **Axios Interceptors** | Built-in | Token refresh automático |

**Por que Axios?**
- Interceptors poderosos
- Cancelamento de requests
- Timeout configurável
- Transformação de dados

### Utils

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **date-fns** | 3.0+ | Manipulação de datas |
| **react-toastify** | 9.1+ | Notificações toast |
| **react-loading-skeleton** | 3.3+ | Loading states |
| **recharts** | 2.10+ | Gráficos e dashboards |

**Por que date-fns?**
- Modular (tree-shakeable)
- Imutável
- TypeScript nativo
- Locale support

---

## 🐳 Infraestrutura

### Containerização

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **Docker** | 24.0+ | Containerização |
| **Docker Compose** | 2.23+ | Orquestração multi-container |

**Por que Docker?**
- Ambiente consistente (dev = prod)
- Isolamento de dependências
- Deploy simplificado
- Escalabilidade horizontal

### Proxy e Load Balancer

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **Nginx** | 1.25+ | Proxy reverso e load balancer |

**Por que Nginx?**
- Performance extrema
- SSL/TLS termination
- Compressão gzip/brotli
- Rate limiting

### Ferramentas de Desenvolvimento

| Tecnologia | Versão | Justificativa |
|------------|--------|---------------|
| **pgAdmin** | 4.0+ | Interface gráfica para PostgreSQL |
| **RabbitMQ Management** | Built-in | Painel de administração |
| **Redis Commander** | 0.8+ | Interface gráfica para Redis |

---

## 🔌 Integrações Externas

### Pagamentos

| Serviço | Versão API | Justificativa |
|---------|------------|---------------|
| **Mercado Pago** | v1 | PIX automático, webhooks, sem mensalidade |

**Por que Mercado Pago?**
- Líder no Brasil
- PIX instantâneo
- Webhooks confiáveis
- Documentação completa
- Sem custo de setup

### Notificações

| Serviço | Versão | Justificativa |
|---------|--------|---------------|
| **Evolution API** | 2.0+ | WhatsApp self-hosted |

**Por que Evolution API?**
- Self-hosted (sem custos recorrentes)
- Multi-instância
- Webhooks
- API REST completa
- Open source

### Autenticação Social (Futuro)

| Serviço | Versão API | Justificativa |
|---------|------------|---------------|
| **Google OAuth2** | v2 | Login social |
| **Microsoft OAuth2** | v2 | Login social |

---

## 📊 Comparação de Alternativas

### Backend Framework

| Framework | Prós | Contras | Escolha |
|-----------|------|---------|---------|
| **FastAPI** | Performance, async, docs automáticas | Comunidade menor que Django | ✅ Escolhido |
| Django REST | Maduro, admin panel, ORM robusto | Síncrono, mais pesado | ❌ |
| Flask | Simples, flexível | Sem async nativo, sem validação | ❌ |

### Frontend Framework

| Framework | Prós | Contras | Escolha |
|-----------|------|---------|---------|
| **React** | Ecossistema, flexibilidade, jobs | Boilerplate | ✅ Escolhido |
| Vue.js | Simples, documentação | Ecossistema menor | ❌ |
| Angular | Completo, TypeScript nativo | Curva de aprendizado | ❌ |

### CSS Framework

| Framework | Prós | Contras | Escolha |
|-----------|------|---------|---------|
| **Tailwind** | Rápido, customizável, tree-shaking | Classes longas | ✅ Escolhido |
| Bootstrap | Componentes prontos, maduro | Pesado, menos flexível | ❌ |
| Material UI | Design system completo | Opinionado, bundle grande | ❌ |

---

## 🔄 Versionamento e Atualizações

### Política de Versões

- **Major**: Mudanças breaking (ex: Python 3.11 → 3.12)
- **Minor**: Novas features compatíveis (ex: FastAPI 0.104 → 0.105)
- **Patch**: Bug fixes (ex: 1.0.0 → 1.0.1)

### Frequência de Atualizações

- **Dependências de segurança**: Imediato
- **Dependências principais**: Trimestral
- **Dependências secundárias**: Semestral

### Testes Antes de Atualizar

1. Ler changelog da biblioteca
2. Atualizar em ambiente de desenvolvimento
3. Rodar suite de testes completa
4. Testar manualmente features críticas
5. Deploy em staging
6. Deploy em produção

---

## 📚 Recursos e Documentação

### Documentação Oficial

- **FastAPI**: https://fastapi.tiangolo.com/
- **React**: https://react.dev/
- **PostgreSQL**: https://www.postgresql.org/docs/
- **Docker**: https://docs.docker.com/
- **Tailwind CSS**: https://tailwindcss.com/docs

### Comunidades

- **FastAPI Discord**: https://discord.gg/fastapi
- **React Discord**: https://discord.gg/react
- **PostgreSQL Slack**: https://postgres-slack.herokuapp.com/

---

**Projeto:** Runas  
**Equipe:** Equipe DenebCorp  
**Data:** 26 de Maio de 2026  
**Versão:** 1.0.0
