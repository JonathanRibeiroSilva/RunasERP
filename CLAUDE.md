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
| clientes | `clientes` | 8001 |
| produtos | `produtos` | 8002 |
| estoque | `estoque` | 8003 |
| vendas | `vendas` | 8004 |
| financeiro | `financeiro` | 8005 |
| notificacoes | `notificacoes` | 8006 |
| empresas | `empresas` | 8007 |

Ports are from `docker-compose.dev.yml`. Among the app containers only the gateway (`8000:8000`) and the
frontend (`3000:3000`) publish on all interfaces; **8001–8007 are bound to
`127.0.0.1` on purpose** — no service validates a JWT, they all trust
`X-Empresa-Id`, so a service published on the LAN is any tenant for anyone on
the network (and 8007 additionally accepts `X-Plataforma`). The infra containers in
that same file are not loopback-bound: Postgres `5432`, Redis `6379`, RabbitMQ
`5672`/`15672` and evolution-api `8080` publish on all interfaces.

Each service owns only its schema. Never query another service's schema directly.

**Big picture:** FastAPI (Python 3.12) backend + React 19 / TypeScript / Vite frontend (port 3000), plus Postgres (5432) and Redis (cache). A RabbitMQ container runs in the dev compose and each service carries an `events/publisher.py`, but **nothing imports it — there is no event traffic today**. The **API Gateway (8000) is the single entry point**: it owns OAuth2/JWT auth + RBAC, then reverse-proxies `/api/<service>/...` to the backing service. Two cross-cutting facts that aren't obvious from any single file:

- **Multi-tenancy by injected header.** `api-gateway/proxy/service_proxy.py` injects `X-Empresa-Id` (and `X-Cliente-Id` for storefront auth) into every proxied request from the authenticated principal. Services **trust and require** these headers and **fail closed** without them — calling a service directly on its own port (bypassing the gateway) without `X-Empresa-Id` is rejected (400 in `produtos`, e.g. `utils/tenant.py`). Setting the header by hand is enough to pick any tenant, which is why the ports are loopback-bound. Each service also runs `validar_token_interno` (`services/*/interno.py`, header `X-Servico-Interno-Token`), but it is **fail-open** while `SERVICO_INTERNO_TOKEN` is unset or absent from the request. Integration-test through the gateway, never service ports.
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
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml ps
docker compose -f docker-compose.dev.yml down [-v]

# Backend tests — the CI runs exactly two legs (.github/workflows/ci.yml).
# Run those two; anything else is not what the gate checks.

# Leg 1 — unit suite, from the repo root. No services need to be up.
pip install -r tests/requirements.txt
pytest -c tests/pytest.ini tests/unit
pytest -c tests/pytest.ini tests/unit/test_tenant_guards.py -v   # single file

# Leg 2 — per service, from the service's own directory (CI runs a matrix of 8:
# api-gateway + the 7 services). Each service imports flat (`from main import app`),
# so two services in one pytest process fight over sys.path.
cd services/<name>            # or cd api-gateway
# Path to tests/requirements.txt is relative to where you are: ../../tests from
# services/<name>, ../tests from api-gateway. CI sidesteps it with
# $GITHUB_WORKSPACE/tests/requirements.txt (.github/workflows/ci.yml:167).
pip install -r requirements.txt -r ../../tests/requirements.txt
pytest tests

# NEVER run a bare `pytest` from the repo root: tests/pytest.ini has
# `testpaths = tests`, and the files sitting directly under tests/ are manual
# scripts, not part of the gate: test_produtos_api.py calls a live
# localhost:8002 (fails with nothing up); test_produtos_local.py and
# test_estrutura_simples.py run module-level code against services/produtos
# (imports its models, `sys.exit(1)` on failure), so collection breaks.

# Frontend (run from frontend/)
npm run dev          # Vite dev server
npm run build        # tsc && vite build
npm run lint         # eslint --report-unused-disable-directives --max-warnings 115
npm run test         # vitest  (also test:coverage, test:watch)
npm run format       # prettier
```

Default login: `admin@runas.com` / `Admin@123`. Seed data: `docker compose -f docker-compose.dev.yml exec <service> python seed.py`. DB migrations have their own section below.

### The two legs have opposite capabilities — read this before writing a test

They are not the same environment, and a test written for one usually breaks on
the other:

| | Leg 1 — `tests/unit` | Leg 2 — `<service>/tests` |
|---|---|---|
| pytest config | `tests/pytest.ini`, `asyncio_mode = auto` | **none** — no `pytest.ini`, no `pyproject.toml`, no `setup.cfg` in any service |
| async tests | plain `async def` works | strict mode: needs explicit `@pytest.mark.asyncio` |
| fastapi / sqlalchemy | **absent** — `tests/requirements.txt` has neither | present, from the service's own `requirements.txt` |

Consequences:

- A file under `tests/unit` that imports a service's `main.py` (or anything
  pulling in FastAPI/SQLAlchemy) **breaks collection for the whole leg**, not
  just itself. Unit tests there read source, parse compose/YAML and assert on
  structure — they do not import the apps.
- A file under `<service>/tests` with a bare `async def test_...` is **not run**
  by strict mode — it needs `@pytest.mark.asyncio`. Every existing async test in
  those directories carries the marker; copy that, do not rely on auto mode.

---

## Database Migrations

**Always use Alembic. Never use `Base.metadata.create_all()` in production.**

### A bad revision is a crashloop, not a degradation — read first

Every one of the 8 apps runs `alembic upgrade head` **as a subprocess inside its
own lifespan startup**, before it serves a single request (`init_db()` in
`<app>/database.py`, awaited from `lifespan` in `<app>/main.py` — e.g.
`api-gateway/database.py:47-66` called at `api-gateway/main.py:45`). The failure
is deliberate and fatal: `subprocess.run(..., check=True)` raises, startup dies,
the container restarts, and it dies again. There is no "the app comes up with a
stale schema" middle ground, by design — serving on the wrong schema is
considered worse than being down.

What that means in practice:

- A migration that fails on production data (a constraint the existing rows
  violate, a rename against a column that is not there) takes the service
  **fully offline in a restart loop**, not partially.
- Production is stamped at a baseline, so old revisions do not replay — but a
  **new** revision runs on the next boot, on production data, unattended.
- **A deploy rollback reverts images, never DDL.** `TAG=<sha>` puts the old code
  back next to the already-migrated schema. Any migration that the previous
  image cannot read is a one-way door; write it backward-compatible or plan the
  down path before merging.
- `init_db()` also refuses to start when `alembic/versions/` is empty, so an
  image built without its migrations fails loudly instead of booting healthy on
  an empty schema.

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

### Current Schema Status (snapshot of 2026-06-11; all 8 apps run Alembic at boot, see above)

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
- **There is no shared exception library.** `shared/` at the repo root is dead code — zero imports anywhere. Exceptions live per service: `services/empresas/exceptions.py` is the only one that exists today (`BaseServiceError`, `ValidationError`, `NotFoundError`, `ConflictError`, `UnauthorizedError`, `ForbiddenError`), of which `main.py` registers `@app.exception_handler(...)` for `ValidationError`, `NotFoundError`, `ConflictError` and a catch-all `Exception` (`UnauthorizedError`/`ForbiddenError` have no handler). Copy that shape into a service that needs it — do not import across service boundaries, the images do not ship each other's code.
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
- Rate limiting on auth endpoints (today in `api-gateway/routers/auth.py`: login 10/min, forgot-password 5/min, reset-password 10/min; default 300/min per IP)
- CSP, `X-Content-Type-Options`, `X-Frame-Options` headers

### Auth Pattern
1. Login → backend generates JWT → sets HttpOnly cookie
2. Requests → browser sends cookie automatically (`credentials: 'include'`)
3. Refresh → backend validates refresh token → updates cookie (`POST /auth/refresh` exists, but the frontend never calls it: on 401 the axios interceptor logs the user out)
4. Logout → invalidate token + clear cookie

---

## Infrastructure

**Domains:** app → `https://app.runaserp.com.br` (tunnel) · platform panel → `https://admin.runaserp.com.br` (tunnel, same `frontend-prod` container; tunnel route and Cloudflare Access configured outside the repo, per a 2026-09-28 check) · landing → `https://runaserp.com.br` + `www` (Cloudflare Pages, serves `landing-page/`, outside the tunnel)

The bundle picks the app from the hostname (`frontend/src/config/host.ts`: first label == `VITE_HOST_PLATAFORMA`, default `admin`). The split is frontend-only: in production the `/plataforma*` routes are not even registered outside the panel host, and `frontend/nginx.conf` answers 404 on `/plataforma` when the host does not start with `admin.`; but `/api/plataforma/*` answers on both hosts, guarded by `require_super_admin`. In dev both apps coexist on `localhost`; `admin.localhost:3000` exercises the production path.

One base file per kind of machine, plus overlays for the one axis that varies.
Compose files stack: `-f base -f overlay`, where the overlay only restates the
lines it changes.

| File | Read by | Use |
|------|---------|-----|
| `docker-compose.dev.yml` | your machine | local dev — builds from source, hot reload. **Localhost is the default, no overlay needed.** |
| `docker-compose.cloudflare.yml` | your machine | overlay on dev: public URLs + tunnel. The only reason to add a second `-f`. |
| `docker-compose.prod.yml` | Coolify | production runtime. **Pull only — no `build:` anywhere**, images come from ghcr. |
| `docker-compose.build.yml` | GitHub Actions | overlay on prod: adds the `build:` sections back so CI can build and push. |

Production images are `${REGISTRY}/<service>:${TAG}` (defaults in the compose:
`ghcr.io/jonathanribeirosilva/runaserp`, `latest`). CI publishes every image
twice, as `:<sha>` and `:latest`; a rollback is `TAG=<sha>` on the VPS.

```powershell
# API testing — ALWAYS via Cloudflare tunnel (tests OAuth, CORS, HTTPS, webhooks)
$domain = "https://app.runaserp.com.br"
Invoke-WebRequest -Uri "$domain/api/health" -UseBasicParsing

# NEVER use curl in PowerShell — the alias maps to Invoke-WebRequest differently and wastes tokens on error handling
# NEVER test direct to service ports (http://localhost:8001) for integration tests

# Start with Cloudflare tunnel
docker compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d

# Logs
docker logs erp-api-gateway-dev -f
docker logs erp-cloudflared -f           # no -dev: docker-compose.cloudflare.yml:34
docker logs erp-<service>-dev -f
```

**OAuth2 redirect URIs** (Google Console / Azure):
```
https://app.runaserp.com.br/auth/callback
https://app.runaserp.com.br/auth/callback/google
https://app.runaserp.com.br/auth/callback/microsoft
```
Only `/auth/callback/google` and `/auth/callback/microsoft` have routes in `frontend/src/App.tsx`; the bare `/auth/callback` is just the `VITE_OAUTH_REDIRECT_URI` default in `frontend/src/config/env.ts`. A CONFIRMAR: whether the consoles actually have all three registered.

**Mercado Pago webhook:** per-empresa, sent as `notification_url` on each preference — `{API_BASE_URL}/loja/{empresa_slug}/webhook/mercadopago`. Driven by `API_BASE_URL` in the compose file; nothing to configure in the MP dashboard.

**DB access:** `localhost:5432` with credentials from `.env` (use DBeaver or any PostgreSQL client).

Removed and dead — never reference: Ngrok, the standalone Nginx reverse-proxy container (the frontend image still serves the SPA with nginx: `frontend/nginx.conf`, `docker-compose.prod.yml`), PgAdmin container,
`docker-compose.nginx.yml`, `docker-compose.local.yml` (its localhost values are
the defaults in `docker-compose.dev.yml` now), and `shared/` at the repo root
(`shared/exceptions.py`, `shared/pagination.py`, `shared/events/` — zero imports
in the whole codebase; the service Dockerfiles do not even copy it).

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

The graph auto-updates via GitHub Actions on push to **`main` only** when `.py`, `.ts`, `.tsx`, `.js`, `.jsx` or `.vue` files change (`.github/workflows/graphify-update.yml:10-18`). It deliberately does **not** run on `Developer` — the bot commits the regenerated `graphify-out/` on whichever branch it runs, and running on both made every merge conflict in the generated files. So after a push to `Developer` the graph is stale; refresh locally with `graphify update` if you need it.

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
