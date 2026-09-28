# Plano de controle da plataforma (SaaS)

Dois produtos convivem neste repositório:

- **O ERP** — o que cada lojista (tenant) usa: produtos, estoque, vendas, financeiro.
- **O plano de controle** — o que o **dono da plataforma** usa para administrar os
  lojistas: provisionar, suspender, cobrar, auditar, exportar.

Este documento descreve o segundo. Ele vive quase inteiro em
`api-gateway/routers/plataforma.py` (494 linhas) e num punhado de rotas do serviço
`empresas`. Contratos de request/response não estão aqui — ver
[Ponteiros](#ponteiros).

---

## 1. SUPER_ADMIN: papel disjunto, sem tenant

`SUPER_ADMIN` é um valor do `RoleEnum` (`api-gateway/models/usuario.py:15`) e **não
herda de `ADMIN`**. A checagem é igualdade estrita:

```python
# api-gateway/auth/oauth2.py:161-165
if current_user.role != RoleEnum.SUPER_ADMIN:
    raise HTTPException(403, "Acesso negado: apenas a administração da plataforma")
```

`require_admin` (`oauth2.py:130`) faz a comparação simétrica contra `RoleEnum.ADMIN`.
Consequência prática: **um SUPER_ADMIN não passa em nenhuma rota de ADMIN, e um ADMIN
não passa em nenhuma rota de plataforma.** Não há escalonamento por herança.

O super admin também **não tem tenant**: `usuarios.empresa_id` é anulável desde
`api-gateway/alembic/versions/20260828_100000_super_admin.py:25-26`, e o comentário da
coluna diz `None = SUPER_ADMIN, sem tenant` (`models/usuario.py:32`).

Isso não é cosmético. O `ServiceProxy` deriva o `X-Empresa-Id` do usuário autenticado
(`api-gateway/proxy/service_proxy.py:113-117`); sem `empresa_id`, o header simplesmente
não é injetado, e os serviços a jusante são *fail closed* — `exigir_tenant` devolve
400 sem ele (`services/empresas/routers/empresas.py:27-41`). Um super admin que caia
numa rota de tenant leva 400, nunca um acesso cross-tenant silencioso.

O super admin é criado pelo seed no startup do gateway, a partir de
`SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD` (`api-gateway/seed.py:93-116`). A guarda é
`if super_email and super_password` (`seed.py:95`): faltando **qualquer uma** das duas,
o seed apenas loga `seed.super_admin_skipped` com o motivo e não cria ninguém
(`seed.py:112-116`).

---

## 2. As rotas

Todas montadas em `api-gateway/routers/plataforma.py`, registradas em
`api-gateway/main.py:99-101` **antes do `proxy.router`** — o proxy tem catch-all e o
Starlette casa por ordem de registro.

### 2.1 Router protegido — 11 rotas, `require_super_admin` no nível do router

A dependência está no construtor do `APIRouter`, não rota a rota
(`plataforma.py:28-32`): rota nova nasce fechada.

| Método | Rota | Linha | O que faz |
|---|---|---|---|
| GET | `/plataforma/tenants` | :72 | Lista tenants + usuários ativos + assinatura |
| POST | `/plataforma/tenants` | :99 | Provisiona empresa + usuário ADMIN inicial |
| PATCH | `/plataforma/tenants/{id}/suspender` | :158 | Status `SUSPENSA` + desativa os usuários |
| PATCH | `/plataforma/tenants/{id}/reativar` | :163 | Status `ATIVA` + reativa os usuários |
| PATCH | `/plataforma/tenants/{id}/plano` | :185 | Plano e limites |
| GET | `/plataforma/tenants/{id}/auditoria` | :199 | Trilha + snapshots do tenant |
| POST | `/plataforma/auditoria/{registro_id}/reverter` | :239 | Reaplica `dados_antes` |
| GET | `/plataforma/tenants/{id}/exportar` | :336 | Dump JSON do tenant (streaming) |
| GET | `/plataforma/tenants/{id}/dumps` | :390 | Lista backups (hoje sempre vazio) |
| POST | `/plataforma/tenants/{id}/assinatura` | :410 | Cria preapproval no MP |
| DELETE | `/plataforma/tenants/{id}/assinatura` | :425 | Cancela no MP e marca local |

### 2.2 Router público — 2 rotas, sem sessão de usuário

`router_publico` é um `APIRouter` separado **de propósito** (`plataforma.py:433-438`):
webhook e cron não têm usuário logado, então não podem herdar `require_super_admin`.

- `POST /plataforma/webhook/mercadopago` (`:441`) — confirmação de mensalidade.
  Idempotente pelo id do evento contra `gateway.webhooks_plataforma` (`:455-470`);
  evento repetido responde **200**, porque 4xx faria o MP reenviar para sempre (`:448`).
- `POST /plataforma/jobs/regua` (`:480`) — varredura diária. Não é público de fato:
  exige `X-Job-Token` igual a `PLATAFORMA_JOB_TOKEN`, e **rejeita com 403 se a env
  estiver vazia** (`:492`) — é a única das quatro validações de segredo em header
  entre gateway e serviços que é *fail closed*; as outras três
  (`SERVICO_INTERNO_TOKEN`, `PLATAFORMA_INTERNO_TOKEN` e `REGISTRO_INTERNO_TOKEN` —
  `api-gateway/routers/auth_cliente.py:600-611`) são fail-open. (Fora da conta fica
  a assinatura HMAC do webhook do MP de cada lojista, em vendas: usa o segredo do
  lojista, não um nosso, e sem segredo configurado ou sem `x-signature` a
  notificação ainda passa — `services/vendas/routers/webhook.py:36-43`.)

---

## 3. A prova de origem — o mecanismo

Esta é a parte que não se deduz lendo o código rápido.

### 3.1 O problema

O serviço `empresas` **não tem noção de papel**. Ele não valida JWT, não conhece
`SUPER_ADMIN`. Para ele, autorização de plataforma é um header: `X-Plataforma: 1`.

Isso era *afirmação sem prova*. Quem alcançasse a porta 8007 do container `empresas`
mandava o header e virava administrador da plataforma — podia listar todos os tenants
e apagar empresa. O próprio docstring registra o furo
(`services/empresas/routers/empresas.py:55-59`).

O `SERVICO_INTERNO_TOKEN` **não fecha isso**: ele é o *mesmo valor nos 8 containers*
(`.env.example:132-136`), então prova apenas "a chamada veio de algum dos 8". Para
rotas que apagam tenant, isso não basta.

### 3.2 O carimbo (gateway)

Toda chamada do router de plataforma ao serviço `empresas` passa por `_empresas()`
(`plataforma.py:40-62`), que monta **dois** carimbos:

```python
# api-gateway/routers/plataforma.py:54-58
headers = auth_interno(HEADERS_PLATAFORMA)   # X-Plataforma: 1 + X-Servico-Interno-Token
if settings.PLATAFORMA_INTERNO_TOKEN:
    headers["X-Plataforma-Token"] = settings.PLATAFORMA_INTERNO_TOKEN
if tenant_id is not None:
    headers["X-Empresa-Id"] = str(tenant_id)
```

`auth_interno()` (`api-gateway/interno.py:17-23`) acrescenta
`X-Servico-Interno-Token`. O `X-Plataforma-Token` vem de `PLATAFORMA_INTERNO_TOKEN`,
um segredo de **escopo menor: só o gateway e o empresas** — confirmado nos dois
`config.py` (`api-gateway/config.py:76-80`, `services/empresas/config.py:26-31`) e no
compose, onde apenas `api-gateway-prod` e `empresas-prod` recebem a variável
(`docker-compose.prod.yml:297` e `:373`).

O ponto do desenho: esse header só é escrito **dentro deste router**, e o router só
executa **depois** do `require_super_admin`. O header é, portanto, prova de que a
requisição atravessou a checagem de papel.

### 3.3 A validação (empresas)

Do outro lado, `exigir_plataforma` (`services/empresas/routers/empresas.py:44-89`)
roda em três etapas:

1. `x_plataforma != "1"` → **403** (`:61-65`).
2. Se `PLATAFORMA_INTERNO_TOKEN` estiver vazio **ou** o header não vier: loga
   `plataforma.sem_segredo` e **deixa passar** (`:69-80`).
3. Comparação com `secrets.compare_digest` em bytes; diferente → **403** (`:82-89`).

> **Fail-open declarado.** A etapa 2 é uma brecha deliberada e temporária, marcada com
> `# ponytail:` no código (`empresas.py:69-73`): fechar junto com o deploy tiraria o
> super admin do ar, porque as rotas de plataforma são *todas* guardadas por aqui e o
> gateway só carimba depois que a env nova chegar ao container.
> **Enquanto `PLATAFORMA_INTERNO_TOKEN` não estiver setado nos dois containers, o
> `X-Plataforma: 1` sozinho continua valendo.** O critério de fechamento está escrito
> no próprio comentário: medir `plataforma.sem_segredo` em produção; zerado, troca-se
> o `log.warning` pelo mesmo `raise` do bloco seguinte — uma linha.

Antes ainda, o middleware `validar_token_interno` (`services/empresas/main.py:56`,
implementado em `services/empresas/interno.py:50-83`) valida o
`X-Servico-Interno-Token` em tudo exceto `/health` (`interno.py:31`) — e tem o
**mesmo fail-open**, pelo mesmo motivo (`interno.py:58-72`).

### 3.4 O que acontece se alguém chamar o empresas direto

Depende de onde essa pessoa está e do estado dos segredos:

| Origem | Hoje, em produção | Com os dois segredos setados |
|---|---|---|
| Internet | Não alcança: o `docker-compose.prod.yml` **não publica porta nenhuma** (nenhuma chave `ports:` no arquivo; o tráfego entra pelo túnel, ver `docker-compose.prod.yml:10`) | idem |
| Rede Docker, sem headers | passa (fail-open do `interno.py`) | 403 no middleware |
| Rede Docker, com `X-Plataforma: 1` e sem `X-Plataforma-Token` | **passa** — vira plataforma | **403** em `exigir_plataforma` |
| Outro container da malha (tem o `SERVICO_INTERNO_TOKEN`, não tem o de plataforma) | passa | **403** — é exatamente o caso que o segredo de escopo menor existe para cobrir |

Em desenvolvimento a porta 8007 está publicada, mas só em loopback:
`127.0.0.1:8007:8007` (`docker-compose.dev.yml:490-491`).

### 3.5 Os headers, lado a lado

| Header | Segredo | Escopo | Prova o quê | Fail-open? |
|---|---|---|---|---|
| `X-Servico-Interno-Token` | `SERVICO_INTERNO_TOKEN` | os 8 containers | "veio de dentro da malha" — não diz *qual* serviço | Sim (`services/empresas/interno.py:65-72`) |
| `X-Plataforma-Token` | `PLATAFORMA_INTERNO_TOKEN` | gateway + empresas | "veio do router `/plataforma`, depois do `require_super_admin`" | Sim (`empresas.py:69-80`) |
| `X-Empresa-Id` | — (sem segredo próprio) | injetado pelo gateway | "o tenant do portador é este" | N/A — *fail closed* no consumidor (`empresas.py:27-41`) |
| `X-Job-Token` | `PLATAFORMA_JOB_TOKEN` | gateway + cron do host | "é o cron diário" | **Não** (`plataforma.py:492`) |

`X-Empresa-Id` é ortogonal ao resto: ele diz *de quem é o dado*, o
`X-Plataforma-Token` diz *quem está mandando*. As rotas de plataforma do `empresas`
que também tocam um tenant específico precisam dos dois — por isso `_empresas()`
aceita `tenant_id` (`plataforma.py:40-46`): sem o `X-Empresa-Id`, o `DELETE` da
compensação de rollback levava 400 silencioso e deixava tenant órfão.

### 3.6 O gateway apaga headers forjados

Antes de repassar qualquer request, o `ServiceProxy` remove do request do cliente os
cinco headers de contexto — em minúsculas, porque as chaves de `request.headers` vêm
assim (`api-gateway/proxy/service_proxy.py:165-171`):

```python
for interno in ("x-empresa-id", "x-cliente-id", "x-plataforma",
                "x-servico-interno-token", "x-plataforma-token"):
    headers.pop(interno, None)
```

Só depois é que o gateway carimba os seus (`service_proxy.py:173-176`). Um cliente que
mande `X-Plataforma: 1` pela internet tem o header descartado no gateway.

### 3.7 Rotas do serviço `empresas` guardadas por `exigir_plataforma`

Três, todas em `services/empresas/routers/empresas.py`:

- `POST /empresas` (`:101-110`) — criar empresa
- `PATCH /empresas/{id}/plano` (`:273-282`) — plano, limites e status
- `GET /empresas/plataforma/todas` (`:290-297`) — "o único ponto cross-tenant do serviço"

As demais rotas do serviço usam `exigir_tenant` e são do lojista — com uma
exceção: `GET /empresas/publico/{slug}` (`:206-215`) não tem guarda nenhuma. É a
rota do catálogo público, chamada sem usuário logado; ela só devolve
`EmpresaPublicInfo` e só se a empresa estiver ativa e com catálogo ligado.

---

## 4. Modelo de confiança, em uma frase por ator

- **Lojista (ADMIN/OPERADOR)** — chega pelo gateway com JWT; o gateway deriva o
  `X-Empresa-Id` do usuário; vê só o próprio tenant (`validar_tenant`,
  `empresas.py:92-98`). Nunca recebe `X-Plataforma`.
- **Dono da plataforma (SUPER_ADMIN)** — chega pelo gateway com JWT; passa por
  `require_super_admin`; o router carimba `X-Plataforma` + `X-Plataforma-Token`. Não
  tem `empresa_id`, então nenhuma rota de tenant funciona para ele.
- **Serviço da malha** — tem o `SERVICO_INTERNO_TOKEN`; pode falar com os outros
  serviços; **não** pode agir como plataforma (quando o segredo estiver ativo).
- **Cron do host** — só o `POST /plataforma/jobs/regua`, com `X-Job-Token`.
- **Mercado Pago** — só o `POST /plataforma/webhook/mercadopago`, sem segredo e sem
  verificação de assinatura: o `preapproval_id` vem do corpo do request
  (`plataforma.py:472`), não de uma consulta ao MP. O que existe é a idempotência por
  `evento_id` e o fato de a rota só mexer em assinatura já cadastrada
  (`UPDATE ... WHERE mp_preapproval_id`, `preapproval_service.py:117-125`).

---

## 5. O guard do frontend

`SUPER_ADMIN` não tem `empresa_id`, então **toda** tela de tenant do React consultaria
uma empresa que ele não tem. Por isso o painel da plataforma e o ERP dos lojistas são
tratados como **duas aplicações servidas pelo mesmo bundle**, separadas pelo hostname.

### 5.1 Dois hosts, um bundle, um container

`frontend/src/config/host.ts` lê `window.location.hostname`: se o primeiro rótulo for
`VITE_HOST_PLATAFORMA` (padrão `admin`), o bundle monta o painel
(`ehPainelPlataforma`, `host.ts:16-19`). Não há segunda imagem: `admin` e `app`
apontam para o mesmo container `frontend-prod`, cujo nginx tem `server_name _`
(`frontend/nginx.conf:5`) — quem separa é o hostname lido no navegador. O comentário
de ingress do túnel em `docker-compose.prod.yml` já lista
`admin.runaserp.com.br -> http://frontend-prod:80`.

Em dev (`import.meta.env.DEV`) a separação só é aplicada em host `admin.*`
(`separarPorHost`, `host.ts:26`): em `localhost` as duas aplicações convivem, senão o
super admin ficaria trancado fora do próprio painel; `admin.localhost:3000` exercita o
caminho de produção.

### 5.2 Uma porta só: `escolherPorta()`

Em vez de um guard por rota, há **uma porta só**, dentro do `ProtectedRoute`
(`frontend/src/App.tsx:69-78`), que delega a decisão à função pura `escolherPorta()`
(`host.ts:38-56`):

| Situação (com separação por host ativa) | Resultado |
|---|---|
| Super admin fora do host `admin`, ou não-super no host `admin` | `porta-errada` — tela "Endereço errado" com botão Sair |
| Super admin no host certo, em `/plataforma*` ou `/perfil` | `ok` |
| Super admin no host certo, em qualquer outra rota | redireciona para `/plataforma` |
| Não-super no host certo, em `/plataforma*` | redireciona para `/dashboard` (só alcançável em dev; ver abaixo) |
| Não-super no host certo, em qualquer outra rota | `ok` |

O efeito é que **tela nova nasce fechada para quem não é daquele host sem ninguém
precisar lembrar de fechá-la**; `/perfil` vale nos dois lados porque é onde cada um
troca a própria senha.

`porta-errada` é uma **tela** (`PortaErrada`, `App.tsx:83-106`) e não um redirect para o
outro host, por dois motivos: o cookie de sessão é *host-only* (`set_auth_cookies`
não passa `domain=`), então a sessão não iria junto; e mandar o super admin para
`/plataforma` num host que não serve `/plataforma`, e de lá de volta, fecharia um laço
de redirect. O texto da tela depende do host: no `admin`, "Esta conta não administra a
plataforma. Entre pelo endereço do seu ERP."; no host do lojista, só "Esta conta não
tem acesso a este sistema.", sem nomear o painel nem o endereço dele, porque ali o
texto é visível para qualquer conta.

As rotas `/plataforma` e `/plataforma/tenants` têm ainda um
`RoleProtectedRoute requiredRole={['SUPER_ADMIN']}` — o caminho inverso: impedir que
um ADMIN entre no painel. E elas **só são registradas no host do painel**
(`ehPainelPlataforma || !separarPorHost`, `App.tsx:255-280`): no host do lojista não
existem e caem no catch-all, como qualquer endereço que nunca existiu (em dev, em
`localhost`, continuam registradas). O `frontend/nginx.conf:71-76` fecha o mesmo lado no
servidor: `location /plataforma` devolve **404** quando o host não casa `^admin\.`, em vez
do `index.html` com 200 que já contaria que o painel existe.

### 5.3 A separação é só do frontend

Nada mudou no backend: além do bundle, só o nginx do próprio container do frontend
participa (o 404 em `/plataforma`, acima). O `/api` é relativo, então no subdomínio ele é same-origin e o
CORS não entra em jogo; o gateway não tem `TrustedHost` nem checagem de `Origin`.
**`/api/plataforma/*` responde nos dois hosts**, protegido só por
`require_super_admin` (seção 2.1); o comentário em `frontend/nginx.conf:68-70` registra
que separar essa rota exigiria duplicar o bloco `/api/` inteiro. O host `admin` é uma fronteira da interface, não do
servidor.

Produção: o PR que introduziu os dois hosts (#113, commit `4643422`) chegou à
`main` pelo PR #114 (merge `1df3a0f`) e está no ar desde o deploy de 2026-09-28,
que terminou com sucesso. A rota do túnel
`admin.runaserp.com.br -> frontend-prod:80` e um Cloudflare Access (policy Allow por
e-mail) na frente do host `admin` estão configurados **fora do repositório** (painel
da Cloudflare), segundo verificação de 2026-09-28; nada no código comprova isso. O registro condicional das rotas, o 404 do nginx e o
texto novo da tela `PortaErrada` vêm do commit `045c0c0`, que em 2026-09-28 estava no
`Developer` e **ainda não na `main`**.

### 5.4 As telas

As páginas do painel são carregadas com `lazy()` (`App.tsx:28-29`): no host do lojista
nenhuma rota chega a pedir esses chunks. No Sidebar, "Plataforma" é um submenu com
"Visão Geral" (`/plataforma`, com `end`) e "Lojistas" (`/plataforma/tenants`).

- `frontend/src/pages/Plataforma/PlataformaDashboard.tsx` — rota `/plataforma`, visão
  geral: cartões calculados por `resumirTenants()` sobre `useTenants()`
  (`PlataformaDashboard.tsx:22-43`)
- `frontend/src/pages/Plataforma/PlataformaPage.tsx` — rota `/plataforma/tenants`,
  lista de lojistas (provisionar, plano, suspender, cobrança, auditoria), via
  `useTenants()` (`PlataformaPage.tsx:59`)
- `frontend/src/pages/Plataforma/TenantDetalhe.tsx` — abas `auditoria`, `assinatura`,
  `backups` (`TenantDetalhe.tsx:19-24`); `auditoria` e `backups` só consultam a API
  quando a aba está ativa (`:95-96`), `assinatura` é um formulário
- `frontend/src/hooks/usePlataforma.ts` — hooks React Query; toda mutação invalida
  `['plataforma-tenants']` (`usePlataforma.ts:11-17`)
- `frontend/src/services/api/plataformaApi.ts` — camada HTTP

Uma exceção de desenho: a exportação **não** passa por axios. `urlExportar()` devolve
a URL crua (`plataformaApi.ts:60-62`) e o `<a href>` deixa o navegador baixar pelo
cookie de sessão (`TenantDetalhe.tsx:180-184`) — puxar por axios carregaria o tenant
inteiro em memória só para reemitir o mesmo download.

---

## 6. Cobrança: o segundo Mercado Pago

Há **dois** Mercado Pago no sistema, e confundi-los cobra a pessoa errada:

| | Credencial | Quem cobra quem |
|---|---|---|
| Plataforma | `PLATAFORMA_MP_ACCESS_TOKEN` (env) | o dono cobra a mensalidade do lojista |
| Lojista | `vendas.configuracoes_pagamento` (tabela) | o lojista cobra o cliente final |

`api-gateway/services/preapproval_service.py` conhece **só o primeiro**
(`preapproval_service.py:4-9`) e falha alto com `RuntimeError` se a env estiver vazia
(`:32-33`). A assinatura é um *preapproval* recorrente mensal em BRL (`:42-56`),
gravado em `gateway.assinaturas` com `ON CONFLICT (empresa_id) DO UPDATE` (`:61-74`).
Quem abre o link e assina é o lojista, então a `back_url` é `{FRONTEND_URL}/dashboard`
(`:48`), o ERP dele no host `app`. Ela apontava para `/plataforma`, que no host `app`
passou a responder 404 com o commit `045c0c0` (seção 5.2).

---

## 7. Régua de inadimplência

Dois números definem a régua inteira (`preapproval_service.py:26-27`):
`DIAS_CARENCIA = 5`, `DIAS_SOMENTE_LEITURA = 7`.

O ciclo (`aplicar_regua`, `preapproval_service.py:137-191`), rodado pelo cron diário:

1. Vence (`vence_em`) — nada acontece ainda.
2. Passa a carência (`carencia_ate < hoje`) → `somente_leitura_desde = hoje`, status
   `INADIMPLENTE` (`:146-154`).
3. Sete dias em somente leitura → status `SUSPENSA` **e** `usuarios.ativo = FALSE`
   para o tenant (`:156-169`).
4. Pagamento confirmado em qualquer estágio, inclusive suspenso → vencimento empurrado
   30 dias, `somente_leitura_desde = NULL` e usuários reativados
   (`registrar_pagamento`, `:108-134`).

O mesmo job poda auditoria com mais de 180 dias (`:171-180`).

O **corte de escrita** acontece no gateway, não nos serviços:
`InadimplenciaMiddleware` (`api-gateway/middleware/inadimplencia_middleware.py`,
registrado em `main.py:92`) devolve **402** em `POST/PUT/PATCH/DELETE` (`:24`,
`:43-49`) consultando `gateway.assinaturas` localmente — nenhum dos 7 serviços aprende
o que é inadimplência.

Duas decisões importantes:

- **GET sempre passa** (`:36`) — cortar leitura transformaria um atraso de dois dias em
  cancelamento, e o lojista precisa continuar entrando para ver a própria fatura.
- `/auth/`, `/health`, `/plataforma/`, `/docs`, `/openapi.json` ficam liberados (`:27`)
  — sem isso o inadimplente não consegue nem entrar para pagar.

Cache de 60s no Redis, com fallback para consulta direta se o Redis cair (`:29`,
`:79-112`). Tenant sem linha em `gateway.assinaturas` não é bloqueado (`:104-105`).

---

## 8. Auditoria em dois níveis

### Nível 1 — a intenção

`AuditoriaMiddleware` (`api-gateway/middleware/auditoria_middleware.py`, registrado em
`main.py:91`) grava em `gateway.auditoria`: usuário, empresa, método, rota, payload e
status de resposta, para todo `POST/PUT/PATCH/DELETE` (`:20`, `:87-101`). Um arquivo
cobre os 7 serviços porque tudo passa pelo gateway.

- `/auth/login`, `/auth/refresh`, `/auth/register` e `/health` ficam de fora (`:24`) —
  auditar o login gravaria a senha numa tabela que o suporte lê.
- Chaves com `senha`, `password`, `token`, `secret`, `api_key`, `apikey`,
  `authorization` são redigidas recursivamente para `***` (`:28`, `:33-42`).
- Payload acima de 16 KB não é gravado (`:30`).
- Falha na auditoria **nunca** derruba a requisição auditada (`:63-67`).

### Nível 2 — o estado

A função `gateway.auditar_registro()` (`postgres/init-schemas.sql:94-121`) é uma
trigger `AFTER INSERT OR UPDATE OR DELETE` que grava em `gateway.auditoria_registros`
o `to_jsonb(OLD)` e o `to_jsonb(NEW)` — o antes e o depois de cada linha.

A trigger é instalada por
`api-gateway/alembic/versions/20260828_120000_auditoria.py:32-41`, hoje em **uma única
tabela**: `gateway.usuarios` (`:29`). Escopo deliberado, também marcado `# ponytail:`
(`:26-29`): numa VPS de 1 vCPU, ligar tudo antes de medir é apostar contra o disco.
Escalar = nova migration com mais nomes na lista.

> A função e as tabelas nascem no `postgres/init-schemas.sql`, não na migration: sete
> Alembics independentes não têm ordem de boot entre si
> (`20260828_120000_auditoria.py:7-9`).

### É o snapshot que torna a reversão possível

`POST /plataforma/auditoria/{id}/reverter` (`plataforma.py:239-323`) reaplica
`dados_antes` no registro de origem. Seis recusas, todas deliberadas:

- snapshot inexistente → 404 (`:258-259`)
- já revertido → 409 (`:260-261`)
- `dados_antes` vazio, isto é, um INSERT → 422, "apague o registro em vez de reverter"
  (`:262-266`)
- o registro de origem não existe mais → 409 (`:274-275`)
- nada a reverter além do `id` → 422 (`:290-291`)
- **o registro mudou depois da operação** (`atual != dados_depois`) → 409 (`:276-281`).
  Esta é a que importa: aplicar um estado antigo por cima de uma edição posterior
  apagaria silenciosamente o trabalho de outra pessoa.

A escrita usa `jsonb_populate_record` em vez de montar `SET col = (:dados->>'col')`,
porque `->>` devolve texto e atribuir texto a coluna `numeric`/`bool`/`timestamp`
falha; os nomes de coluna vêm do `to_jsonb` da própria trigger, nunca do usuário, e os
valores viajam por bind param (`:284-300`).

Reverter é ele próprio uma escrita auditada: a trigger da tabela de origem grava o
snapshot novo, e o handler insere a linha de quem mandou (`:305-319`). A resposta da
rota de auditoria marca cada registro com `reversivel` para a tela não ter de adivinhar
(`:235`).

---

## 9. Exportação: o único ponto em que o super admin toca dado de negócio

`GET /plataforma/tenants/{id}/exportar` (`plataforma.py:336-387`) atravessa cinco
serviços — empresa, clientes, produtos, estoque, vendas (`FONTES_EXPORTACAO`,
`:327-333`) — carimbando o `X-Empresa-Id` do tenant, e devolve um `StreamingResponse`.

Duas razões para o desenho: é auditado *antes* de começar, com quem exportou, quando e
de quem (`:350-361`); e é streaming porque a VPS tem ~1.1 GB livres e montar o tenant
inteiro em memória derrubaria o gateway junto (`:346-348`).

Não existe rota de restaurar, e `GET /tenants/{id}/dumps` devolve lista vazia com
`"restauracao": "manual"` (`:401-405`). É deliberado: restaurar sobrescreve o tenant
inteiro e descarta tudo posterior ao dump — operação de terminal com revisão humana.
O caminho de suporte do dia a dia é a reversão pontual, que é cirúrgica e auditada
(`:394-399`).

---

## 10. Migrations que criaram isto

Todas em `api-gateway/alembic/versions/`, encadeadas:

| Arquivo | Revision | O que cria |
|---|---|---|
| `20260828_100000_super_admin.py` | `20260828_100000` | valor `SUPER_ADMIN` no `roleenum`; `usuarios.empresa_id` anulável |
| `20260828_120000_auditoria.py` | `20260828_aud_gatewa` | `CREATE TRIGGER trg_auditoria` em `gateway.usuarios` |
| `20260828_130000_assinaturas.py` | `20260828_assin` | `gateway.assinaturas` (unique em `empresa_id`) e `gateway.webhooks_plataforma` (unique em `evento_id`) |

Nota do `20260828_100000_super_admin.py:19-23`: um valor novo de ENUM não pode ser
usado na mesma transação que o adiciona (PG ≥ 12), por isso a migration só declara — o
seed do super admin roda depois, no startup.

---

## 11. O que isto substituiu

`scripts/provisionar-lojista.ps1` batia direto nos containers, em dois endpoints sem
autenticação — o furo que o `POST /plataforma/tenants` fecha
(`api-gateway/routers/plataforma.py:4-6`).

O script ainda existe, mas hoje é só um **wrapper**: monta o payload e chama
`POST /plataforma/tenants` com um token de SUPER_ADMIN; a lógica, incluindo a
compensação, vive no gateway (`scripts/provisionar-lojista.ps1:1-14`).

Essa compensação existe porque **não há transação distribuída** entre gateway e
empresas: se a criação do admin falhar, a empresa recém-criada é apagada
(`plataforma.py:121-132`). Sem isso o provisionamento deixaria empresas órfãs que
ninguém consegue acessar nem recriar, com slug e CNPJ ocupados (`:107-109`).

Detalhe de produto: a loja nasce fechada — `catalogo_ativo` entra como `False` por
padrão, e o lojista abre o catálogo quando terminar de configurar (`:116-117`).

---

## 12. Variáveis de ambiente

| Variável | Onde | Vazio significa |
|---|---|---|
| `SUPER_ADMIN_EMAIL` / `SUPER_ADMIN_PASSWORD` | gateway | nenhum super admin é criado (`seed.py:112-116`) |
| `PLATAFORMA_INTERNO_TOKEN` | gateway **e** empresas, mesmo valor | fail-open: `X-Plataforma: 1` sozinho volta a valer |
| `SERVICO_INTERNO_TOKEN` | os 8 containers, mesmo valor | fail-open na malha inteira |
| `PLATAFORMA_MP_ACCESS_TOKEN` | gateway | `RuntimeError` ao gerar/cancelar assinatura |
| `PLATAFORMA_JOB_TOKEN` | gateway + cron do host | **403** no job — fail closed |

Referência comentada em `.env.example:103-142` e `.env.production.example:184-223`
(o bloco `SUPER_ADMIN` vem antes do de cobrança nos dois arquivos).
O cron sugerido está nos dois arquivos (`.env.example:122`):

```cron
0 3 * * * curl -fsS -X POST -H "X-Job-Token: SEU_TOKEN" http://localhost:8000/plataforma/jobs/regua
```

**Sem esse cron, a régua de inadimplência não roda**: nenhum scheduler residente
executa `aplicar_regua` — é cron do host batendo num endpoint, decisão registrada como
`# ponytail:` em `plataforma.py:488-490` (um beat worker come RAM 24h por dia para
trabalhar 200 ms).

---

## A CONFIRMAR

- **`PLATAFORMA_INTERNO_TOKEN` está de fato preenchido no `.env` da VPS?** Enquanto não
  estiver, a validação da seção 3.3 é fail-open e o modelo de confiança da seção 4 não
  vale na prática. Verificar `plataforma.sem_segredo` nos logs do container
  `erp-empresas-prod`.
- **`SERVICO_INTERNO_TOKEN` idem**, para o middleware de `interno.py`: verificar
  `servico_interno.ausente`.
- **O cron da régua está instalado no host, e por qual endereço?** Não há nada no
  repositório que o instale — só a sugestão comentada no `.env.example`, que aponta para
  `http://localhost:8000`. Em produção o `docker-compose.prod.yml` não publica porta
  nenhuma (`:10`), então esse endereço não existe no host: o cron teria de rodar dentro
  da rede Docker ou o gateway teria de expor uma porta. Não foi possível verificar o
  crontab da VPS daqui.
- **Onde o webhook do MP é registrado na conta do dono da plataforma** (a URL pública
  configurada no painel do Mercado Pago) — não há registro disso no repositório.

---

## Ponteiros

- **Contratos de request/response das rotas** → `docs/10-api-reference/plataforma-api.md`
- **O painel React** → `docs/05-frontend/`
- **Comunicação entre serviços em geral** → `docs/03-arquitetura/comunicacao.md`
- **Persistência e schemas** → `docs/03-arquitetura/persistencia-e-durabilidade.md`
