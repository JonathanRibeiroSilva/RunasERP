# API da Plataforma - Runas

> **Referência completa** das rotas de administração da camada SaaS (gestão de tenants).
>
> Este arquivo é **contrato**: o que cada rota recebe e devolve. O *porquê* das
> decisões está em [docs/03-arquitetura/plataforma.md](../03-arquitetura/plataforma.md).

---

## 🚨 Aviso de acesso

O router inteiro é declarado com a dependência no nível do router:

```python
router = APIRouter(
    prefix="/plataforma",
    tags=["Plataforma"],
    dependencies=[Depends(require_super_admin)],
)
```
`api-gateway/routers/plataforma.py:28-32`

**`SUPER_ADMIN` não herda de `ADMIN`.** São papéis disjuntos: `require_super_admin`
compara por igualdade (`current_user.role != RoleEnum.SUPER_ADMIN` →
`403 "Acesso negado: apenas a administração da plataforma"`) —
`api-gateway/auth/oauth2.py:153-166`. Um `ADMIN` de tenant recebe 403 em **todas**
as rotas desta página. Os papéis existentes são `SUPER_ADMIN`, `ADMIN` e `OPERADOR`
(`api-gateway/models/usuario.py:13-17`).

Existe um segundo router no mesmo arquivo, **sem** `require_super_admin`
(`router_publico`, `plataforma.py:438`), com as duas rotas de máquina: webhook do
Mercado Pago e job do cron. Elas estão na seção "Rotas públicas" no fim.

**O host não faz parte da autorização.** O frontend separa o painel (host `admin.*`)
do ERP dos lojistas pelo hostname, mas isso é só de interface
(`frontend/src/config/host.ts`, ver [plataforma.md §5](../03-arquitetura/plataforma.md)).
As rotas desta página respondem em qualquer host que chegue ao gateway (`app` ou
`admin`), protegidas só por `require_super_admin`. Não confunda com as **telas**
`/plataforma` (visão geral) e `/plataforma/tenants` (lista de lojistas) do React: essas
são rotas do navegador, sem o prefixo `/api`.

---

## 📋 Visão geral

**Serviço**: api-gateway
**Autenticação**: Bearer Token (JWT) — `OAuth2PasswordBearer(tokenUrl="/auth/login", auto_error=False)`, `api-gateway/auth/oauth2.py:19`
**Formato**: JSON

```http
Authorization: Bearer <access_token>
```

O token pode vir do header **ou** do cookie `access_token`: `get_current_user` lê
`request.cookies.get("access_token") or token_from_header` (`oauth2.py:75`). Sem
nenhum dos dois, `401 "Token não fornecido"` (`oauth2.py:76-81`).

### Nota de borda — o prefixo `/api` não existe no gateway

O caminho que o navegador chama é `/api/plataforma/...`, mas o caminho registrado
no FastAPI é `/plataforma/...`. Quem remove o `/api` é a camada web:

- produção: `rewrite ^/api/(.*)$ /$1 break;` em `frontend/nginx.conf:36`, proxiando para `api-gateway-prod:8000` (`frontend/nginx.conf:35`);
- dev: `rewrite: (path) => path.replace(/^\/api/, '')` em `frontend/vite.config.ts:84`.

O `app = FastAPI(...)` do gateway não define `root_path`, e os routers são
incluídos sem prefixo extra (`api-gateway/main.py:99-100`). Ou seja: batendo direto
no gateway, use `/plataforma/...`; passando pelo nginx/Vite, use `/api/plataforma/...`.

Os dois routers de plataforma são registrados **antes** do proxy, porque o proxy
tem rota catch-all e o Starlette casa por ordem de registro (`api-gateway/main.py:98-101`).

---

## 📍 Tabela das rotas

Todas com prefixo `/plataforma`. "Irreversível" = não há rota que desfaça.

| Método | Caminho | O que faz | Irreversível | Fonte |
|--------|---------|-----------|--------------|-------|
| GET | `/tenants` | Lista tenants + usuários ativos + assinatura | não | `plataforma.py:72` |
| POST | `/tenants` | Provisiona empresa + admin inicial | não (mas ocupa slug/CNPJ) | `plataforma.py:99` |
| PATCH | `/tenants/{empresa_id}/suspender` | Corta o acesso do tenant | não (há `/reativar`) | `plataforma.py:158` |
| PATCH | `/tenants/{empresa_id}/reativar` | Devolve o acesso | não | `plataforma.py:163` |
| PATCH | `/tenants/{empresa_id}/plano` | Altera plano, limites e status | não | `plataforma.py:185` |
| GET | `/tenants/{empresa_id}/auditoria` | Trilha de escritas do tenant | não | `plataforma.py:199` |
| POST | `/auditoria/{registro_id}/reverter` | **Sobrescreve um registro de negócio** | ⚠️ **SIM** | `plataforma.py:239` |
| GET | `/tenants/{empresa_id}/exportar` | **Exporta dados de negócio do tenant** | 🔒 **LGPD** | `plataforma.py:336` |
| GET | `/tenants/{empresa_id}/dumps` | Lista backups (hoje sempre vazio) | não | `plataforma.py:390` |
| POST | `/tenants/{empresa_id}/assinatura` | Cria preapproval no Mercado Pago | não | `plataforma.py:410` |
| DELETE | `/tenants/{empresa_id}/assinatura` | **Cancela a assinatura no Mercado Pago** | ⚠️ **SIM** | `plataforma.py:425` |
| POST | `/webhook/mercadopago` | Webhook de pagamento (**sem JWT**) | não | `plataforma.py:441` |
| POST | `/jobs/regua` | Varredura de vencimentos + poda de auditoria (**sem JWT**) | ⚠️ **SIM** (poda) | `plataforma.py:480` |

> ⚠️ Suspender e reativar são **PATCH**, não POST. Cancelar assinatura é **DELETE**,
> não POST. Confira sempre o verbo contra o decorador no arquivo antes de escrever
> um cliente.

---

## Tenants

### Listar todos os tenants
```http
GET /plataforma/tenants
```
`plataforma.py:72-96`

Busca as empresas no serviço empresas (`GET /empresas/plataforma/todas`,
`services/empresas/routers/empresas.py:290-303`) e enriquece cada item com duas
consultas locais ao banco do gateway: contagem de usuários ativos e a linha de
`gateway.assinaturas`.

**Response 200:**
```json
{
  "items": [
    {
      "id": 1,
      "usuarios_ativos": 4,
      "assinatura": {
        "empresa_id": 1,
        "plano": "BASICO",
        "valor": 149.9,
        "status": "ATIVA",
        "vence_em": "2026-10-24",
        "somente_leitura": false
      }
    }
  ],
  "total": 1
}
```
Os campos da empresa em si vêm do serviço empresas; `usuarios_ativos` e
`assinatura` são acrescentados aqui (`plataforma.py:93-95`). `assinatura` é `null`
para tenant sem linha em `gateway.assinaturas`. As colunas da assinatura são
exatamente as da query em `plataforma.py:88-90`.

---

### Provisionar tenant
```http
POST /plataforma/tenants
```
`plataforma.py:99-135` — **Response 201**.

**Request Body:** o corpo é recebido como `dict` cru no gateway; a validação de
schema acontece no serviço empresas. Obrigatório ter as duas chaves `empresa` e
`admin`, senão 422 (`plataforma.py:113-114`).

```json
{
  "empresa": {
    "razao_social": "Loja Exemplo LTDA",
    "nome_fantasia": "Loja Exemplo",
    "cnpj": "00.000.000/0001-00",
    "cep": "01310-100",
    "logradouro": "Av. Paulista",
    "numero": "1000",
    "bairro": "Bela Vista",
    "cidade": "Sao Paulo",
    "uf": "SP"
  },
  "admin": {
    "nome": "Fulano de Tal",
    "email": "admin@lojaexemplo.com.br",
    "senha": "SenhaForte123"
  }
}
```

- `empresa` é validado contra `EmpresaCreate` (`services/empresas/schemas/empresa.py:111-113`),
  que herda `EmpresaBase` (`:25-55`). `slug` é opcional — omitido, é gerado a partir
  do nome fantasia. `cnpj` tem exatamente 18 caracteres (formatado) e `cep` 9.
- `admin` é validado contra `UsuarioCreate` (`api-gateway/schemas/usuario.py:10-20`):
  `nome` (mín. 3), `email`, `senha`. **`role` e `empresa_id` são sobrescritos pelo
  router** com `ADMIN` e o id da empresa recém-criada (`plataforma.py:126-128`) —
  não adianta mandar outro valor.
- `catalogo_ativo` recebe `False` por padrão se não vier no corpo (`plataforma.py:117`):
  a loja nasce fechada.

**Response 201:**
```json
{
  "empresa": { "id": 12 },
  "admin": { "id": "uuid", "email": "admin@lojaexemplo.com.br" }
}
```
(`empresa` é o objeto inteiro devolvido pelo serviço empresas; `admin` traz só os
dois campos — `plataforma.py:135`.)

**409** — e-mail do admin já cadastrado. Nesse caso a empresa recém-criada é
apagada por compensação (`DELETE /empresas/{id}` no serviço empresas,
`plataforma.py:122`), porque não há transação distribuída entre gateway e empresas.
O mesmo rollback roda se a criação do usuário levantar qualquer exceção
(`plataforma.py:129-132`).

---

### Suspender tenant
```http
PATCH /plataforma/tenants/{empresa_id}/suspender
```
`plataforma.py:158-160`. Sem corpo.

Faz duas coisas (`_definir_acesso`, `plataforma.py:138-155`):
1. `PATCH /empresas/{id}/plano` no serviço empresas com `{"status": "SUSPENSA"}`;
2. `UPDATE usuarios SET ativo = false` para todos os usuários do tenant, no banco
   do gateway.

É o passo 2 que corta de fato: `get_current_user` relê o usuário do banco a cada
request, então a sessão cai no request seguinte.

**Response 200:** a empresa atualizada, como devolvida pelo serviço empresas.

---

### Reativar tenant
```http
PATCH /plataforma/tenants/{empresa_id}/reativar
```
`plataforma.py:163-165`. Sem corpo. Mesmo caminho da suspensão, com
`status = "ATIVA"` e `usuarios.ativo = true`.

**Response 200:** a empresa atualizada.

---

### Alterar plano e limites
```http
PATCH /plataforma/tenants/{empresa_id}/plano
```
`plataforma.py:185-194`.

**Request Body** (todos opcionais, `extra="forbid"` — campo desconhecido = 422 no
gateway, `plataforma.py:168-182`):
```json
{
  "plano": "PRO",
  "max_usuarios": 20,
  "max_produtos": 5000,
  "status": "ATIVA",
  "ativo": true
}
```
`status` é validado do outro lado contra `StatusEmpresa`, cujos valores são
`ATIVA`, `INATIVA` e `SUSPENSA` (`services/empresas/models/empresa.py:20-24`);
valor fora disso volta 422 do serviço empresas.

Só os campos **enviados** são repassados (`exclude_unset=True`, `plataforma.py:193`):
mandar os cinco com `null` zeraria plano e limites de quem só queria mudar o status.

**Response 200:** a empresa atualizada.

---

## Auditoria e reversão

### Trilha de auditoria do tenant
```http
GET /plataforma/tenants/{empresa_id}/auditoria
```
`plataforma.py:199-236`.

**Query Parameters:**
- `limit` (int, opcional, padrão `50`) — aplicado às **duas** listas.

**Response 200:**
```json
{
  "requisicoes": [
    { "id": 1, "usuario_id": "uuid", "metodo": "PATCH", "rota": "/produtos/9",
      "status_resposta": 200, "criado_em": "2026-09-24T10:00:00" }
  ],
  "registros": [
    { "id": 1, "schema_origem": "produtos", "tabela": "produtos",
      "registro_id": "9", "operacao": "UPDATE",
      "dados_antes": {}, "dados_depois": {},
      "revertido_em": null, "criado_em": "2026-09-24T10:00:00",
      "reversivel": true }
  ]
}
```

São dois níveis distintos de auditoria (`postgres/init-schemas.sql:61-87`):
- `requisicoes` vem de `gateway.auditoria` — trilha gravada pelo middleware: **quem e quando**;
- `registros` vem de `gateway.auditoria_registros` — snapshot gravado pela trigger SQL: **o quê**.

`reversivel` é calculado no router como `revertido_em is None` (`plataforma.py:235`),
para a tela não precisar adivinhar.

---

### ⚠️ Reverter uma escrita — DESTRUTIVO
```http
POST /plataforma/auditoria/{registro_id}/reverter
```
`plataforma.py:239-323`. Sem corpo.

> **Esta rota sobrescreve um registro de negócio de um tenant.** Ela só é possível
> porque a trigger `gateway.auditar_registro()` guarda `to_jsonb(OLD)` em
> `dados_antes` a cada UPDATE/DELETE (`postgres/init-schemas.sql:94-105`). **Sem o
> snapshot da trigger não há o que reverter**: um INSERT não tem estado anterior e
> a rota recusa com 422 dizendo para apagar o registro em vez de reverter
> (`plataforma.py:262-266`).

O que ela faz: reaplica `dados_antes` na tabela de origem
(`{schema_origem}.{tabela}`) via `jsonb_populate_record`, todas as colunas exceto
`id` (`plataforma.py:289-300`).

**Recusas deliberadas:**

| Código | Quando | Fonte |
|--------|--------|-------|
| 404 | Registro de auditoria não existe | `plataforma.py:258-259` |
| 409 | Já revertido (`revertido_em` preenchido) | `plataforma.py:260-261` |
| 422 | `dados_antes` vazio (era um INSERT) | `plataforma.py:262-266` |
| 409 | O registro de origem não existe mais | `plataforma.py:274-275` |
| 409 | O registro mudou depois desta operação — reverta a mais nova primeiro | `plataforma.py:276-281` |
| 422 | Snapshot só tem `id`, nada a reverter | `plataforma.py:290-291` |

**Response 200:**
```json
{ "revertido": true, "alvo": "produtos.produtos", "registro_id": "9" }
```

A reversão **não** apaga a história: marca `revertido_em = now()` no snapshot,
insere uma linha nova em `gateway.auditoria` com o super admin que mandou, e a
trigger da tabela de origem grava o snapshot novo (`plataforma.py:301-319`).

**Não existe rota de "desreverter".** O caminho de volta é reverter o snapshot que
a própria reversão gerou.

---

## Exportação (LGPD)

### 🔒 Exportar dados do tenant
```http
GET /plataforma/tenants/{empresa_id}/exportar
```
`plataforma.py:336-387`.

> **Dado pessoal de titulares do tenant sai do sistema aqui.** É o único ponto em
> que o super admin toca dado de negócio de um cliente (`plataforma.py:344-347`).
> Trate o arquivo gerado como dado pessoal: ele contém a base de clientes do
> lojista.

A chamada é **auditada antes de começar**: insere em `gateway.auditoria` quem
exportou, de qual tenant e quando (`plataforma.py:350-361`) — esse INSERT é
commitado antes do streaming começar.

**Response 200** — `StreamingResponse`, `Content-Type: application/json`,
`Content-Disposition: attachment; filename="tenant-{empresa_id}.json"`
(`plataforma.py:383-387`). É streaming porque montar o tenant inteiro em memória
derrubaria o gateway na VPS.

```json
{ "empresa_id": 12, "dados": { "empresa": {}, "clientes": {}, "produtos": {}, "estoque": {}, "vendas": {} } }
```

As cinco fontes e suas rotas estão em `FONTES_EXPORTACAO` (`plataforma.py:327-333`):
`empresa` → `/empresas`, `clientes` → `/clientes`, `produtos` → `/produtos`,
`estoque` → `/estoque`, `vendas` → `/vendas`. Cada uma é chamada com
`X-Empresa-Id` do tenant e `params={"limit": 1000}` (`plataforma.py:373-377`).

**Limitação real:** `limit=1000` por fonte. Um tenant com mais de mil registros em
qualquer coleção tem a exportação **truncada**, sem erro e sem aviso no arquivo.
Uma fonte que responda diferente de 200 entra no JSON como `{"erro": <status>}`
em vez de falhar a resposta inteira (`plataforma.py:378-380`).

Notificações e financeiro **não** estão na exportação — só as cinco fontes acima.

---

### Listar backups do tenant
```http
GET /plataforma/tenants/{empresa_id}/dumps
```
`plataforma.py:390-405`.

**Response 200** — hoje é uma resposta fixa, sempre esta:
```json
{ "items": [], "restauracao": "manual", "detalhe": "scripts/restaurar-tenant.sh (Fase 4)" }
```

**Não existe rota de restaurar, e é deliberado** (`plataforma.py:395-399`):
restaurar sobrescreve o tenant inteiro e descarta tudo posterior ao dump. O caminho
de suporte do dia a dia é a reversão pontual acima.

`scripts/restaurar-tenant.sh` é citado no corpo da resposta como trabalho de Fase 4,
mas **o arquivo ainda não existe** no repositório (`scripts/` tem hoje `README.md`,
`check-secrets.sh`, `graphify-smart.ps1`, `medir-downtime.sh`, `provisionar-lojista.ps1`,
`resgate-vps.sh`, `setup-graphify-hook.ps1`, `test-carrinho-recovery.ps1`,
`test-check-secrets.sh`). O campo `detalhe` é um plano, não um caminho executável.

---

## Cobrança

> **Dois Mercado Pagos no sistema.** As rotas abaixo usam
> `PLATAFORMA_MP_ACCESS_TOKEN` (`api-gateway/config.py:61`), a conta **do dono da
> plataforma**, que cobra a mensalidade dos lojistas. A conta de cada lojista, que
> cobra os clientes finais dele, mora em `vendas.configuracoes_pagamento` e não
> tem nada a ver com isto (`api-gateway/services/preapproval_service.py:4-9`).

### Gerar link de assinatura
```http
POST /plataforma/tenants/{empresa_id}/assinatura
```
`plataforma.py:410-422`.

**Request Body:**
```json
{ "email_pagador": "financeiro@lojaexemplo.com.br", "plano": "BASICO", "valor": 149.90 }
```
- `email_pagador` é **obrigatório** — ausente, 422 (`plataforma.py:417-419`);
- `plano` padrão `"BASICO"`, `valor` padrão `0` (`plataforma.py:421`).

**Response 200:**
```json
{ "preapproval_id": "...", "init_point": "https://www.mercadopago.com.br/..." }
```
(`preapproval_service.py:78`.) `init_point` é o link que o lojista abre para assinar.
Depois de assinar, o Mercado Pago o devolve para `{FRONTEND_URL}/dashboard` (`back_url`,
`preapproval_service.py:48`).

Efeito no banco: grava/atualiza `gateway.assinaturas` com `status = 'PENDENTE'`,
`vence_em` em 30 dias e `carencia_ate` 5 dias depois disso
(`preapproval_service.py:60-75`; `DIAS_CARENCIA = 5` em `:26`). O `ON CONFLICT
(empresa_id) DO UPDATE` significa que chamar de novo **substitui** a assinatura
existente do tenant.

---

### ⚠️ Cancelar assinatura
```http
DELETE /plataforma/tenants/{empresa_id}/assinatura
```
`plataforma.py:425-430`. Sem corpo.

> **Irreversível pela API.** O cancelamento vai para o Mercado Pago
> (`PUT /preapproval/{id}` com `status: "cancelled"`, `preapproval_service.py:90-94`)
> e marca `status = 'CANCELADA'` localmente. Não há rota de "reativar assinatura":
> o caminho de volta é gerar uma assinatura nova, com link novo, que o lojista
> precisa aceitar de novo.

Cancelar **não suspende o tenant** — quem suspende no prazo é a régua
(`plataforma.py:427`).

**Response 200:** `{ "cancelada": true }`
**404:** `"Tenant sem assinatura"` (o tenant não tem `mp_preapproval_id`).

---

## Rotas públicas (sem JWT)

Estas duas estão no `router_publico` (`plataforma.py:438`), que **não** tem
`require_super_admin`. Ambas são registradas em `api-gateway/main.py:100`.

### Webhook do Mercado Pago
```http
POST /plataforma/webhook/mercadopago
```
`plataforma.py:441-477`. **Sem autenticação de usuário.**

**Request Body:** o payload do Mercado Pago. O router lê `id` (ou `data.id`) como
id do evento e `type` como tipo (`plataforma.py:450-451`).

**Responde sempre 200**, inclusive para evento repetido ou ignorado — 4xx faria o
Mercado Pago reenviar para sempre (`plataforma.py:448`).

| Situação | Response |
|----------|----------|
| Evento sem id | `{"ignorado": "evento sem id"}` |
| Evento já visto (idempotência por `evento_id` em `gateway.webhooks_plataforma`) | `{"ja_processado": true}` |
| `type == "subscription_preapproval"` com `data.id` | `{"processado": true, "empresa_id": 12}` |
| Qualquer outro tipo | `{"processado": false, "tipo": "..."}` |

Um pagamento confirmado empurra `vence_em` em 30 dias, zera
`somente_leitura_desde`, põe `status = 'ATIVA'` e **reativa os usuários do tenant**
(`preapproval_service.py:108-134`) — quem pagou volta a operar no request seguinte,
mesmo se estava suspenso.

O router não valida assinatura nem origem do webhook — a proteção que existe no
código é a idempotência por `evento_id`. O nginx também não filtra: `location /api/`
é genérico, sem regra própria para esta rota (`frontend/nginx.conf:25-44`).

A CONFIRMAR: se há regra de origem na frente, no Cloudflare — isso não está no
repositório e não dá para verificar a partir do código.

---

### Varredura diária de vencimentos (régua)
```http
POST /plataforma/jobs/regua
```
`plataforma.py:480-494`. Sem corpo.

**Header obrigatório:**
```http
X-Job-Token: <PLATAFORMA_JOB_TOKEN>
```
Comparado contra `settings.PLATAFORMA_JOB_TOKEN` (`api-gateway/config.py:63`).
**Token ausente, errado, ou variável não configurada → `403 "Token de job inválido"`**
(`plataforma.py:492-493`): com a variável vazia a rota fica fechada para todo mundo,
não aberta.

Chamada pelo cron do host, não por um scheduler residente.

**Response 200:**
```json
{ "somente_leitura": [3, 7], "suspensos": [11], "auditoria_podada": 412 }
```

O que executa (`preapproval_service.aplicar_regua`, `preapproval_service.py:137-191`):
1. passou de `carencia_ate` → `somente_leitura_desde = hoje`, `status = 'INADIMPLENTE'` (pula quem está `CANCELADA`);
2. `DIAS_SOMENTE_LEITURA = 7` dias assim (`preapproval_service.py:27`) → `status = 'SUSPENSA'` e `usuarios.ativo = false`;
3. ⚠️ **apaga** de `gateway.auditoria_registros` e `gateway.auditoria` tudo com mais de **180 dias** (`preapproval_service.py:171-180`).

> ⚠️ **A poda é irreversível e apaga trilha de auditoria.** Um snapshot podado
> deixa de ser reversível pela rota de reverter. A retenção de 180 dias está
> escrita no SQL, não em variável de ambiente: mudar exige alterar o código.

---

## 🚨 Códigos de erro

| Código | Onde aparece |
|--------|--------------|
| 401 | Sem token / token inválido |
| 403 | Papel diferente de `SUPER_ADMIN` (`oauth2.py:161-165`); `X-Job-Token` inválido na régua (`plataforma.py:492-493`) |
| 404 | Registro de auditoria inexistente; tenant sem assinatura |
| 409 | E-mail de admin já cadastrado; snapshot já revertido; registro de origem sumiu ou mudou depois |
| 422 | Falta `empresa`/`admin`; falta `email_pagador`; campo desconhecido no PATCH de plano; reversão de INSERT |

Erro vindo do serviço empresas é **repassado com o status original**, não
convertido em 200 (`_repassar`, `plataforma.py:65-69`).

---

## 📚 Documentação relacionada

- [Arquitetura da Plataforma](../03-arquitetura/plataforma.md) — o porquê das decisões
- [Mapeamento Completo de Rotas](./mapeamento-rotas.md)
- [Guia de Autenticação](./guia-autenticacao.md)

Os três arquivos existem no repositório — conferido em `docs/03-arquitetura/` e
`docs/10-api-reference/`.

---

**Fonte primária:** `api-gateway/routers/plataforma.py` (494 linhas)
**Projeto:** Runas
