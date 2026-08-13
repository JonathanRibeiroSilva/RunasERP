# ✅ Checklist de Desenvolvimento - Runas ERP

> Guia completo para desenvolvimento de novas features no sistema

**Última atualização**: Junho 2026

---

## 📋 Antes de Começar

### Ambiente de Desenvolvimento

- [ ] Docker e Docker Compose instalados
- [ ] Git configurado com Conventional Commits
- [ ] Editor configurado (VSCode recomendado)
- [ ] `.env` criado a partir do `.env.example`
- [ ] Containers rodando: `docker-compose -f docker-compose.dev.yml up -d`

### Documentação Lida

- [ ] [O SISTEMA.md](./O%20SISTEMA.md) - Visão geral
- [ ] [QUICK-START.md](./QUICK-START.md) - Setup inicial
- [ ] [.kiro/steering/git-conventions.md](./.kiro/steering/git-conventions.md) - Convenções Git
- [ ] [docs/README.md](./docs/README.md) - Índice da documentação

---

## 🎯 Desenvolvimento Backend

### 1. Planejamento

- [ ] Feature mapeada no [roadmap](./docs/01-visao-geral/roadmap.md)
- [ ] Regras de negócio documentadas em `docs/11-regras-negocio/`
- [ ] Endpoints definidos (método, path, request, response)
- [ ] Dependências entre serviços identificadas

### 2. Estrutura do Código

Cada serviço deve seguir esta estrutura:

```
services/[nome-servico]/
├── models/          # SQLAlchemy models
├── schemas/         # Pydantic schemas (request/response)
├── repositories/    # Database queries
├── services/        # Business logic
├── routers/         # FastAPI routers
├── utils/           # Helpers (validators, etc)
├── tests/           # Pytest tests
├── alembic/         # Database migrations
├── main.py          # FastAPI app
├── config.py        # Configurações
└── requirements.txt # Dependencies
```

### 3. Implementação

#### Models (SQLAlchemy)
- [ ] Model criado em `models/`
- [ ] Campos com tipos corretos
- [ ] Relacionamentos definidos
- [ ] Soft delete implementado (`ativo: bool`, `deletado_em: datetime`)
- [ ] `empresa_id` adicionado (multi-tenancy)
- [ ] Índices criados para queries frequentes

#### Schemas (Pydantic)
- [ ] Schema de request criado
- [ ] Schema de response criado
- [ ] Validações implementadas
- [ ] Documentação nos fields (`Field(description="...")`)

#### Repository
- [ ] CRUD completo implementado
- [ ] Queries otimizadas (eager loading quando necessário)
- [ ] Filtros por `empresa_id` (multi-tenancy)
- [ ] Soft delete respeitado (`ativo=True`)

#### Service
- [ ] Regras de negócio implementadas
- [ ] Validações customizadas
- [ ] Tratamento de erros com exceções personalizadas
- [ ] Logs estruturados (`structlog`)
- [ ] Transações de banco gerenciadas

#### Router
- [ ] Endpoints documentados (summary, description, tags)
- [ ] Autenticação configurada (`Depends(get_current_user)`)
- [ ] Permissões verificadas (RBAC)
- [ ] Status codes corretos (200, 201, 204, 400, 401, 403, 404, 500)
- [ ] Responses tipadas

#### Migration
- [ ] Migration criada: `alembic revision --autogenerate -m "descrição"`
- [ ] Migration revisada manualmente
- [ ] Migration testada: `alembic upgrade head`
- [ ] Migration com downgrade implementado

### 4. Testes

- [ ] Testes unitários de services criados
- [ ] Testes de repository criados
- [ ] Testes de endpoints criados (FastAPI TestClient)
- [ ] Cobertura > 80% para código crítico
- [ ] Todos os testes passando: `pytest`

### 5. Documentação

- [ ] Endpoint documentado em `docs/10-api-reference/`
- [ ] Regras de negócio atualizadas em `docs/11-regras-negocio/`
- [ ] README do serviço atualizado (se necessário)

---

## 🎨 Desenvolvimento Frontend

### 1. Planejamento

- [ ] Design/mockup aprovado (Figma, etc)
- [ ] Rotas definidas
- [ ] Estados do componente mapeados
- [ ] APIs backend necessárias prontas

### 2. Estrutura do Código

```
frontend/src/
├── pages/            # Páginas (rotas)
│   └── [Modulo]/
│       ├── ModuloPage.tsx
│       ├── ModuloFormPage.tsx
│       └── index.ts
├── components/
│   ├── common/       # Componentes reutilizáveis
│   └── layout/       # Layout (Navbar, Sidebar, etc)
├── services/         # Chamadas à API
│   └── api/
│       └── [modulo].ts
├── contexts/         # Context API (AuthContext, etc)
├── hooks/            # Custom hooks
├── types/            # TypeScript types
├── utils/            # Helpers
└── config/           # Configurações
```

### 3. Implementação

#### Página
- [ ] Componente criado em `pages/[Modulo]/`
- [ ] Rota adicionada em `App.tsx`
- [ ] Proteção de rota implementada (`RoleProtectedRoute`)
- [ ] Loading states implementados
- [ ] Error states implementados
- [ ] Empty states implementados

#### API Service
- [ ] Service criado em `services/api/`
- [ ] Tipos TypeScript definidos
- [ ] Funções CRUD implementadas
- [ ] Tratamento de erros
- [ ] Token JWT incluído nos headers

#### Componentes
- [ ] Componentes reutilizáveis em `components/common/`
- [ ] Props tipadas com TypeScript
- [ ] Responsivos (mobile, tablet, desktop)
- [ ] Acessíveis (ARIA labels, keyboard navigation)

#### Formulários
- [ ] Validação implementada
- [ ] Máscaras aplicadas (CPF, telefone, CEP, etc)
- [ ] Feedback visual (erros, sucesso)
- [ ] Toasts para confirmações

#### Tabelas
- [ ] Paginação implementada
- [ ] Ordenação implementada
- [ ] Filtros implementados
- [ ] Responsividade (mobile stack)

### 4. Qualidade

- [ ] TypeScript sem erros: `npm run type-check`
- [ ] ESLint sem warnings: `npm run lint`
- [ ] Build sem erros: `npm run build`
- [ ] Testado em Chrome, Firefox, Safari
- [ ] Testado em mobile, tablet, desktop

### 5. Documentação

- [ ] Componente documentado (JSDoc)
- [ ] README atualizado (se necessário)
- [ ] Guia de uso adicionado em `docs/05-frontend/`

---

## 🔒 Segurança

### Checklist de Segurança

- [ ] Inputs validados no backend
- [ ] SQL injection prevenida (SQLAlchemy ORM)
- [ ] XSS prevenida (React já escapa por padrão)
- [ ] CSRF prevenida (state token no OAuth)
- [ ] Secrets não commitados (`.gitignore` configurado)
- [ ] Logs não expõem dados sensíveis
- [ ] Senhas hasheadas (bcrypt)
- [ ] Rate limiting implementado
- [ ] CORS configurado corretamente

### Verificação de Secrets

```powershell
# Antes de commitar
Select-String -Path . -Pattern "(password|secret|token|key).*=.*['\"][^'\"]{8,}" -Recurse -Exclude "*.md"
```

---

## 🧪 Testes

### Backend (pytest)

```powershell
# Rodar todos os testes
cd services/[servico]
pytest

# Rodar com cobertura
pytest --cov=. --cov-report=html

# Rodar testes específicos
pytest tests/test_service.py::test_criar_cliente
```

### Frontend (Vitest - planejado)

```powershell
cd frontend
npm run test
```

### Testes Manuais

- [ ] Fluxo completo testado (create → read → update → delete)
- [ ] Casos de erro testados (404, 400, 401, 403, 500)
- [ ] Performance testada (queries lentas?)
- [ ] Multi-tenancy testado (dados isolados por empresa?)

---

## 📦 Commit e Deploy

### Antes de Commitar

- [ ] Código formatado
- [ ] Imports organizados
- [ ] Console.logs removidos
- [ ] Comentários desnecessários removidos
- [ ] Testes passando
- [ ] Build sem erros

### Commit (Conventional Commits)

```bash
# Formato
<type>(<scope>): <description>

# Exemplos
feat(clientes): add cliente credit limit management
fix(vendas): resolve race condition in stock update
docs(api): update authentication endpoints
refactor(produtos): extract validation to shared validator
chore(docker): update postgres to version 16
```

**Types**: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`, `test`, `chore`, `ci`, `revert`

### Git Workflow

```bash
# 1. Criar branch
git checkout -b feat/nova-feature

# 2. Desenvolver e commitar
git add .
git commit -m "feat(modulo): descrição"

# 3. Push
git push origin feat/nova-feature

# 4. Abrir Pull Request no GitHub
```

---

## 🚀 Deploy

### Desenvolvimento

```powershell
# Reiniciar serviço específico
docker-compose -f docker-compose.dev.yml restart [servico]

# Ver logs
docker logs erp-[servico]-dev -f

# Rodar migrations
docker-compose -f docker-compose.dev.yml exec [servico] alembic upgrade head
```

### Produção

```powershell
# Build
docker-compose -f docker-compose.prod.yml build

# Deploy
docker-compose -f docker-compose.prod.yml up -d

# Verificar
docker-compose -f docker-compose.prod.yml ps
```

---

## 📚 Recursos

### Documentação Interna
- [Arquitetura](./docs/03-arquitetura/README.md)
- [APIs](./docs/10-api-reference/README.md)
- [Regras de Negócio](./docs/11-regras-negocio/)
- [Troubleshooting](./docs/09-troubleshooting/)

### Convenções
- [Git Conventions](./.kiro/steering/git-conventions.md)
- [Infrastructure Reference](./.kiro/steering/infrastructure-reference.md)
- [Docs Policy](./docs/.docs-policy.md)

### Ferramentas
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [SQLAlchemy Docs](https://docs.sqlalchemy.org/)
- [React Docs](https://react.dev/)
- [TypeScript Docs](https://www.typescriptlang.org/docs/)

---

## ✅ Checklist Rápido (TL;DR)

### Backend
- [ ] Model → Schema → Repository → Service → Router
- [ ] Migration criada e aplicada
- [ ] Testes escritos e passando
- [ ] Documentação atualizada
- [ ] Commit com Conventional Commits

### Frontend
- [ ] Page → Service → Components
- [ ] Tipos TypeScript definidos
- [ ] Responsivo e acessível
- [ ] Build sem erros
- [ ] Commit com Conventional Commits

### Segurança
- [ ] Validação no backend
- [ ] Secrets não commitados
- [ ] RBAC implementado
- [ ] Multi-tenancy respeitado

### Deploy
- [ ] Testado em dev
- [ ] PR aberto e revisado
- [ ] Merge e deploy em prod

---

<div align="center">

**Checklist Completo** | Junho 2026  
**Sempre verifique antes de commitar!**

</div>
