# ✅ Checklist de Desenvolvimento - Runas ERP

> Guia completo para desenvolvimento de novas features no sistema

**Última atualização**: Setembro 2026

---

## 📋 Antes de Começar

### Ambiente de Desenvolvimento

- [ ] Docker e Docker Compose instalados
- [ ] Git configurado com Conventional Commits
- [ ] Editor configurado (VSCode recomendado)
- [ ] `.env` criado a partir do `.env.example`
- [ ] Containers rodando: `.\erp.ps1 up` (wrapper PowerShell na raiz; equivale a
      `docker compose -f docker-compose.dev.yml up -d`)

### Documentação Lida

- [ ] [O SISTEMA.md](../../O%20SISTEMA.md) - Visão geral
- [ ] [QUICK-START.md](../../QUICK-START.md) - Setup inicial
- [ ] [docs/README.md](../README.md) - Índice da documentação

---

## 🎯 Desenvolvimento Backend

### 1. Planejamento

- [ ] Feature mapeada no [roadmap](../01-visao-geral/roadmap.md)
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
├── events/          # Publishers/consumers RabbitMQ (existe nos 7 serviços)
├── utils/           # Helpers (validators, etc) — opcional
├── tests/           # Pytest tests
├── alembic/         # Database migrations
├── main.py          # FastAPI app
├── config.py        # Configurações
├── database.py      # Engine, Base, get_db
└── requirements.txt # Dependencies
```

`utils/` só existe onde há helper próprio: hoje em `clientes`, `empresas`,
`estoque`, `produtos` e `vendas` — `financeiro` e `notificacoes` não têm.
`events/`, `alembic/` e `tests/` existem nos sete.

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

- [ ] ESLint sem erros: `npm run lint` (o script já permite até 115 warnings: `--max-warnings 115`)
- [ ] Build sem erros: `npm run build` (o script é `tsc && vite build`, ou seja, o TypeScript já é checado aqui)
- [ ] Testes passando: `npm run test -- --run`
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

Não existe varredura manual: o repositório tem um hook de pre-commit.
`.git/hooks/pre-commit` é um shim de duas linhas que executa
`scripts/check-secrets.sh`, e é esse script que bloqueia o commit. Ele
analisa **as linhas adicionadas** do diff staged, não os arquivos inteiros.

```bash
# Roda sozinho em todo `git commit`. Para executar manualmente:
bash scripts/check-secrets.sh

# Para validar o próprio script depois de mexer num padrão:
bash scripts/test-check-secrets.sh
```

Os padrões cobertos e o comportamento do hook estão em
[SECURITY_HOOKS.md](SECURITY_HOOKS.md).

---

## 🧪 Testes

### Backend (pytest)

O `pytest` **não está** em `services/*/requirements.txt`. Ele, o `pytest-asyncio`
e o `pytest-cov` vêm de `tests/requirements.txt` (`pytest==9.1.1`,
`pytest-asyncio==1.4.0`, `pytest-cov==7.1.0`).

Os testes de serviço batem num Postgres de verdade: `tests/conftest.py` do serviço
não faz `create_all`, ele assume o schema que o `alembic upgrade head` construiu, e
usa `DATABASE_URL`/`REDIS_URL` apontando por padrão para o Postgres e o Redis do
`docker-compose.dev.yml` publicados no host. Ou seja: suba o dev antes.

```powershell
# Dependências de teste (uma vez)
pip install -r tests/requirements.txt

# Rodar os testes de um serviço — como a CI faz (.github/workflows/ci.yml, job `services`)
cd services/clientes
pytest tests -p no:cacheprovider

# Rodar com cobertura
pytest tests --cov=. --cov-report=html

# Rodar um teste específico
pytest tests/test_base.py::test_app_responde_health

# Suíte unitária compartilhada (roda na raiz, config própria)
pytest -c tests/pytest.ini tests/unit
```

### Frontend (Vitest)

O Vitest já roda: `vitest ^5.0.1` está em `frontend/package.json` (devDependencies),
a configuração está em `frontend/vitest.config.ts` e a CI executa
`npm run test -- --run` no job `frontend` de `.github/workflows/ci.yml`.

```powershell
cd frontend

# Modo watch (o script `test` é só `vitest`)
npm run test

# Uma passada só, como na CI
npm run test -- --run

# Com cobertura
npm run test:coverage
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

# 4. Abrir Pull Request no GitHub com base em Developer
gh pr create --base Developer
```

**A base do PR tem de ser `Developer`.** `.github/workflows/ci.yml` só dispara em
`pull_request: branches: [main, Developer]`; um PR empilhado sobre outra branch de
feature não casa com nenhum desses e o GitHub mostra "no checks reported" — que não
é "rodando", é "não vai rodar".

`Developer` é a branch de integração. O deploy só acontece no **merge de Developer
em main**: `.github/workflows/deploy.yml` tem `push: branches: [main]`.

---

## 🚀 Deploy

### Desenvolvimento

```powershell
# Subir só o que você precisa (o wrapper resolve as dependências)
.\erp.ps1 up vendas          # gateway + frontend + vendas + clientes/produtos/estoque/financeiro
.\erp.ps1 up clientes -NoFrontend

# Reiniciar, listar, ver saúde
.\erp.ps1 restart vendas
.\erp.ps1 ps
.\erp.ps1 health

# Ver logs
.\erp.ps1 logs vendas
docker logs erp-[servico]-dev -f

# Rodar migrations
docker compose -f docker-compose.dev.yml exec [servico] alembic upgrade head
```

### Produção

**Você não roda deploy de produção pela mão.** O fluxo é automático e tem dois donos:

1. **Merge em `main`** dispara `.github/workflows/deploy.yml`, que constrói as nove
   imagens e empurra para o ghcr.
2. Esse mesmo workflow chama a API do Coolify
   (`POST {COOLIFY_URL}/api/v1/deploy?uuid={COOLIFY_UUID}`). **O Coolify** é quem
   puxa as imagens e roda `docker compose -f docker-compose.prod.yml up -d --wait`
   na VPS.

`docker-compose.prod.yml` **não tem nenhuma seção `build:`, de propósito**: a VPS é
1 vCPU / 4 GB e não constrói nove imagens sem derrubar o que está no ar. As seções de
build vivem em `docker-compose.build.yml`, carregado só pela CI. Rodar
`docker compose -f docker-compose.prod.yml build` não constrói nada.

Para redeploy ou rollback sem inventar commit, use o `workflow_dispatch` do
`deploy.yml`: `tag` vazia reconstrói o commit atual; `tag` com um sha já presente no
ghcr pula o build e republica aquelas imagens como `:latest`.

Detalhes do fluxo e do que fazer quando ele quebra:
[deploy.md](../06-operacao/deploy.md) e
[runbook-producao.md](../06-operacao/runbook-producao.md).

---

## 📚 Recursos

### Documentação Interna
- [Arquitetura](../03-arquitetura/README.md)
- [APIs](../10-api-reference/README.md)
- [Regras de Negócio](../11-regras-negocio/)
- [Troubleshooting](../06-operacao/troubleshooting.md)

### Convenções
- [Docs Policy](../.docs-policy.md)

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

**Checklist Completo** | Setembro 2026  
**Sempre verifique antes de commitar!**

</div>
