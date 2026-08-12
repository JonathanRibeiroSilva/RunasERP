# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# RunasERP — Development Conventions

> **Language rule:** All Claude Code input and output must be in **English** — chat, tool calls, responses, comments, commit suggestions. This reduces token count and keeps context precise. Exception: user-facing UI text and PT-BR identifiers already in the codebase stay as-is.

---

## Architecture

Single PostgreSQL database, one schema per microservice:

| Service | Schema | Port |
|---------|--------|------|
| api-gateway | `gateway` | 8000 |
| empresas | `empresas` | — |
| clientes | `clientes` | 8001 |
| produtos | `produtos` | 8002 |
| estoque | `estoque` | 8003 |
| vendas | `vendas` | 8004 |
| financeiro | `financeiro` | 8005 |
| notificacoes | `notificacoes` | — |

Each service owns only its schema. Never query another service's schema directly.

**Big picture:** FastAPI (Python 3.12) backend + React 18 / TypeScript / Vite frontend (port 3000), plus Postgres (5432), Redis (cache), and RabbitMQ (events — see `shared/events`). The **API Gateway (8000) is the single entry point**: it owns OAuth2/JWT auth + RBAC, then reverse-proxies `/api/<service>/...` to the backing service. Two cross-cutting facts that aren't obvious from any single file:

- **Multi-tenancy by injected header.** `api-gateway/proxy/service_proxy.py` injects `X-Empresa-Id` (and `X-Cliente-Id` for storefront auth) into every proxied request from the authenticated principal. Services **trust and require** these headers and **fail closed** without them — calling a service directly on its own port (bypassing the gateway) will be rejected. Integration-test through the gateway, never service ports.
- **Each service has its own Alembic history** keyed to its schema (`version_table_schema = "<schema>"`); see Database Migrations.

Layer order (FastAPI): `router → service → repository → model`

---

## Code Layer Rules

```
router      validates input (Pydantic), calls service, returns response
service     business logic, orchestrates repositories, raises domain exceptions
repository  DB queries only — no business logic
schema      Pydantic I/O models — never expose ORM model directly
model       SQLAlchemy ORM — must have __table_args__ = {"schema": "<name>"}
```

---

## Build, Run & Test

```bash
# Run the full stack (dev). For the Cloudflare tunnel variant + logs, see Infrastructure below.
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml ps
docker-compose -f docker-compose.dev.yml down [-v]

# Backend tests (pytest, run from repo root; services must be up)
pip install -r tests/requirements.txt
pytest                                   # all
pytest tests/integration/                # one suite
pytest tests/integration/test_auth.py::TestAuth::test_login_admin_success -v   # single test
pytest --cov=api-gateway --cov=services --cov-report=html

# Frontend (run from frontend/)
npm run dev          # Vite dev server
npm run build        # tsc && vite build
npm run lint         # eslint (max-warnings 0)
npm run test         # vitest  (also test:coverage, test:watch)
npm run format       # prettier
```

Default login: `admin@runas.com` / `Admin@123`. Seed data: `docker-compose -f docker-compose.dev.yml exec <service> python seed.py`. DB migrations have their own section below.

---

## Database Migrations

**Always use Alembic. Never use `Base.metadata.create_all()` in production.**

```python
# Every SQLAlchemy model MUST declare its schema
class MyModel(Base):
    __tablename__ = "my_table"
    __table_args__ = {"schema": "service_name"}  # REQUIRED
```

`alembic/env.py` must have `include_schemas=False` and `version_table_schema="<service_schema>"`.

```bash
docker exec -it erp-<service>-dev alembic revision --autogenerate -m "description"
# Always review the generated file in alembic/versions/ before applying
docker exec -it erp-<service>-dev alembic upgrade head

# Useful inspection
docker exec -it erp-<service>-dev alembic current
docker exec -i erp-db-dev psql -U erp -d erp -c "SELECT version_num FROM <schema>.alembic_version;"
```

**Never:** `include_schemas=True`, missing `__table_args__`, unreviewed migrations, editing a migration after it has been applied.

### Migration Troubleshooting

| Error | Cause | Fix |
|-------|-------|-----|
| Detects tables from other schemas | `include_schemas=True` in env.py | Set to `False` |
| Table created in `public` instead of service schema | Missing `__table_args__` | Add it, create new migration |
| `type ENUM already exists` | Migration tries to create existing ENUM | Create empty migration (`pass`) and stamp it |
| Alembic detects phantom changes | Model/DB state mismatch | Apply pending migrations; last resort: `alembic stamp head` (careful) |

### Current Schema Status (2026-06-11)

| Service | Schema | Status |
|---------|--------|--------|
| api-gateway | `gateway` | ✅ Alembic |
| empresas | `empresas` | ✅ Alembic |
| clientes | `clientes` | ✅ Multi-tenancy |
| produtos | `produtos` | ✅ Multi-tenancy |
| estoque | `estoque` | ✅ UUIDs + multi-tenancy |
| vendas | `vendas` | ✅ Loja online MVP |
| financeiro | `financeiro` | ⚠️ Empty service |
| notificacoes | `notificacoes` | ⚠️ Empty service |

---

## Git Commits — Conventional Commits (English only)

```
<type>(<scope>): <short description>   ← max 72 chars, imperative, no period
```

| Type | Use |
|------|-----|
| `feat` | new feature |
| `fix` | bug fix |
| `refactor` | neither fix nor feature |
| `docs` | docs only |
| `test` | tests |
| `chore` | build, deps, tooling |
| `perf` | performance |
| `ci` | CI/CD |

```
feat(auth): add Google OAuth2 login
fix(estoque): prevent negative stock on concurrent sales
refactor(clientes): extract CPF validation to shared validator
chore(docker): consolidate postgres containers
```

---

## Engineering Standards

### Decision Ladder (Ponytail — apply before writing any code)
1. Does it need to exist? (YAGNI)
2. Already in the codebase? → reuse
3. Standard library covers it? → use it
4. Native platform feature? → use it
5. Existing dependency installed? → use it
6. Can it be one line? → one line
7. Only then: minimum working implementation

### Clean Code
- Descriptive names — no `x`, `tmp`, `cli`
- One function, one responsibility
- No magic numbers — use named constants
- No dead code, no commented-out blocks
- DRY — extract duplicated logic
- No hidden side effects

### SOLID
- **S** Single Responsibility per class/module
- **O** Open for extension, closed for modification
- **L** Subclasses substitutable for base
- **I** Specific interfaces over general ones
- **D** Depend on abstractions, not concretions

### Code Calisthenics (non-negotiable)
1. One level of indentation per method — extract nested blocks
2. No `else` — use early returns / guard clauses
3. Wrap primitives — `CPF`, `Email`, `Dinheiro` are value objects
4. First-class collections — encapsulate lists in domain classes
5. One dot per line — Law of Demeter (`order.get_country()` not `order.client.address.country.name`)
6. No abbreviations — `calculate_total_with_discount()` not `calc_tot_disc()`
7. Small entities — classes < 200 lines, methods < 15 lines
8. Max 2 instance variables per class
9. No public getters/setters — expose behavior, not data

### Error Handling
- Never bare `except Exception` in services — catch specific exceptions
- Use custom exceptions from `shared/exceptions.py` (`ValidationError`, `NotFoundError`, `ConflictError`)
- Routers must NOT have try/except — global handlers in `main.py` own that
- Never expose stack traces to the client — return `request_id` on 500
- Structured logs: `structlog` with `request_id`, `usuario_id`, `empresa_id`, `action`, `duration_ms`

### Performance
- No N+1 queries — use `joinedload()` or `selectinload()` in SQLAlchemy
- Pagination required on all list endpoints
- Indexes on every column used in WHERE and JOIN
- Redis for frequently-read, rarely-changed data

---

## Security — Non-Negotiable

### Never
- `localStorage` / `sessionStorage` for tokens → XSS vulnerable
- Tokens in query parameters → exposed in logs and history
- Passwords in plain text (no hash, no logging, no GET)
- `Access-Control-Allow-Origin: *` in production
- Business logic or secrets in frontend code
- `f"SELECT * FROM users WHERE id = {user_id}"` — always use ORM

### Always
- HttpOnly cookies for tokens (`httponly=True, secure=True, samesite="lax"`)
- Bcrypt/Argon2 for passwords
- Restrictive CORS (explicit origins only)
- Backend validation even when frontend validates
- Rate limiting on auth endpoints (5/min login, 10/min register)
- CSP, `X-Content-Type-Options`, `X-Frame-Options` headers

### Auth Pattern
1. Login → backend generates JWT → sets HttpOnly cookie
2. Requests → browser sends cookie automatically (`credentials: 'include'`)
3. Refresh → backend validates refresh token → updates cookie
4. Logout → invalidate token + clear cookie

---

## Infrastructure

**Domains:** app → `https://app.runaserp.com.br` (tunnel) · landing → `https://runaserp.com.br` + `www` (Cloudflare Pages, serves `landing-page/`, outside the tunnel)

| File | Use |
|------|-----|
| `docker-compose.dev.yml` | local dev |
| `docker-compose.prod.yml` | production |
| `docker-compose.cloudflare.yml` | Cloudflare tunnel |

```powershell
# API testing — ALWAYS via Cloudflare tunnel (tests OAuth, CORS, HTTPS, webhooks)
$domain = "https://app.runaserp.com.br"
Invoke-WebRequest -Uri "$domain/api/health" -UseBasicParsing

# NEVER use curl in PowerShell — the alias maps to Invoke-WebRequest differently and wastes tokens on error handling
# NEVER test direct to service ports (http://localhost:8001) for integration tests

# Start with Cloudflare tunnel
docker-compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d

# Logs
docker logs erp-api-gateway-dev -f
docker logs erp-cloudflared-dev -f
docker logs erp-<service>-dev -f
```

**OAuth2 redirect URIs** (Google Console / Azure):
```
https://app.runaserp.com.br/auth/callback
https://app.runaserp.com.br/auth/callback/google
https://app.runaserp.com.br/auth/callback/microsoft
```

**Mercado Pago webhook:** per-empresa, sent as `notification_url` on each preference — `{API_BASE_URL}/loja/{empresa_slug}/webhook/mercadopago`. Driven by `API_BASE_URL` in the compose file; nothing to configure in the MP dashboard.

**DB access:** `localhost:5432` with credentials from `.env` (use DBeaver or any PostgreSQL client).

Removed and dead — never reference: Ngrok, Nginx, PgAdmin container, `docker-compose.nginx.yml`.

---

## Graphify — Use Before Reading Files

Query the graph before reading files. The graph answers architectural questions in ~500 tokens instead of reading 10+ files.

```bash
graphify query "how does the sales module work?"
graphify path "VendaService" "EstoqueService"
graphify explain "VendaService"
```

**Decision:**
- Need architecture/structure overview → `graphify query`
- Need connections between components → `graphify path`
- Already know the exact file → read it directly (skip graphify)
- Trivial one-file change → read it directly

The graph auto-updates via GitHub Actions on push to `main`/`master`/`Developer` when `.py`, `.ts`, `.tsx`, `.js`, `.jsx` files change. No manual `graphify update` needed after a push.

---

## Token Efficiency

Do NOT create automatically unless explicitly requested:
- Markdown files summarizing changes already in commits
- Analysis documents before simple changes
- `_TEMP.md`, `_WIP.md`, `_DRAFT.md`, `BUGFIX_*.md`, `RESUMO_*.md`
- Abstract base classes with no concrete implementations
- Generic try/catch wrappers "just in case"
- Scripts that wrap a single docker command

Default flow: **understand → implement → verify → suggest commit message.** Never propose multiple options when best practice is obvious.

---

## Testing

- Unit tests for service layer on all new code
- Validators: 90%+ coverage
- Framework: `pytest` with DB session fixtures
- Naming: `test_create_client_with_duplicate_cpf_returns_409`
- Tests must be FIRST: Fast, Independent, Repeatable, Self-validating, Timely

---

## Documentation

Write docs only for: complex architecture, external integrations (Mercado Pago, Google, Microsoft), non-trivial setup, explicit design decisions, or when explicitly requested.

Format: concise markdown with practical examples. Docstrings on public service and repository methods are required; keep them one line unless the behavior is non-obvious.

**Never commit automatically.** Always suggest the commit message and let the developer run it.

---

## Git is the Source of Truth

- No manual changelogs — `git log` is authoritative
- No temp/archive docs — delete instead of archiving
- No `_TEMP.md`, `_WIP.md`, `BUGFIX_*.md`, `RESUMO_*.md`, `AUDITORIA_*.md`
- Zero Changelogs policy: if it's not in a commit, it doesn't exist
