# Arquitetura de Comunicação — ERP Runas

Como o gateway, os 7 microsserviços e o frontend realmente conversam entre si.

**Resumo em uma linha**: a comunicação é **100% HTTP síncrono via `httpx.AsyncClient`**.
Não há barramento de eventos em uso — RabbitMQ sobe no compose, `aio-pika` está nos
requirements e `services/*/events/publisher.py` existe, mas **nenhum código chama
`publish()`**.

---

## 1. Os dois caminhos que existem

### 1.1 Cliente → API Gateway → Microsserviço

Todo tráfego de API entra pelo gateway (em produção, via o nginx do frontend):

```
Navegador / app
      │ HTTPS (Cloudflare Tunnel -> frontend-prod:80)
      ▼
nginx do frontend (location /api/, tira o prefixo /api)   [frontend/nginx.conf:25-37]
      │ HTTP
      ▼
api-gateway (8000)
      │ valida JWT + RBAC
      │ descarta headers internos vindos do cliente
      │ carimba X-Servico-Interno-Token, X-Empresa-Id, X-Cliente-Id
      │ aplica idempotência (se houver Idempotency-Key)
      ▼ httpx.AsyncClient(timeout=30.0)
microsserviço (8001–8007)
```

Implementação: `api-gateway/proxy/service_proxy.py` (`ServiceProxy.proxy_request`).
O roteamento é por prefixo de path, na tabela `ServiceProxy.SERVICE_URLS`:

| Prefixo | Serviço |
|---|---|
| `/clientes` | clientes |
| `/produtos`, `/categorias`, `/variantes`, `/fornecedores`, `/loja-online` | produtos |
| `/estoque` | estoque |
| `/loja`, `/carrinho`, `/pagamentos`, `/integracoes` | vendas |
| `/contas` | financeiro |
| `/notificacoes` | notificacoes |
| `/empresas` | empresas |

Path sem prefixo conhecido → 404 "Serviço não encontrado".

**Portas** (fonte: `services/*/Dockerfile` e `api-gateway/Dockerfile`):

| Serviço | Porta |
|---|---|
| api-gateway | 8000 |
| clientes | 8001 |
| produtos | 8002 |
| estoque | 8003 |
| vendas | 8004 |
| financeiro | 8005 |
| notificacoes | 8006 |
| empresas | 8007 |

### 1.2 Microsserviço → Microsserviço (HTTP direto)

Chamadas diretas, sempre com `httpx.AsyncClient` e sempre carimbadas com
`auth_interno(...)`. As que existem hoje no código:

| Origem | Destino | Onde |
|---|---|---|
| estoque | produtos (`/produtos/{id}`, `/variantes/{id}`) | `services/estoque/services/estoque_service.py:82-98` |
| vendas | produtos (cache de catálogo) | `services/vendas/services/cache_service.py:122-130` |
| vendas | produtos (`/produtos/{id}`) | `services/vendas/services/venda_service.py:94,96` |
| vendas | clientes (`/clientes/{id}`, `POST /clientes`, `/credito/ajustar`) | `services/vendas/services/venda_service.py:138-141` (existe/ativo), `:415-419,442-446` (débito/crédito do fiado, C3/Onda 6), `loja_service.py:177-179` |
| vendas | estoque (`/estoque/reservar`, `/liberar-reserva`, `/saida`, `/baixar-venda`, `/estornar-venda`, `/disponibilidade`) | `services/vendas/services/venda_service.py:157-397`, `reserva_temporaria_service.py:61-68` |
| vendas | empresas (`/empresas/publico/{slug}`, `/empresas/{id}`) | `services/vendas/utils/tenant.py:31-131` |
| vendas | api-gateway (`POST /auth/cliente/registrar-interno`) | `services/vendas/services/loja_service.py:210-215` |
| vendas | empresas (GET do nome da empresa para o e-mail de credenciais, montado como `{CLIENTES_URL}/../empresas/empresas/{id}`) | `services/vendas/services/loja_service.py:247` (A CONFIRMAR: se essa URL relativa resolve em algum ambiente; as outras chamadas a empresas usam `EMPRESAS_URL`) |

Notas de estado real:

- `services/financeiro` **não faz nenhuma chamada HTTP de saída** — não há `httpx`
  nem URL de outro serviço fora do `config.py`.
- `FINANCEIRO_URL` está declarada em `services/vendas/config.py:20` mas **não é usada**
  por nenhum código do serviço. Não existe `NOTIFICACOES_URL` em `vendas/config.py` —
  vendas não tem nem o endereço do serviço de notificações.
- A única chamada de dentro para o gateway é a de `loja_service.py` acima; ela usa
  `X-Registro-Interno-Token` (`REGISTRO_INTERNO_TOKEN`) além do token interno.

### Regra de isolamento

> Comunicação entre serviços via HTTP (`httpx` async) — nunca importar código de
> outro serviço.

- Serviços chamam outros serviços via HTTP.
- Serviços não importam código de outro serviço (só `shared/`).

---

## 2. Eventos assíncronos: infraestrutura morta

O que existe:

- `aio-pika==10.0.1` nos 7 `services/*/requirements.txt`.
- `services/*/events/publisher.py` nos 7 serviços, com método `publish()`.
- Container `rabbitmq` (`rabbitmq:3.12-management-alpine`) em
  `docker-compose.prod.yml:260`, com healthcheck e volume.
- `RABBITMQ_URL` obrigatória no env compartilhado dos serviços
  (`docker-compose.prod.yml:42`) e em `services/*/config.py`.

O que **não** existe:

- Nenhuma chamada a `publish()` fora do próprio `publisher.py` — `grep -rn "publish("`
  só devolve a definição e o `exchange.publish` interno dela.
- Nenhum import de `events` / `event_publisher` fora de `services/*/events/`.
- Nenhum consumidor: não há worker de fila em nenhum compose.
- Nenhum Celery: `celery==5.6.3` está nos requirements, mas não há `Celery(...)`,
  `celery_app`, `@shared_task` nem `beat_schedule` em lugar nenhum, e não há
  container de worker/beat. **Não existe scheduler residente separado**, mas há trabalho
periódico rodando: o `vendas` sobe dois loops `asyncio` no `lifespan`
(`services/vendas/main.py:37-71` — pagamentos pendentes a cada 60s, reconciliação de
estoque a cada 120s), e a régua de inadimplência depende de cron do host chamando
`POST /plataforma/jobs/regua` (runbook de produção, seção "O cron obrigatório").

Consequência prática: qualquer fluxo descrito como "publica evento X e o serviço Y
consome" é ficção. A baixa de estoque de uma venda acontece por chamada HTTP síncrona
de `vendas` para `estoque` (tabela da seção 1.2). O WhatsApp sai direto de `vendas`
para a Evolution API (`notificacao_service.py:359-374`), sem passar pelo serviço
`notificacoes`. Já **conta a receber**: `vendas` só grava a flag/coluna
`gera_conta_receber` / `conta_receber_id` e não chama o `financeiro` (ver "Notas de
estado real" acima) — A CONFIRMAR: o que de fato cria a conta a receber.

---

## 3. Contrato de origem interna: `X-Servico-Interno-Token`

Os serviços de `services/` **não validam JWT**: eles tratam `X-Empresa-Id` e
`X-Cliente-Id` como identidade confiável. O que prova que a chamada veio de dentro da
malha é um segredo compartilhado.

- **Segredo**: `SERVICO_INTERNO_TOKEN`, o **mesmo valor nos 8 containers**
  (`docker-compose.prod.yml`, bloco `api-gateway-prod`).
- **Quem carimba**: `auth_interno()` em `api-gateway/interno.py` (toda chamada
  proxiada, em `service_proxy.py`) e em `services/*/interno.py` (cada chamada
  serviço→serviço, opt-in, uma por vez — o carimbo é deliberadamente manual para não
  vazar o segredo em chamadas a Mercado Pago, viacep e Evolution API).
- **Quem valida**: middleware `validar_token_interno` em `services/*/interno.py`,
  montado em `services/*/main.py` com `app.middleware("http")(validar_token_interno)`.
- **Comparação**: `secrets.compare_digest(recebido.encode(), esperado.encode())`
  (`.encode()` porque `compare_digest` estoura `TypeError` com str não-ASCII).
- **Isento**: só `/health` (`ISENTOS = frozenset({"/health"})`) — o healthcheck do
  Docker bate em `localhost:PORTA/health` sem passar pelo gateway.
- Token inválido → `403 {"detail": "Forbidden"}` e log `servico_interno.invalido`.

### Hoje é FAIL-OPEN

Se o segredo **não estiver dos dois lados** (env vazia no chamador ou no validador), a
requisição **passa** e o serviço apenas registra:

```
log.warning("servico_interno.ausente", path=..., configurado=..., recebido=...)
```

Motivo documentado no código: o deploy não é blue-green — o stack velho cai antes do
novo subir — então há uma janela em que um lado já carimba e o outro ainda não tem a
env. Fechar junto com o deploy daria 403 no checkout e na baixa de estoque.

**Como fechar**: medir `servico_interno.ausente` em produção; zerado, troca-se o
`log.warning` pelo `return`/`raise` do ramo seguinte — uma linha.

---

## 4. Rotas de plataforma: o par `X-Plataforma` + `X-Plataforma-Token`

O serviço `empresas` não tem noção de papel (role). As rotas de administração da
plataforma — criar tenant, listar todas as empresas, alterar plano, apagar tenant —
são guardadas por um segundo segredo, de **escopo menor: só gateway e empresas**.

| | |
|---|---|
| Headers | `X-Plataforma: 1` **e** `X-Plataforma-Token: <segredo>` |
| Segredo | `PLATAFORMA_INTERNO_TOKEN` (só em `api-gateway-prod` e `empresas-prod`) |
| Quem injeta | `api-gateway/routers/plataforma.py`, helper `_empresas()` |
| Pré-condição | o router inteiro roda sob `dependencies=[Depends(require_super_admin)]` |
| Quem valida | `exigir_plataforma` em `services/empresas/routers/empresas.py` |

Por que não basta o `SERVICO_INTERNO_TOKEN`: ele é o mesmo nos 8 containers, logo prova
apenas que a chamada veio de *algum* deles. Rotas que apagam tenant precisam de prova
mais forte. Antes deste par, `X-Plataforma: 1` era afirmação sem prova — bastava
alcançar a porta 8007 para virar administrador da plataforma.

Ordem da validação em `exigir_plataforma`:

1. `X-Plataforma != "1"` → `403 "Rota exclusiva da administração da plataforma"`.
2. Segredo ausente de um dos lados → `log.warning("plataforma.sem_segredo")` e
   **deixa passar** (fail-open, mesma janela de deploy do item 3).
3. Segredo presente e diferente → `log.warning("plataforma.segredo_invalido")` + `403`.

**Como fechar**: medir `plataforma.sem_segredo`; zerado, o `log.warning` vira o mesmo
`raise` do ramo seguinte.

---

## 5. O gateway descarta headers internos vindos do cliente

Antes de injetar os seus, `service_proxy.py` remove da cópia de `request.headers`:

```
x-empresa-id, x-cliente-id, x-plataforma, x-servico-interno-token, x-plataforma-token
```

Isso importa porque as chaves de `request.headers` chegam em minúsculas: um
`x-empresa-id` do cliente sobreviveria ao lado do `X-Empresa-Id` injetado. E
`X-Plataforma` nunca era sobrescrito — com o proxy catch-all `/empresas/{path:path}`,
qualquer admin de tenant mandava `X-Plataforma: 1` e virava administrador da
plataforma.

Ordem exata no código: sanear → `auth_interno(headers)` → `_inject_context_headers(...)`.

**Teste de regressão**: `tests/unit/test_headers_internos_nao_vem_do_cliente.py` — lê a
fonte do proxy e falha se algum header interno deixar de ser descartado entre
`headers = dict(request.headers)` e a injeção de contexto; um segundo teste garante que
`exigir_plataforma` continua lendo `Header(None, alias="X-Plataforma")`.

---

## 6. Idempotência: centralizada no gateway

Nenhum serviço implementa idempotência por conta própria. Ela mora em
`api-gateway/proxy/idempotency.py` porque todo tráfego do frontend passa por
`ServiceProxy.proxy_request()` — uma implementação cobre os 7 serviços.

| | |
|---|---|
| Header de entrada | `Idempotency-Key` (ausente → caminho normal, nada muda) |
| Métodos cobertos | `POST`, `PUT`, `PATCH`, `DELETE` |
| Chave Redis | `idem:{empresa_id ou 0}:{sha256 de "metodo\|path\|valor"}` |
| TTL | `IDEMPOTENCY_TTL_SECONDS`, default **86400** (`api-gateway/config.py:25`) |
| Replay | resposta guardada, devolvida com `X-Idempotent-Replay: true` |
| Em voo | requisição idêntica ainda processando → `409 Conflict` |

Fluxo: reserva a chave **antes** de encaminhar (`SET nx ex`), encaminha, e fecha a
reserva com a resposta final. Liberam a reserva (cliente pode reenviar): status ≥ 500,
status transitórios `{408, 425, 429}` e corpo acima de 256 KB (`MAX_BODY`), além de
timeout e erro de conexão com o upstream.

Esta camada é defesa contra retry de cliente. **A garantia final continua sendo o
`UNIQUE` no banco de cada serviço** — as duas se somam, nenhuma substitui a outra.

---

## 7. Isolamento: o que é verdade e o que não é

### Banco de dados

Não há um Postgres por serviço. Há **um container `db`, um database `erp`, e um schema
por serviço**:

- `docker-compose.prod.yml:51` define o único serviço `db`; `POSTGRES_DB=erp`.
- `db-init` (`docker-compose.prod.yml:140-238`) roda `CREATE SCHEMA IF NOT EXISTS` para
  cada schema, porque as migrations fazem `CREATE TABLE <schema>.<table>` mas nunca
  `CREATE SCHEMA`.
- Cada serviço recebe sua própria variável (`DATABASE_URL_CLIENTES`,
  `DATABASE_URL_VENDAS`, …), mas todas apontam para o mesmo
  `postgresql+asyncpg://…@db:5432/erp` (`.env.example:60-67`).

O isolamento é **lógico (schema + `X-Empresa-Id`)**, não físico.

### O que de fato é independente

- Cada serviço tem seu `Dockerfile` e seu `requirements.txt`.
- Nenhum serviço importa código de outro (só `shared/`).
- Cada serviço tem suas próprias migrations Alembic.

### Exposição de portas

- **Produção**: `docker-compose.prod.yml` **não publica nenhuma porta**. O único
  ingress é o `cloudflared` (`docker-compose.prod.yml:539`), que aponta para
  `frontend-prod:80` (o nginx do frontend repassa `/api/` ao gateway); o comentário do
  compose lista ainda uma rota para o Coolify no host (`:547`). Os serviços só se alcançam pela rede
  `erp-network`.
- **Desenvolvimento**: os serviços internos publicam apenas em loopback
  (`127.0.0.1:8001:8001` … `127.0.0.1:8007:8007`), garantido por
  `tests/unit/test_portas_internas_so_em_localhost.py`, que trata todo diretório novo
  em `services/` como interno por definição.

---

## 8. Resumo

| Caminho | Transporte | Prova de identidade |
|---|---|---|
| Cliente → gateway | HTTPS via Cloudflare Tunnel, nginx do frontend em `/api/` | JWT + RBAC no gateway |
| Gateway → serviço | `httpx.AsyncClient` (timeout 30s) | `X-Servico-Interno-Token` (fail-open) + `X-Empresa-Id`/`X-Cliente-Id` injetados |
| Gateway → empresas (plataforma) | `httpx.AsyncClient` (timeout 30s) | acima + `X-Plataforma: 1` e `X-Plataforma-Token` (fail-open) |
| Serviço → serviço | `httpx.AsyncClient` (timeout 5s/10s) | `auth_interno()` explícito por chamada |
| Eventos assíncronos | — | **não existe em uso** |

### Dívida conhecida

1. Os dois contratos de segredo são **fail-open**. Fechar cada um é uma linha, depois de
   confirmar que `servico_interno.ausente` e `plataforma.sem_segredo` estão zerados em
   produção.
2. `SERVICO_INTERNO_TOKEN` é token estático, não claim assinado: responde "veio de
   dentro" e nada mais — não diz qual serviço chamou nem expira.
3. RabbitMQ, `aio-pika` e `celery` consomem recurso e espaço de imagem sem nenhum uso.
   Ou se implementa o consumo, ou se remove.
4. `FINANCEIRO_URL` configurada em `vendas` sem nenhum uso (`services/vendas/config.py:20`).

### A CONFIRMAR

- Quais eventos de domínio o produto de fato precisa (se algum) antes de decidir entre
  implementar o consumo RabbitMQ ou remover a dependência.
- Se o `rabbitmq` de produção está de pé apenas por inércia do compose ou se algum
  consumidor fora deste repositório se conecta a ele.

---

**Última atualização**: 2026-09-25
