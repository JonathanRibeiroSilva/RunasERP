# Backend - Runas ERP

## Visão Geral

O backend é um api-gateway mais 7 microsserviços FastAPI, todos em Python 3.12
(`FROM python:3.12-slim` nos 8 Dockerfiles). O gateway é a única porta de entrada:
ele autentica, aplica rate limit e encaminha para o serviço de destino.

---

## Serviços e portas

Portas lidas do `CMD` de cada Dockerfile — as mesmas que o CI usa nas variáveis
`*_URL` (`.github/workflows/ci.yml`).

| Serviço | Porta | Rotas próprias (`routers/`) |
|---|---|---|
| api-gateway | 8000 | `auth.py`, `auth_cliente.py`, `auth_admin.py`, `plataforma.py`, `proxy.py` |
| clientes | 8001 | `clientes.py`, `enderecos.py` |
| produtos | 8002 | `produtos.py` |
| estoque | 8003 | `estoque.py` |
| vendas | 8004 | `vendas.py`, `loja.py`, `webhook.py`, `admin_pagamento.py`, `admin_entrega.py`, `admin_integracao.py` |
| financeiro | 8005 | **nenhuma** |
| notificações | 8006 | **nenhuma** |
| empresas | 8007 | `empresas.py` |

### financeiro e notificações são cascas

Não procure código de negócio nesses dois: ele não existe.
`services/financeiro/main.py` e `services/notificacoes/main.py` registram
**apenas** `GET /health`, o middleware `validar_token_interno` e o handler global
de exceções. `routers/`, `models/`, `schemas/`, `repositories/` e `services/`
contêm só a docstring do pacote — arquivos `__init__.py` de 19 a 37 bytes, sem
nenhuma outra definição.

O que existe de fato nos dois: `config.py`, `database.py`, `interno.py`,
`events/publisher.py`, `seed.py`, uma revision baseline em
`alembic/versions/20260919_baseline.py` e `tests/test_base.py`.

Ou seja: contas a receber, cobranças, envio de WhatsApp e histórico de
notificações **não estão implementados no backend**. Pagamento (Mercado Pago) e
integração com a Evolution API vivem hoje em `services/vendas/`.

---

## Multi-tenancy e autenticação — quem valida o quê

Este é o ponto mais fácil de entender errado.

**Nenhum dos 7 serviços valida JWT.** Só o api-gateway decodifica token:
`api-gateway/auth/jwt.py` (`decode_token` / `verify_token`, python-jose, HS256) e
`api-gateway/auth/oauth2.py`. `python-jose` aparece apenas em
`api-gateway/requirements.txt` e em `services/vendas/requirements.txt` — e em
vendas ele é usado para **emitir** um token de cliente no checkout
(`services/vendas/services/loja_service.py`, `jwt.encode`), nunca para validar um.

O fluxo real:

1. O gateway valida o JWT e resolve o usuário/cliente.
2. `api-gateway/proxy/service_proxy.py` injeta `X-Empresa-Id` (e `X-Cliente-Id`
   quando o portador é um cliente autenticado) no request encaminhado.
3. O serviço **confia** nesse header. `services/produtos/utils/tenant.py` — e os
   gêmeos em `clientes`, `estoque` e `vendas` — só verifica presença e valor:
   sem o header, `400 Header X-Empresa-Id é obrigatório`; valor `<= 0`, `400`.
   Não há assinatura, nem claim, nem conferência contra o banco.

A prova de que a chamada veio de dentro é um segredo estático compartilhado no
header `X-Servico-Interno-Token`, validado por `interno.py` em cada serviço, com
`/health` isento — o healthcheck do Docker bate direto em `localhost:PORTA/health`.
Esse token responde "veio de dentro" e nada mais: não diz qual serviço chamou nem
expira.

### Autenticação (só no gateway)

- OAuth2 com JWT HS256, `ACCESS_TOKEN_EXPIRE_MINUTES = 30` e
  `REFRESH_TOKEN_EXPIRE_DAYS = 7` (`api-gateway/config.py`).
- Refresh token guardado no Redis (`refresh:<usuario_id>`); revogação por
  blacklist no Redis (`blacklist:<token>`), consultada em `auth/oauth2.py`.
- Roles: `SUPER_ADMIN`, `ADMIN`, `OPERADOR` (`api-gateway/models/usuario.py`),
  aplicadas por dependências — `require_admin`, `require_super_admin`,
  `require_admin_or_operador`.

### Rate limiting

slowapi no gateway, teto global de **300/minute por IP**
(`api-gateway/middleware/rate_limit.py`). Login, registro e reset de senha usam
limites bem mais apertados via `@limiter.limit` direto na rota
(`routers/auth.py`, `routers/auth_cliente.py`). `/health` é isento.

---

## `shared/` não é uma biblioteca compartilhada

O diretório `shared/` existe no repositório (`exceptions.py`, `pagination.py`,
`events/base.py`), mas **nenhum arquivo Python do projeto o importa** — zero
ocorrências de `from shared` ou `import shared` fora de `.claude/worktrees/`. Ele
também não entra em nenhuma imagem: os Dockerfiles dos 8 serviços não o copiam e
o compose não o monta. Trate-o como código morto, não como dependência comum.

---

## Stack (versões lidas de `requirements.txt`)

Pins do serviço produtos; o gateway usa os mesmos números nos pacotes em comum.

- **Python 3.12** (Dockerfiles e CI)
- **FastAPI 0.141.1** + **uvicorn[standard] 0.53.0**
- **SQLAlchemy[asyncio] 2.0.54** + **asyncpg 0.31.0**
- **Pydantic 2.13.5** / **pydantic-settings 2.15.0**
- **Alembic 1.20.0**
- **structlog 26.1.0** — logging estruturado em JSON
- **httpx 0.28.1** — chamadas serviço a serviço
- **aio-pika 10.0.1** — cliente RabbitMQ (**não** é `pika`)
- **redis 8.1.0**
- Só no gateway: **python-jose[cryptography] 3.5.0**, **passlib[bcrypt] 1.7.4**
  com **bcrypt 4.0.1** (pin obrigatório — ver o comentário em
  `api-gateway/requirements.txt`), **slowapi 0.1.10**, **aiosmtplib**, **jinja2**

Infra: **PostgreSQL 15-alpine**, **Redis 7-alpine**, **RabbitMQ 3.12-management-alpine**.

---

## Banco de dados: um Postgres, um schema por serviço

Não é "database per service". Em produção existe **um** container `db`
(`erp-db-prod`) com um único banco (`POSTGRES_DB=erp`), e cada serviço recebe sua
própria `DATABASE_URL` apontando para **esse mesmo banco** — veja
`.env.production.example`, onde `DATABASE_URL_GATEWAY` até
`DATABASE_URL_NOTIFICACOES` são todas
`postgresql+asyncpg://erp:...@db:5432/erp`.

O isolamento é por **schema**. O one-shot `db-init` do `docker-compose.prod.yml`
roda `CREATE SCHEMA IF NOT EXISTS` para: `gateway`, `empresas`, `clientes`,
`produtos`, `estoque`, `vendas`, `financeiro`, `notificacoes`, `evolution`. Em
dev o mesmo trabalho é feito por `postgres/init-schemas.sql`, montado em
`/docker-entrypoint-initdb.d`.

### Migrations

Cada serviço tem seu próprio `alembic.ini` e `alembic/versions/`. O
`alembic upgrade head` roda **no boot do serviço**, como subprocesso disparado de
`database.py`, e a inicialização aborta de propósito se `alembic/versions/`
estiver sem revisions. Consequência operacional: uma revision que falha vira
crashloop do container.

```bash
# dentro do diretório do serviço (services/produtos, api-gateway, ...)
alembic revision --autogenerate -m "descrição"
alembic upgrade head
alembic downgrade -1
```

---

## Arquitetura em camadas

```
                 Cloudflare / cloudflared
                            │
                  ┌─────────▼─────────┐
                  │ api-gateway :8000 │  valida JWT, rate limit,
                  │                   │  injeta X-Empresa-Id
                  └─────────┬─────────┘
                            │  httpx + X-Servico-Interno-Token
        ┌───────────┬───────┴───────┬───────────┐
   ┌────▼────┐ ┌────▼────┐     ┌────▼────┐ ┌────▼────┐
   │clientes │ │produtos │ ... │ vendas  │ │empresas │
   │  :8001  │ │  :8002  │     │  :8004  │ │  :8007  │
   └────┬────┘ └────┬────┘     └────┬────┘ └────┬────┘
        └───────────┴───────┬───────┴───────────┘
                  ┌─────────▼─────────┐
                  │  PostgreSQL 15    │  1 banco `erp`,
                  │  (schema/serviço) │  1 schema por serviço
                  └───────────────────┘
```

Dentro de um serviço que tem rotas (clientes, empresas, estoque, produtos, vendas):

```
routers/      → endpoints HTTP, validação de entrada
services/     → lógica de negócio, transações
repositories/ → acesso a dados (SQLAlchemy)
models/       → ORM        schemas/ → Pydantic
```

---

## Comunicação entre serviços

### Síncrona (HTTP, httpx)

Toda chamada interna leva a prova de origem: `auth_interno()` em `interno.py`,
opt-in por chamada, porque esses serviços também falam com Mercado Pago, viacep e
Evolution API — mandar o segredo interno para terceiro é vazar credencial.

```python
async with httpx.AsyncClient() as client:
    response = await client.get(
        f"{settings.PRODUTOS_URL}/produtos/{produto_id}",
        headers=auth_interno({"X-Empresa-Id": str(empresa_id)}),
        timeout=10.0,
    )
```

### Assíncrona (RabbitMQ, aio-pika)

Cada um dos 7 serviços (o gateway não) tem `events/publisher.py` com um `EventPublisher` (`connect`,
`publish`, `close`) sobre `aio_pika`.

**A CONFIRMAR:** não localizei nenhum consumidor de fila no backend — só
publishers. Antes de documentar um fluxo "publica → consome", confirme quem lê a
exchange.

---

## Logs e health check

```python
import structlog

log = structlog.get_logger()
log.info("operacao_sucesso", usuario_id=usuario_id, produto_id=produto_id)
```

`structlog` está configurado com `TimeStamper(fmt="iso")` + `JSONRenderer()` em
cada `main.py`.

Todos os 8 serviços expõem `GET /health`, com resposta de dois campos apenas
(sem timestamp):

```json
{ "status": "healthy", "service": "produtos" }
```

O gateway tem ainda o readiness profundo (banco, Redis e os serviços). No
processo a rota é **`GET /health/ready`** (`api-gateway/main.py:154`); de fora ela
chega como `/api/health/ready` porque o nginx do frontend remove o prefixo `/api`
antes de repassar (`frontend/nginx.conf:36`). Detalhes no
[runbook de produção](../06-operacao/runbook-producao.md).

---

## Testes

Existem **62 arquivos `test_*.py`** no repositório, mas o CI roda só **49**: os de
`tests/unit` e os das pernas por serviço. `tests/integration` (9), `tests/e2e` (1) e
os 3 scripts soltos em `tests/` **não rodam no CI** (`.github/workflows/ci.yml`
não os referencia). Não há `Makefile`: os comandos abaixo são os do `.github/workflows/ci.yml`.

| Local | Arquivos |
|---|---|
| `tests/unit` | 17 |
| `tests/integration` | 9 (fora do CI) |
| `tests/e2e` | 1 (fora do CI) |
| `tests/` (scripts manuais, contra serviço vivo) | 3 (fora do CI) |
| `api-gateway/tests` | 5 |
| `services/vendas/tests` | 10 |
| `services/produtos/tests` | 7 |
| `services/estoque/tests` | 5 |
| `services/empresas/tests` | 2 |
| `services/clientes/tests` | 1 |
| `services/financeiro/tests` | 1 |
| `services/notificacoes/tests` | 1 |

O CI tem duas pernas, com capacidades diferentes:

```bash
# perna "backend": só tests/unit, com a config própria
pip install -r tests/requirements.txt
pytest -c tests/pytest.ini tests/unit

# perna "services": uma por serviço, a partir do diretório do serviço,
# porque eles importam flat (`from main import app`, `from config import settings`)
cd services/produtos
pip install -r requirements.txt -r ../../tests/requirements.txt
psql -h localhost -U erp -d erp -v ON_ERROR_STOP=1 -f ../../postgres/init-schemas.sql
alembic upgrade head          # a cadeia inteira contra banco vazio
pytest tests -p no:cacheprovider
```

Os arquivos soltos diretamente em `tests/` são scripts manuais que chamam um
serviço em `localhost`; o CI os exclui de propósito, filtrando por caminho.

**A CONFIRMAR:** não há `--cov` nem `cov-fail-under` em `ci.yml`, `pytest.ini`,
`setup.cfg` ou `pyproject.toml`. Nenhum percentual de cobertura é medido ou
exigido hoje — não publique um alvo de cobertura sem antes criar o gate.

---

## Subir o ambiente

Não existe `docker-compose.yml` sem sufixo: um `docker compose up` cru não acha
arquivo. Os que existem são `docker-compose.dev.yml`, `docker-compose.prod.yml`,
`docker-compose.build.yml` e `docker-compose.cloudflare.yml`.

```bash
docker compose -f docker-compose.dev.yml up -d
docker compose -f docker-compose.dev.yml logs -f produtos
docker compose -f docker-compose.dev.yml up -d --build
```

Produção não sobe à mão: o deploy é pelo Coolify, a partir de
`docker-compose.prod.yml` com imagens do registry
(`ghcr.io/.../<servico>:<tag>`). O passo a passo está em
[deploy](../06-operacao/deploy.md).

Não há `docker-compose.nginx.yml` e não há nginx como reverse proxy: o TLS
termina na Cloudflare e o tráfego chega por `cloudflared`. O único nginx do stack
é o que serve o SPA já buildado, dentro da imagem do frontend. pgAdmin está
**comentado** em `docker-compose.dev.yml` e não existe em produção.

---

## Guias relacionados

- [Transações de Banco de Dados](./transacoes-banco-dados.md)
- [Evolution API](./integracao/evolution-api.md)
- [Arquitetura Geral](../03-arquitetura/README.md)
- [Microsserviços](../03-arquitetura/microsservicos.md)
- [Regras de Negócio](../11-regras-negocio/README.md)
- [API Reference](../10-api-reference/README.md)
- [Setup do Projeto](../../QUICK-START.md)
- [Troubleshooting](../06-operacao/troubleshooting.md)
- [Deploy](../06-operacao/deploy.md)
- [Runbook de Produção](../06-operacao/runbook-producao.md)

---

## Contribuindo

1. **Seguir a estrutura de camadas** — router → service → repository.
2. **Usar transações atômicas** em operações de escrita; ver
   [transações](./transacoes-banco-dados.md).
3. **Validar entrada** com schemas Pydantic; regra de negócio no service.
4. **Escrever testes** no diretório do serviço (`services/<svc>/tests/`) ou em
   `tests/unit` — são esses os caminhos que as duas pernas do CI rodam.
5. **Migration nova = risco de crashloop**: ela roda no boot do container em
   produção. Teste `alembic upgrade head` contra banco vazio antes do PR, como o
   CI faz.

O processo completo de PR está em [CONTRIBUTING](../../.github/CONTRIBUTING.md) e
o checklist em
[CHECKLIST_DESENVOLVIMENTO](../02-desenvolvimento/CHECKLIST_DESENVOLVIMENTO.md).

---

**Última atualização:** 2026-09-25
