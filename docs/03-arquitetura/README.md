# Arquitetura do Sistema

Índice da pasta. O conteúdo extenso vive nos documentos abaixo — aqui ficam
apenas os ponteiros e os poucos fatos de arquitetura que não têm outro lar.

---

## Documentos desta pasta

| Documento | Do que trata |
|---|---|
| [Visão geral](./visao-geral.md) | Stack, estrutura de pastas e o resumo dos 8 serviços |
| [Microsserviços](./microsservicos.md) | Detalhe de cada serviço: domínio, modelos e rotas |
| [Comunicação entre serviços](./comunicacao.md) | Como o gateway fala com os serviços e os serviços entre si |
| [Plano de controle da plataforma](./plataforma.md) | A camada SaaS (multi-tenant) sobre o ERP |
| [Persistência e durabilidade](./persistencia-e-durabilidade.md) | Onde o banco vive e como sobrevive a deploys |
| [Performance e consumo de CPU](./performance-cpu.md) | O aperto de CPU na VPS e o que foi feito a respeito |

## Relacionados

- [Regras de negócio](../11-regras-negocio/README.md)
- [Referência da API da plataforma](../10-api-reference/plataforma-api.md)
- [Runbook de produção](../06-operacao/runbook-producao.md)

---

## Serviços e portas

Portas lidas de `docker-compose.dev.yml` (bloco `ports:` e o `--port` de cada
`command:`). Em dev, as portas 8001-8007 dos microsserviços são publicadas só em
`127.0.0.1`; o gateway (8000) e o frontend (3000) são publicados em todas as
interfaces, assim como o Postgres, o Redis, o RabbitMQ e a Evolution API (ver a
lista de infraestrutura abaixo).

| Serviço | Porta | Container (dev) |
|---|---|---|
| API Gateway | 8000 | `erp-api-gateway-dev` |
| Clientes | 8001 | `erp-clientes-dev` |
| Produtos | 8002 | `erp-produtos-dev` |
| Estoque | 8003 | `erp-estoque-dev` |
| Vendas | 8004 | `erp-vendas-dev` |
| Financeiro | 8005 | `erp-financeiro-dev` |
| Notificações | 8006 | `erp-notificacoes-dev` |
| Empresas | 8007 | `erp-empresas-dev` |

Infraestrutura: PostgreSQL 15 em `5432`, Redis 7 em `6379`, RabbitMQ em
`5672` (painel em `15672`), Evolution API em `8080`, frontend em `3000`.

---

## Três coisas que a documentação antiga afirmava e o código não confirma

### 1. A comunicação é 100% HTTP síncrono — não há eventos em uso

Existe infraestrutura de eventos: o RabbitMQ sobe em dev e em produção, cada
um dos 7 microsserviços recebe `RABBITMQ_URL` (em dev o gateway não recebe; em
produção ele herda a variável pelo anchor `x-service-env`, mas o `config.py` do
gateway não a lê) e todos os 7 têm um `events/publisher.py` com um método
`publish()`. **Nenhum desses publishers é chamado por nenhum router, service ou
repository** — `get_publisher` e `event_publisher` não aparecem fora das
próprias pastas `events/`.

Na prática, toda integração entre serviços passa por `httpx` a partir de
`api-gateway/proxy/service_proxy.py`. Trate RabbitMQ como dependência
provisionada e ainda não usada, não como parte do desenho em funcionamento.

### 2. `shared/` não é biblioteca compartilhada — é código morto

A pasta `shared/` existe na raiz (`exceptions.py`, `pagination.py`, `events/`),
mas `from shared` / `import shared` retorna **zero ocorrências** em `services/`,
`api-gateway/` e `tests/`, e **nenhum Dockerfile a copia** para dentro da
imagem. Cada serviço que precisa desse código tem a sua própria cópia local
(por exemplo `services/empresas/exceptions.py`).

Alterar `shared/` não muda o comportamento de serviço nenhum.

### 3. Nenhum serviço valida JWT — a identidade chega por header

O JWT é verificado só no API Gateway. Para os serviços internos, a identidade
do tenant chega como header `X-Empresa-Id`, injetado pelo gateway em
`proxy/service_proxy.py`, e o serviço confia nele: em
`services/produtos/utils/tenant.py`, `get_empresa_id` apenas exige que o header
exista e seja maior que zero.

O que sustenta o modelo é o gateway descartar os headers de identidade que
venham do cliente antes de repassar a requisição, somado às portas 8001-8007
publicadas apenas em `127.0.0.1`. Se um desses serviços ficar exposto na rede,
qualquer máquina vira qualquer tenant — e o 8007 (empresas) ainda aceita
`X-Plataforma`. O comentário no bloco `clientes` do `docker-compose.dev.yml`
registra exatamente isso.

---

## Banco de dados

**Uma** instância PostgreSQL 15 (banco `erp`), com um schema por serviço, não um
banco por serviço. Os schemas são criados por `postgres/init-schemas.sql`:
`gateway`, `empresas`, `clientes`, `produtos`, `estoque`, `vendas`,
`financeiro`, `notificacoes` e `evolution`. Todas as variáveis
`DATABASE_URL_*` do `.env.example` apontam para o mesmo banco `erp`.

Isso dá isolamento lógico e migrations independentes por serviço, mas **não** dá
isolamento de falha nem escala independente: um banco fora do ar derruba os oito.

Detalhes de backup, volume e durabilidade em
[persistência e durabilidade](./persistencia-e-durabilidade.md).

---

## Escalabilidade

### O que existe hoje

- **Connection pooling** em todos os oito serviços: `pool_size=10`,
  `max_overflow=20` em cada `database.py`.
- **Tetos por container** no Compose: `0.5` CPU e `512M` por serviço em dev
  (`x-dev-limits`), com `db` e frontend sobrescrevendo para valores maiores.
  Limite não reserva memória — só impede que um serviço em loop leve a máquina
  junto.
- **Rate limiting** no gateway: `300/minute` por IP como padrão
  (`api-gateway/middleware/rate_limit.py`); login, registro e reset de senha têm
  limites bem mais apertados aplicados por rota.
- **Redis** para refresh tokens, blacklist de tokens, tokens de reset de senha e
  idempotência no gateway. O rate limiting (`slowapi`) não usa Redis: o
  `Limiter` é criado sem `storage_uri`, então os contadores ficam em memória do
  processo (comportamento padrão do slowapi; A CONFIRMAR na versão instalada).

### O que não existe

- **Nenhuma réplica.** Não há `replicas:` em nenhum Compose; cada serviço roda
  em uma instância única.
- **Nenhum load balancer.** O nginx do projeto (`frontend/nginx.conf`) serve o
  SPA buildado dentro da imagem do frontend; ele não distribui carga entre
  instâncias. Em produção o TLS termina na Cloudflare; o único nginx é o do
  frontend, que repassa `/api/` a uma única instância do gateway
  (`frontend/nginx.conf:25-37`) e não há nginx na frente dos microsserviços.
- A VPS de produção é apertada em CPU — ver
  [performance e consumo de CPU](./performance-cpu.md) antes de propor subir
  mais containers.

O desenho é stateless o bastante para escalar horizontalmente (a sessão vive no
Redis, não em memória do processo), mas nada disso está configurado.

A CONFIRMAR: se há índices além das PKs/FKs geradas pelos models, e quais
listagens já usam paginação — não foi verificado modelo a modelo.

---

**Última verificação contra o código**: 25 de setembro de 2026
