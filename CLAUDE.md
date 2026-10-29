# CLAUDE.md

Guia do Claude Code (claude.ai/code) para este repositório.

# RunasERP — Convenções de desenvolvimento

> **Idioma:** converse, comente e escreva commits em **português (pt-BR)**. Identificadores já existentes no código, texto de UI e o prefixo do Conventional Commits (`feat(auth): ...`) ficam como estão.

---

## Arquitetura

Um único PostgreSQL, um schema por microsserviço:

| Serviço | Schema | Porta |
|---------|--------|-------|
| api-gateway | `gateway` | 8000 |
| clientes | `clientes` | 8001 |
| produtos | `produtos` | 8002 |
| estoque | `estoque` | 8003 |
| vendas | `vendas` | 8004 |
| financeiro | `financeiro` | 8005 |
| notificacoes | `notificacoes` | 8006 |
| empresas | `empresas` | 8007 |

Portas do `docker-compose.dev.yml`. Entre os containers da aplicação só o gateway (`8000:8000`) e o frontend (`3000:3000`) publicam em todas as interfaces; **8001–8007 ficam presas a `127.0.0.1` de propósito**: nenhum serviço valida JWT, todos confiam em `X-Empresa-Id`, e o 8007 ainda aceita `X-Plataforma`. A defesa em profundidade é o `X-Servico-Interno-Token` (abaixo), mas não dependa dela para expor porta. Os containers de infra desse arquivo não são presos ao loopback: Postgres `5432`, Redis `6379`, RabbitMQ `5672`/`15672` e evolution-api `8080` publicam em todas as interfaces.

Cada serviço é dono só do seu schema; não consulte o schema de outro. Exceções conhecidas, que não devem crescer (card 74): o gateway lê `empresas.empresas` em `api-gateway/proxy/service_proxy.py` e o `produtos` em `services/produtos/routers/produtos.py`.

**Visão geral:** backend FastAPI (Python 3.12) + frontend React 19 / TypeScript / Vite (porta 3000), com Postgres e Redis (cache). Há um RabbitMQ no compose de dev e cada serviço tem `events/publisher.py`, mas **nada o importa: hoje não existe tráfego de eventos**. O **API Gateway (8000) é a única entrada**: cuida de OAuth2/JWT + RBAC e faz proxy de `/api/<serviço>/...` para o serviço. Dois fatos transversais que nenhum arquivo isolado mostra:

- **Multi-tenancy por header injetado.** `api-gateway/proxy/service_proxy.py` injeta `X-Empresa-Id` (e `X-Cliente-Id` no login da loja) em toda requisição proxied, a partir do principal autenticado. Os serviços **exigem** esses headers e **falham fechado** sem eles: chamar a porta do serviço direto, sem `X-Empresa-Id`, é recusado (400 em `produtos`, ver `utils/tenant.py`). Com o header na mão escolhe-se qualquer tenant, por isso as portas ficam no loopback. Todo serviço também roda `validar_token_interno` (`services/*/interno.py`, header `X-Servico-Interno-Token`), **fail-closed**: sem token configurado ou sem o header, a resposta é 403 (só `/health` é isento). Teste de integração passa pelo gateway, nunca pela porta do serviço.
- **Cada serviço tem o próprio histórico Alembic**, no schema dele (`version_table_schema = "<schema>"`); ver Database Migrations.

Ordem das camadas (FastAPI): `router → service → repository → model`

```
router      valida a entrada (Pydantic), chama o service, devolve a resposta
service     regra de negócio, orquestra repositories, levanta exceções de domínio
repository  só consultas ao banco, sem regra de negócio
schema      modelos Pydantic de E/S, nunca exponha o model ORM direto
model       SQLAlchemy ORM, com __table_args__ = {"schema": "<nome>"}
```

---

## Build, execução e testes

```bash
# Stack completa (dev). Para a variante com túnel Cloudflare e logs, ver Infraestrutura.
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml ps
docker compose -f docker-compose.dev.yml down [-v]

# Frontend (rode em frontend/)
npm run dev          # servidor Vite
npm run build        # tsc && vite build
npm run lint         # eslint --report-unused-disable-directives --max-warnings 115
npm run test         # vitest  (também test:coverage, test:watch)
npm run format       # prettier
```

O CI (só em PR para `Developer`, escopado pelo diff) roda **duas pernas de teste de backend** (`.github/workflows/ci.yml`), e elas têm ambientes opostos. Antes de escrever ou rodar teste, leia `.claude/rules/testes-backend.md` (carrega sozinho ao abrir arquivo de teste). Nunca rode `pytest` puro na raiz.

Login padrão: `admin@runas.com` / `Admin@123`. Seed: `produtos` exige a ordem `exec produtos python seed_categorias.py` → `exec produtos python seed_produtos.py` (29 EANs válidos), depois `exec estoque python seed.py`; **não rode `produtos/seed.py`**: cria 3 produtos sem EAN e bloqueia os dois seeds acima (só limpa dropando o schema). Outros serviços: `exec <serviço> python seed.py`.

---

## Database Migrations

**Sempre Alembic. Nunca `Base.metadata.create_all()` em produção.**

**Uma revision ruim é crashloop, não degradação.** Os 8 apps rodam `alembic upgrade head` como subprocesso no `lifespan` (`init_db()` em `<app>/database.py`, ex.: `api-gateway/database.py:47-66` chamado em `api-gateway/main.py:45`) antes de servir qualquer requisição. Se falhar, o container reinicia e cai de novo. Produção está carimbada num baseline, então revisions antigas não rodam de novo, mas uma **nova** roda no próximo boot, sobre dados de produção, sem ninguém olhando. **Rollback de deploy volta imagem, nunca DDL** (tag `producao` ou dispatch `tag=<sha>`): migration que a imagem anterior não lê é porta sem volta, então escreva-a compatível com a versão anterior ou planeje a descida antes do merge.

Todo model declara o schema (`__table_args__ = {"schema": "<nome>"}`); `alembic/env.py` usa `include_schemas=False` e `version_table_schema="<schema>"`. **Nunca:** `include_schemas=True`, model sem `__table_args__`, migration sem revisão, editar migration já aplicada. Comandos e erros comuns: `.claude/rules/migrations.md` (carrega sozinho ao abrir `alembic/`).

---

## Git

Conventional Commits em pt-BR: `<tipo>(<escopo>): <descrição curta>` (até 72 caracteres, imperativo, sem ponto). Tipos: `feat` `fix` `refactor` `docs` `test` `chore` `perf` `ci`. Exemplo: `fix(estoque): impede estoque negativo em venda concorrente`.

**Não commite sem pedido explícito**; sem pedido, sugira a mensagem e deixe o desenvolvedor rodar. Worktrees ficam dentro do projeto, em `.claude/worktrees/<nome>` (`git worktree add .claude/worktrees/<nome> -b <branch> origin/Developer`), nunca como pasta irmã. Git é a fonte da verdade: sem changelog manual e sem documento temporário ou arquivado (`_TEMP.md`, `_WIP.md`, `BUGFIX_*.md`, `RESUMO_*.md`, `AUDITORIA_*.md`): se não está num commit, não existe.

---

## Padrões de engenharia

Fluxo padrão: **entender → implementar → verificar → sugerir a mensagem de commit.** Não proponha várias opções quando a boa prática é óbvia. Não crie classes base abstratas sem implementação concreta, try/catch genérico "por garantia" nem script que embrulha um único comando docker.

### Clean Code e SOLID

São princípios de orientação: valem para **código novo** e para o trecho legado que você está alterando; não reescreva legado só para cumpri-los.

- **Clean Code:** nomes descritivos (nada de `x`, `tmp`, `cli`); uma função, uma responsabilidade; funções pequenas (alvo: corpo abaixo de 15 linhas; em 22/10/2026, 29% das funções do legado passavam disso); sem número mágico, use constante nomeada; sem efeito colateral escondido; DRY, extraia a lógica repetida; sem código morto nem bloco comentado (`shared/` na raiz ainda é código morto, ver Infraestrutura).
- **Calisthenics (só o que o código já segue):** no máximo 2 níveis de indentação por método (medido em 23/10/2026: 56 de 836 funções passam disso) e sem `else`, use guard clause ou retorno antecipado (24 de 836 têm `else`). Value objects `CPF`/`Email`/`Dinheiro`, máximo de 2 variáveis por classe e a regra de um ponto por linha não valem aqui: o código não os segue e modelos ORM/Pydantic têm 3 campos ou mais por natureza.
- **SOLID:** **S** uma responsabilidade por classe/módulo · **O** aberto para extensão, fechado para modificação · **L** subclasse substituível pela base · **I** interfaces específicas em vez de gerais · **D** dependa de abstrações, não de implementações.

### Tratamento de erro

O alvo abaixo vale para **código novo**; o legado ainda não segue (cards 69 a 72 no board):

- Capture exceção específica, não `except Exception` em service.
- Router sem try/except: os handlers globais de `main.py` são donos do tratamento de erro.
- Nunca exponha stack trace ao cliente; no 500, devolva um `request_id`.
- Log estruturado com `structlog`, com `request_id`, `usuario_id`, `empresa_id`, `action` e `duration_ms`.

**Não há biblioteca de exceções compartilhada.** `shared/` na raiz é código morto (zero imports; as Dockerfiles nem o copiam): não importe dele. As exceções vivem por serviço, e `services/empresas/exceptions.py` é o único modelo hoje (`BaseServiceError`, `ValidationError`, `NotFoundError`, `ConflictError`, `UnauthorizedError`, `ForbiddenError`; `main.py` registra handlers para `ValidationError`, `NotFoundError`, `ConflictError` e um catch-all `Exception`). Copie esse formato no serviço que precisar; não importe entre serviços, pois as imagens não levam o código umas das outras.

### Performance

- Sem N+1: `joinedload()` ou `selectinload()`.
- Paginação em todo endpoint de lista; índice em toda coluna de WHERE e JOIN.
- Redis para dado muito lido e pouco alterado.

### Testes

Teste unitário da camada de serviço em todo código novo, com `pytest` e fixtures de sessão de banco. Nomes de teste descrevem o comportamento em frase, em português (`test_cria_cliente_com_cpf_duplicado_retorna_409`). A cobertura não é medida no CI; medi-la é meta (card 72), não regra.

### Documentação

Escreva doc só para arquitetura complexa, integração externa (Mercado Pago, Google, Microsoft), setup não trivial, decisão de design explícita ou pedido explícito. Markdown conciso com exemplos práticos. Docstring em método público de service e repository; uma linha, salvo comportamento não óbvio. **Os docs citam muito `arquivo:linha`**: ao editar um arquivo citado, mantenha o número de linhas ou re-meça com `git grep -n -o -E "<arquivo>:[0-9]+" -- '*.md'`.

---

## Segurança — inegociável

**Nunca:**
- `localStorage` / `sessionStorage` para token (XSS)
- Token em query string (vai para log e histórico) — o fluxo de reset de senha ainda leva `?token=`; não copie o padrão
- Senha em texto puro (sem hash, sem log, sem GET)
- `Access-Control-Allow-Origin: *` em produção — **os 7 serviços ainda usam `*`** (card 73); só o gateway restringe (`allow_origins=[settings.FRONTEND_URL]`). Sustentam-se por estarem no loopback; não publique uma porta de serviço
- Regra de negócio ou segredo no código do frontend
- SQL por f-string — sempre ORM ou parâmetro

**Sempre:**
- Cookie HttpOnly para token (`httponly=True, secure=True, samesite="lax"`; o gateway usa `secure` conforme `is_https`, e o cookie do carrinho em `vendas/routers/loja.py` usa `samesite="none"` sob HTTPS)
- Bcrypt/Argon2 para senha
- CORS restritivo (origens explícitas)
- Validação no backend mesmo com validação no frontend
- Rate limit nos endpoints de auth (hoje em `api-gateway/routers/auth.py`: login 10/min, forgot-password 5/min, reset-password 10/min; padrão 300/min por IP)
- CSP, `X-Content-Type-Options`, `X-Frame-Options`

**Fluxo de auth:** (1) login → o backend gera o JWT e seta o cookie HttpOnly; (2) o navegador manda o cookie sozinho (`credentials: 'include'`); (3) `POST /auth/refresh` existe, mas o frontend não o chama: num 401 o interceptor do axios desloga; (4) logout limpa o cookie, grava o access token em `blacklist:{token}` até o `exp` e apaga o refresh (card 67).

---

## Infraestrutura

**Domínios:** app → `https://app.runaserp.com.br` (túnel) · painel da plataforma → `https://admin.runaserp.com.br` (túnel, mesmo container `frontend-prod`; rota do túnel e Cloudflare Access ficam fora do repo) · landing → `https://runaserp.com.br` + `www` (Cloudflare Pages, serve `landing-page/`, fora do túnel).

O bundle escolhe o app pelo hostname (`frontend/src/config/host.ts`: primeiro rótulo == `VITE_HOST_PLATAFORMA`, padrão `admin`). A divisão é só do frontend: em produção as rotas `/plataforma*` nem são registradas fora do host do painel, e `frontend/nginx.conf` responde 404 em `/plataforma` quando o host não começa com `admin.`; mas `/api/plataforma/*` responde nos dois hosts, protegido por `require_super_admin`. Em dev os dois apps convivem em `localhost`; `admin.localhost:3000` exercita o caminho de produção.

Um arquivo base por tipo de máquina, mais overlays para o único eixo que varia. Os compose se empilham: `-f base -f overlay`, e o overlay só repete as linhas que muda.

| Arquivo | Lido por | Uso |
|---------|----------|-----|
| `docker-compose.dev.yml` | sua máquina | dev local: build do código, hot reload. **Localhost é o padrão, sem overlay.** |
| `docker-compose.cloudflare.yml` | sua máquina | overlay do dev: URLs públicas + túnel. O único motivo para um segundo `-f`. |
| `docker-compose.prod.yml` | Coolify | runtime de produção. **Só pull, nenhum `build:`**: imagens vêm do ghcr. |
| `docker-compose.build.yml` | GitHub Actions | overlay do prod: devolve os `build:` para o CI construir e publicar. |

Imagens de produção: `${REGISTRY}/<serviço>:${TAG}` (padrões no compose: `ghcr.io/jonathanribeirosilva/runaserp`, `latest`). O `publish` empurra só `:<sha>`; o `deploy` promove `:latest` depois dos testes e roda o health check. Rollback: automático para a tag `producao` (para na migration) ou dispatch com `tag=<sha>`.

```powershell
# Teste de API — SEMPRE pelo túnel Cloudflare (cobre OAuth, CORS, HTTPS, webhooks)
Invoke-WebRequest -Uri "https://app.runaserp.com.br/api/health" -UseBasicParsing

# Nunca use curl no PowerShell (o alias vira Invoke-WebRequest e gasta token em erro).
# Nunca teste integração direto na porta do serviço (http://localhost:8001).

# Subir com o túnel Cloudflare
docker compose -f docker-compose.dev.yml -f docker-compose.cloudflare.yml --profile proxy up -d

# Logs
docker logs erp-api-gateway-dev -f
docker logs erp-cloudflared -f           # sem -dev: docker-compose.cloudflare.yml
docker logs erp-<serviço>-dev -f
```

**Banco:** `localhost:5432`, credenciais no `.env` (DBeaver ou qualquer cliente PostgreSQL).

**OAuth2 e webhook do Mercado Pago:** redirect URIs e configuração em `docs/02-desenvolvimento/OAUTH_PROVIDERS_CONFIG.md`; o webhook do MP é por empresa, enviado como `notification_url` em cada preferência, e não exige nada no painel do MP (`docs/06-operacao/CONFIGURACAO_MERCADO_PAGO.md`).

**Removido ou morto, não referencie:** Ngrok, o container Nginx de proxy reverso avulso (o frontend ainda serve o SPA com nginx: `frontend/nginx.conf`), o container PgAdmin (comentado em `docker-compose.dev.yml`), `docker-compose.nginx.yml`, `docker-compose.local.yml` (os valores de localhost são o padrão do dev) e `shared/` na raiz.
