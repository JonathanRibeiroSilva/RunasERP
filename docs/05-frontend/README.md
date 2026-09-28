# Documentação do Frontend — Runas

> Índice da pasta `docs/05-frontend/`. Todo número, porta e comando abaixo foi lido de `frontend/` em 2026-09-25; onde não deu para confirmar, está marcado como **A CONFIRMAR** em vez de preenchido.

**Última atualização**: 25 de Setembro de 2026

---

## Índice da pasta

### Estado atual (leia primeiro)

- **[Estado Atual do Frontend](./frontend-current-state.md)** — retrato factual medido em `frontend/src`: clientes HTTP, React Query, error boundaries, god components.
- **[Architectural Debt Log](./frontend-architectural-debt-log.md)** — dívidas C1–C6 / H1–H7 registradas a partir do AUD-2026-06-29.
- **[Auditoria AUD-2026-06-29](./audits/AUD-2026-06-29.md)** e **[planos de fase](./plans/)** — histórico. Descrevem o estado de junho/2026, não o de hoje.

### Setup

- **[Pré-requisitos](./setup/prerequisites.md)**
- **[Docker](./setup/docker.md)**
- **[Docker Quick Start](./setup/docker-quick-start.md)**

### Design e UI

- **[Design](./design/design.md)** — guia de design e padrões visuais
- **[Componentes](./design/componentes.md)** — biblioteca de componentes
- **[Cores e Tipografia](./design/cores-tipografia.md)** — paleta e fontes
- **[Layouts](./design/layouts.md)** — estruturas de layout

> ⚠️ Os valores de cor em `design/cores-tipografia.md` (`$background: #0F1115`, `$primary: #3B82F6`) **divergem** do código em `frontend/src/styles/variables.scss` (`$background: #080A0F` linha 9, `$primary: #0EA5E9` linha 15, `$secondary: #6366F1` linha 22). A fonte da verdade é o `.scss`. **A CONFIRMAR**: qual dos dois deve ser corrigido — não foi decidido aqui.

### OAuth e autenticação

- **[OAuth Summary](./oauth/oauth-summary.md)** — implementação de Google e Microsoft no gateway e no frontend

### Features

- **[Categorias](./features/categorias.md)** — gestão de categorias de produtos

### Guias

- **[API Examples](./guias/api-examples.md)** — exemplos de uso da API

### Deploy

- **[Production Checklist](./deployment/production-checklist.md)**
- **[Deploy](../06-operacao/deploy.md)** e **[Runbook de Produção](../06-operacao/runbook-producao.md)** — processo real de deploy da stack

---

## Stack

Versões lidas de `frontend/package.json` (declaradas com `^`, ou seja, o instalado pode ser maior dentro do mesmo major).

| Categoria | Tecnologia | Versão declarada |
|-----------|-----------|------------------|
| Framework | React / React DOM | `^19.3.0` |
| Linguagem | TypeScript | `^5.2.2` |
| Build | Vite | `^8.3.1` |
| Plugin React | @vitejs/plugin-react | `^6.1.1` |
| Roteamento | react-router-dom | `^7.18.4` |
| Estado de servidor | @tanstack/react-query | `^5.103.2` |
| UI | react-bootstrap | `^2.9.1` |
| Estilo | bootstrap / sass | `^5.3.2` / `^1.105.0` |
| Formulários | react-hook-form + @hookform/resolvers | `^7.88.0` / `^5.9.1` |
| Validação | zod | `^4.6.5` |
| HTTP | axios | `^1.20.0` |
| Notificações | react-toastify | `^11.1.0` |
| Ícones | react-icons | `^5.7.0` |
| Gráficos | chart.js / react-chartjs-2 | `^4.4.1` / `^5.2.0` |
| Datas | date-fns | `^4.4.0` |
| Testes | vitest + @testing-library/react + jsdom | `^5.0.1` / `^16.3.3` / `^30.1.1` |

O projeto **não usa Material-UI** — nunca esteve em `package.json`.

---

## Estrutura de pastas

Lida de `frontend/` em 2026-09-25.

```
frontend/
├── public/                     # favicons + test.html
├── src/
│   ├── components/
│   │   ├── clientes/  common/  estoque/  financeiro/
│   │   ├── layout/    produtos/  vendas/
│   │   └── common/{ErrorBoundary,MaskedInput,Modal,
│   │                ResponsiveCard,ResponsiveContainer,ResponsiveTable}
│   ├── pages/                  # 13 pastas, capitalizadas:
│   │   ├── Auth/  Clientes/  Configuracoes/  Dashboard/  Estoque/
│   │   ├── Financeiro/  Login/  LojaOnline/  LojaOnlinePublico/
│   │   └── Perfil/  Plataforma/  Produtos/  Vendas/
│   ├── services/
│   │   ├── api/                # axios.ts, apiPublica.ts + 8 serviços de domínio
│   │   └── auth/               # authService.ts, tokenService.ts
│   ├── hooks/                  # 10 hooks (8 de React Query + useAuth, useCarrinho)
│   ├── contexts/  types/  utils/  styles/  img/  test/
│   ├── config/                 # env.ts, host.ts (painel x lojista por hostname)
│   ├── App.tsx                 # tabela de rotas (lazy só nas 2 páginas da Plataforma)
│   └── main.tsx                # entry point + QueryClientProvider
├── Dockerfile                  # build + nginx (EXPOSE 80)
├── Dockerfile.dev              # vite dev (EXPOSE 3000)
├── index.html
├── package.json
├── tsconfig.json
└── vite.config.ts
```

Não existem `src/assets/`, `components/forms/` nem `components/loja/`. Os arquivos `docker-compose*.yml` ficam na **raiz do repositório**, não em `frontend/`.

---

## Quick Start

### Local, sem Docker

```bash
cd frontend
npm install
cp .env.example .env.local     # ver o cabeçalho do .env.example
npm run dev

# Acesse: http://localhost:3000
```

A porta 3000 vem de `frontend/vite.config.ts` (`server.port: 3000`, `preview.port: 3000`) — não é a 5173 padrão do Vite.

### Com Docker

```bash
# Na raiz do repositório
docker compose -f docker-compose.dev.yml up -d frontend-dev

# Acesse: http://localhost:3000
```

O serviço de desenvolvimento chama-se `frontend-dev` (`docker-compose.dev.yml:527`, mapeamento `3000:3000`); em produção é `frontend-prod` (`docker-compose.prod.yml:510`), servido por nginx na porta 80 dentro do container.

Guia completo: [Setup com Docker](./setup/docker.md)

---

## Autenticação

O frontend usa **OAuth2 (Google e Microsoft) com JWT**.

### Armazenamento de tokens

Os tokens vivem em **cookies HTTP-only**, emitidos e limpos pelo backend. O frontend nunca os lê:

- `services/api/axios.ts:23` — `withCredentials: true`; o navegador envia os cookies automaticamente.
- `services/auth/tokenService.ts` — inteiro marcado como DEPRECATED: `getAccessToken()` e `getRefreshToken()` retornam `null`, os setters só emitem `console.warn`, e `clearTokens()` apenas remove chaves de `localStorage` legadas.
- Em um 401 que não seja de `/auth/login`, `/auth/register` ou `/auth/me`, o interceptor de response limpa o legado e redireciona para `/login` (`axios.ts:60-82`).

**A CONFIRMAR**: tempos de expiração de access e refresh token — são definidos no backend, não no frontend, e não foram lidos aqui.

Detalhes do fluxo: [OAuth Summary](./oauth/oauth-summary.md)

---

## Contrato do cliente HTTP

Dois comportamentos de `services/api/axios.ts` valem para qualquer tela nova.

### Idempotency-Key nas escritas

`axios.ts:42-44` gera um `Idempotency-Key` (via `crypto.randomUUID()`) para todo `POST`, `PUT`, `PATCH` e `DELETE`, usando `??=` para **não** regerar a chave em um reenvio — chave nova a cada passagem seria uma operação nova aos olhos do gateway. O gateway reserva a chave no Redis antes de encaminhar a escrita (`api-gateway/proxy/idempotency.py`), então um duplo-clique em "finalizar pedido" recebe a resposta da primeira venda em vez de criar uma segunda. `GET`/`HEAD`/`OPTIONS` não recebem chave.

### Retry de janela de deploy

`axios.ts:97-110` repete a requisição em `502`, `503` e `504` — **apenas** para `GET`, `HEAD` e `OPTIONS` — até 3 vezes, com espera de 1s, 2s e 3s. Cobre os segundos em que um deploy troca o container do gateway. Escritas ficam de fora de propósito: elas já carregam chave de idempotência, mas uma chave reservada cuja primeira tentativa ainda está em voo responde 409, e o retry mostraria esse 409 no lugar do resultado real.

---

## Módulos e seu estado

Medido por LOC das páginas em `frontend/src/pages/`.

| Módulo | Páginas | Estado |
|--------|---------|--------|
| Loja Online pública | `LojaOnlinePublico/` | Implementada — inclui `CheckoutPage.tsx` com 1.507 LOC, o maior arquivo do frontend |
| Estoque | `Estoque/EstoquePage.tsx` (336 LOC), `EstoqueDetalhePage.tsx` (239 LOC) | Implementado |
| Plataforma | `Plataforma/PlataformaDashboard.tsx` (`/plataforma`), `PlataformaPage.tsx` (`/plataforma/tenants`), `TenantDetalhe.tsx` | Implementado — visão geral, administração de tenants e assinaturas |
| Vendas | `Vendas/VendasPage.tsx` (47 LOC) | Stub |
| Financeiro | `Financeiro/FinanceiroPage.tsx` (47 LOC) | Stub |

Coerente com o stub: `services/api/` não tem `vendasApi.ts` nem `financeiroApi.ts`.

### Plataforma

O módulo de administração multi-tenant tem documentação própria fora desta pasta:

- **[Arquitetura da Plataforma](../03-arquitetura/plataforma.md)**
- **[API da Plataforma](../10-api-reference/plataforma-api.md)**

No frontend: `pages/Plataforma/` (páginas, schemas Zod e `__tests__/`), `hooks/usePlataforma.ts`, `services/api/plataformaApi.ts` e `config/host.ts`.

Rotas: `/plataforma` é a visão geral (`PlataformaDashboard`) e `/plataforma/tenants` a lista de lojistas (`PlataformaPage`: provisionar, plano, suspender, cobrança, auditoria). As duas são `lazy()` e exigem `SUPER_ADMIN`; no `Sidebar` o item "Plataforma" é um submenu com esses dois subitens.

O painel e o ERP dos lojistas saem do **mesmo bundle** e do mesmo container; quem decide qual aplicação monta é o hostname. `config/host.ts` compara o primeiro label de `window.location.hostname` com `VITE_HOST_PLATAFORMA` (padrão `admin`), e `escolherPorta()` mostra a tela "Endereço errado" (sem redirect: o cookie de sessão é host-only) para o SUPER_ADMIN fora do host do painel ou para outro papel dentro dele. `/perfil` vale nos dois lados. Em produção, fora do host do painel, as rotas `/plataforma*` nem são registradas (em dev, em `localhost`, continuam), e o `nginx.conf` devolve 404 em `/plataforma` para host que não comece com `admin.`. Em dev as duas aplicações convivem em `localhost`; `admin.localhost:3000` exercita o caminho de produção. A separação é só do frontend: `/api/plataforma/*` responde nos dois hosts, protegido por `require_super_admin`. Em produção desde 2026-09-28 (o PR #113 chegou à `main` pelo PR #114).

---

## Design System

Fonte da verdade: `frontend/src/styles/variables.scss`. É **dark-first**.

```scss
// Base (variables.scss:9-12)
$background: #080A0F;
$surface: #10141D;
$surface-hover: #171C28;
$surface-elevated: #1A202C;

// Primary — cyan/azul elétrico (:15-17)
$primary: #0EA5E9;
$primary-hover: #38BDF8;
$primary-active: #0284C7;

// Secondary — índigo (:22-23)
$secondary: #6366F1;
$secondary-hover: #818CF8;

// Texto (:28-31)
$text-primary: #FFFFFF;
$text-secondary: #94A3B8;
$text-tertiary: #64748B;

// Semânticas (:34-47)
$success: #10B981;
$warning: #F59E0B;
$error:   #EF4444;
$info:    #3B82F6;
```

Tipografia (`variables.scss:66-82`):

```scss
$font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
$font-family-monospace: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;

$font-size-base: 0.9375rem;  // 15px
$font-size-sm:   0.875rem;   // 14px
$font-size-lg:   1.0625rem;  // 17px
$font-size-3xl:  2rem;       // 32px
```

As duas famílias são carregadas do Google Fonts por um `@import url(...)` no topo de `src/styles/global.scss` (linha 3: `https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap`) — e **não** por `<link>` no `index.html`, que só declara favicons, viewport, description e o `<script>` de `/src/main.tsx`. Como é um `@import` de CSS dentro do bundle, o download das fontes só começa depois que a folha de estilo é baixada; até lá vale o fallback (`-apple-system`, `Segoe UI`, `Roboto`).

Detalhes: [Design](./design/design.md) · [Cores e Tipografia](./design/cores-tipografia.md) (ver a ressalva no índice acima).

---

## Testes

Scripts reais de `frontend/package.json`:

```bash
npm run test            # vitest
npm run test:watch      # vitest --watch
npm run test:coverage   # vitest --coverage
```

Não existe script `test:e2e`.

Os testes ficam em pastas `__tests__/` ao lado do código. Os 10 arquivos `*.test.ts` de hoje:

```
components/layout/Sidebar/__tests__/podeVer.test.ts
config/__tests__/host.test.ts
pages/Configuracoes/__tests__/{empresaSchema,integracoesSchema,usuarioSchema}.test.ts
pages/Plataforma/__tests__/{assinaturaSchema,resumirTenants,tenantSchema}.test.ts
services/api/__tests__/axios.test.ts
utils/__tests__/errorLogger.test.ts
```

O setup global fica em `src/test/setup.ts`.

---

## Build e deploy

```bash
npm run build     # tsc && vite build -> dist/
npm run preview   # serve o build em :3000
npm run lint      # eslint, --max-warnings 115
npm run format    # prettier
```

A imagem de produção (`frontend/Dockerfile`) faz o build em `node:22-alpine` e serve `dist/` com `nginx:alpine` na porta 80. As variáveis `VITE_*` são embutidas no bundle **em tempo de build**; os build args ficam em `docker-compose.build.yml`.

Checklist: [Production Checklist](./deployment/production-checklist.md) · Processo: [Deploy](../06-operacao/deploy.md)

---

## Variáveis de ambiente

Lidas de `frontend/.env.example`. Sob Docker elas **não** vêm desse arquivo: vêm da seção `environment:` do compose.

```env
VITE_API_URL=/api                 # /api sob Cloudflare; http://localhost:8000 direto no backend
VITE_API_TIMEOUT=30000
VITE_USE_PROXY=true               # true = Vite faz proxy de /api; false = proxy externo

VITE_APP_NAME=Runas ERP
VITE_APP_VERSION=1.0.0

VITE_ENABLE_DEVTOOLS=true
VITE_ENABLE_ANALYTICS=false

VITE_TOKEN_REFRESH_THRESHOLD=300000

VITE_GOOGLE_CLIENT_ID=your-google-client-id.apps.googleusercontent.com
VITE_MICROSOFT_CLIENT_ID=your-microsoft-client-id
VITE_MICROSOFT_TENANT_ID=common
VITE_OAUTH_REDIRECT_URI=http://localhost:3000/auth/callback
```

---

## Documentação relacionada

- **[API Reference](../10-api-reference/README.md)**
- **[Regras de Negócio](../11-regras-negocio/README.md)**
- **[Arquitetura](../03-arquitetura/README.md)**
- **[Como contribuir](../../.github/CONTRIBUTING.md)**
