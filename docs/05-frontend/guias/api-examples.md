# API pelo frontend — o que o cliente Axios faz por você

> Este arquivo **não guarda mais payloads de exemplo**. Eles viviam aqui escritos
> à mão, sem vínculo com schema nenhum, e apodreceram: documentavam `GET /pedidos`,
> `POST /produtos/{id}/variantes`, `GET /estoque/{variante_id}` e
> `GET /estoque/alertas/minimo` — **nenhuma dessas rotas existe** no código. Ver
> "Por que os exemplos saíram" no fim.
>
> Payload e contrato de rota agora têm um lugar só: **[docs/10-api-reference/](../../10-api-reference/README.md)**.
> O que fica aqui é o que só o frontend faz — o comportamento automático do
> cliente `api` em `frontend/src/services/api/axios.ts`.

---

## Onde achar payloads

| Preciso de… | Vá para |
|---|---|
| rota, verbo, corpo e resposta por serviço | [docs/10-api-reference/README.md](../../10-api-reference/README.md) (índice) |
| qual prefixo cai em qual serviço | [mapeamento-rotas.md](../../10-api-reference/mapeamento-rotas.md) |
| login, refresh, cookies HTTP-only | [guia-autenticacao.md](../../10-api-reference/guia-autenticacao.md) |
| fluxos completos ponta a ponta | [exemplos-praticos.md](../../10-api-reference/exemplos-praticos.md) |
| contrato de `Idempotency-Key` no gateway | [docs/10-api-reference/README.md](../../10-api-reference/README.md) (seção Idempotência) |

**Fonte de última instância é o código**, não um `.md`. Os routers ficam em
`api-gateway/routers/` e `services/<servico>/routers/`. O Swagger do gateway
(`/docs`, `/redoc`, `/openapi.json`) existe mas vem **desligado por padrão**:
`api-gateway/config.py:84` define `DOCS_ENABLED: bool = False`, e `main.py:62-64`
só monta as três rotas quando a flag está ligada. Para ver o schema gerado,
ligue `DOCS_ENABLED=true` no `.env` local.

---

## 1. `Idempotency-Key` em toda escrita (automático)

`axios.ts:42-43` injeta o header em todo `POST`, `PUT`, `PATCH` e `DELETE`:

```ts
if (WRITE_METHODS.includes((config.method ?? 'get').toLowerCase())) {
  config.headers['Idempotency-Key'] ??= crypto.randomUUID();
}
```

`WRITE_METHODS` (`axios.ts:14`) é `['post', 'put', 'patch', 'delete']`, espelhando
`METODOS` em `api-gateway/proxy/idempotency.py:19`. `GET`/`HEAD`/`OPTIONS` não
recebem chave.

Dois detalhes que importam para quem escreve tela:

- **O `??=` é deliberado.** A chave só é gerada se ainda não existe. Num reenvio o
  Axios passa o mesmo `config`, e gerar uma chave nova a cada passagem faria o
  gateway ver uma operação nova — exatamente o que a chave existe para impedir.
- **Você não precisa fazer nada.** Não gere chave à mão, não passe header. Só
  passe pelo cliente `api` exportado de `axios.ts`; um `fetch()` cru perde isso.

### O que o gateway faz com ela

De `api-gateway/proxy/idempotency.py`:

| Situação | Resposta |
|---|---|
| primeira chamada | reserva a chave no Redis (marcador `EM_VOO`), encaminha, guarda a resposta final |
| repetição depois da resposta | a resposta guardada, com **`X-Idempotent-Replay: true`** (`:82`) |
| repetição com a primeira ainda em voo | **409** `"Requisição com esta Idempotency-Key ainda está em processamento"` (`:72-75`) |

TTL da reserva: `IDEMPOTENCY_TTL_SECONDS`, default **86400** s
(`api-gateway/config.py:25`).

Nem toda resposta é guardada. `concluir()` (`idempotency.py:100-102`) **libera** a
reserva quando o status é `>= 500`, está em `TRANSITORIOS` (`408`, `425`, `429`) ou
o corpo passa de `MAX_BODY` (256 KB) — nesses casos o cliente pode reenviar com a
mesma chave. Só 2xx e 4xx de negócio ficam guardados para replay.

O header `X-Idempotent-Replay` é legível no browser porque o CORS do gateway o
expõe: `expose_headers=["X-Idempotent-Replay"]` (`api-gateway/main.py:86`).

> A idempotência do gateway é defesa contra retry de cliente, não a garantia
> final — essa continua sendo o `UNIQUE` no banco de cada serviço
> (`idempotency.py:1-9`).

---

## 2. Retry escalonado na janela de deploy (automático)

`axios.ts:97-110` reenvia a requisição quando o deploy derruba o gateway por
alguns segundos:

- **Status que disparam** (`axios.ts:8`): `502`, `503`, `504`.
- **Métodos** (`axios.ts:9`): só `get`, `head`, `options`.
- **Tentativas** (`axios.ts:10`): até `3`.
- **Espera** (`axios.ts:108`): `sleep(attempt * 1000)` — **1s, depois 2s, depois 3s**.

Por que é mais estreito que `isRetryableError` de `utils/errorLogger`: aquele
retenta todo `500+`, e um `500` de verdade é bug de aplicação — retentar só
triplica a carga e atrasa o erro que o usuário precisa ver.

**Escritas estão de fora de propósito.** Elas já carregam `Idempotency-Key`, então
um replay não duplicaria a venda — mas uma chave reservada cuja primeira tentativa
ainda está em voo responde **409**, e o loop de retry entregaria esse 409 em vez do
resultado real. Alargar a lista exige antes aguardar e desembrulhar o 409; é
mudança de comportamento, não lista maior.

**Consequência na UI:** um `GET` pode demorar até ~6s a mais antes de falhar.
Spinner e skeleton precisam suportar isso sem piscar erro.

---

## 3. Formato de erro

O tipo consumido pelo frontend é mínimo (`frontend/src/types/common.ts:20-23`):

```ts
export interface ApiError {
  detail: string;
  status_code?: number;
}
```

Helpers em `axios.ts`: `getErrorMessage(error, fallback?)` extrai
`response.data.detail` e `getErrorStatus(error)` extrai o status. Use-os em vez de
cavar o `AxiosError` na tela.

Atenção: `detail` **não é sempre string**. Num `422` do FastAPI ele é uma lista de
objetos de validação. O `getErrorMessage` devolve esse valor como veio, então uma
tela que joga o retorno direto no toast pode renderizar `[object Object]` num
erro de validação.

Os códigos e as mensagens de erro por endpoint estão em
[docs/10-api-reference/README.md](../../10-api-reference/README.md).

---

## Por que os exemplos saíram

Auditoria de 2026-09-26 conferiu os payloads deste arquivo contra os routers.
Amostra do que estava errado:

| O arquivo dizia | O código diz |
|---|---|
| `GET /pedidos`, `GET /pedidos/{id}`, `PATCH /pedidos/{id}/status` | prefixo `/pedidos` não existe em `ServiceProxy.SERVICE_URLS` (`api-gateway/proxy/service_proxy.py:23-38`) |
| `POST /produtos/{id}/variantes` | variantes é router próprio: `APIRouter(prefix="/variantes")` (`services/produtos/routers/produtos.py:297`) |
| `GET /estoque/{variante_id}` | `GET /estoque/{estoque_id}` (`services/estoque/routers/estoque.py:111`) |
| `POST /estoque/{variante_id}/entrada` | `POST /estoque/entrada` (`estoque.py:140`) |
| `GET /estoque/alertas/minimo` | `GET /estoque/baixo` (`estoque.py:78`) |
| `GET /contas`, `POST /contas/{id}/pagamentos` | `/contas` roteia para `financeiro`, que **não tem router** — só `GET /health` |
| login devolve `expires_in: 1800` | `LoginResponse` tem `access_token`, `refresh_token`, `token_type`, `user` — **sem `expires_in`** (`api-gateway/schemas/usuario.py:77-82`) |

Payload à mão sem vínculo com schema drifta em silêncio. Se um exemplo tem de
existir, que exista onde alguém o confere: em `docs/10-api-reference/`, ao lado da
rota, ou gerado do `/openapi.json`.

---

**A CONFIRMAR:** ninguém gera este `/openapi.json` automaticamente hoje —
`docs/10-api-reference/openapi.yaml` é mantido à mão. Se a geração automática
entrar, esta página some e o link vai direto para o schema.

**Última verificação contra o código:** 2026-09-26
