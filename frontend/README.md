# Frontend — ERP Runas

SPA React do ERP Runas: gestão para pequenos comércios de alimentos e bebidas,
mais a loja online pública dos tenants.

> Todo número, comando, porta e rota abaixo foi lido de `frontend/` e dos
> `docker-compose.*.yml` da raiz em 2026-09-26. O que não deu para confirmar
> está marcado como **A CONFIRMAR** em vez de preenchido.

---

## Stack

Versões lidas de `frontend/package.json`:

| O que | Versão |
|---|---|
| React + React DOM | `^19.3.0` |
| TypeScript | `^5.2.2` |
| Vite | `^8.3.0` (plugin React `^6.1.1`) |
| React Router DOM | `^7.18.4` |
| TanStack React Query | `^5.103.1` (+ devtools) |
| Axios | `^1.20.0` |
| React Hook Form + Zod | `^7.88.0` + `^4.6.5` (`@hookform/resolvers ^5.9.1`) |
| Bootstrap / React Bootstrap / Sass | `^5.3.2` / `^2.9.1` / `^1.104.1` |
| Chart.js + react-chartjs-2 | `^4.4.1` + `^5.2.0` |
| React Icons / React Toastify / react-loading-skeleton | `^5.7.0` / `^11.1.0` / `^3.3.1` |
| date-fns | `^4.4.0` |
| Vitest + Testing Library + jsdom | `^5.0.1` / `@testing-library/react ^16.3.3` / `^30.1.0` |
| ESLint + Prettier | `^10.10.0` / `^3.9.8` |

Não há campo `engines` no `package.json`. As imagens usam **Node 22**
(`Dockerfile` e `Dockerfile.dev`, ambos `node:22-alpine`), então 22 é a única
versão de Node comprovadamente exercitada.

---

## Como rodar

### Docker (o caminho normal em desenvolvimento)

Os composes ficam **na raiz do repositório**, não em `frontend/`. Não existe
`docker-compose.yml` sem sufixo: os arquivos são `docker-compose.dev.yml`,
`docker-compose.prod.yml`, `docker-compose.build.yml` e
`docker-compose.cloudflare.yml`.

```bash
# na raiz do RunasERP
docker compose -f docker-compose.dev.yml up -d frontend-dev

# logs
docker compose -f docker-compose.dev.yml logs -f frontend-dev

# depois de mexer no .env: recriar, não reiniciar (docker restart não relê o .env)
docker compose -f docker-compose.dev.yml up -d --force-recreate frontend-dev
```

Serviço `frontend-dev`, container `erp-frontend-dev`, porta `3000:3000` →
**http://localhost:3000** (`docker-compose.dev.yml:527-571`).

No compose de dev o `VITE_USE_PROXY` é `"true"`: o próprio Vite faz o proxy de
`/api/*` para `http://api-gateway:8000` (`vite.config.ts:79-86`). Não há nginx
no caminho em desenvolvimento.

Antes do primeiro `up`, veja [../QUICK-START.md](../QUICK-START.md): o
`docker-compose.dev.yml` lê variáveis do `.env` da raiz que não têm valor
padrão.

### Local, sem Docker

```bash
cp .env.example .env.local   # o .env.local é lido; via Docker as vars vêm do compose
npm install
npm run dev                  # http://localhost:3000 (vite.config.ts:35-36)
```

O `.env.example` traz `VITE_API_URL=/api` e `VITE_USE_PROXY=true`. Rodando
fora do Docker o alvo `http://api-gateway:8000` não resolve — ajuste
`VITE_API_GATEWAY_TARGET` (lido em `vite.config.ts:82`) ou aponte
`VITE_API_URL` direto para o gateway.

### Produção

A imagem é multi-stage: `npm ci` + `npm run build` em `node:22-alpine`, e o
`dist/` servido por `nginx:alpine` com o `frontend/nginx.conf` em
`/etc/nginx/conf.d/default.conf` (`Dockerfile`). O container expõe a porta 80
**dentro da rede** — `frontend-prod` em `docker-compose.prod.yml:510-534` não
publica porta no host. O único ingress é o Cloudflare Tunnel, que roteia
`app.runaserp.com.br` para `http://frontend-prod:80`
(`docker-compose.prod.yml:545`). Ou seja: em produção não há `http://localhost`
para abrir.

O mesmo container também atende o painel da plataforma: o comentário de ingress
(`docker-compose.prod.yml:546`) lista `admin.runaserp.com.br` →
`http://frontend-prod:80`, e quem separa as duas aplicações é o hostname lido
pelo bundle (`src/config/host.ts`). A rota no túnel e o Cloudflare Access na
frente do `admin` estão configurados fora do repositório (túnel em modo token,
painel da Cloudflare), segundo verificação de 2026-09-28. O código que usa esse
hostname (PR #113) está em produção desde 2026-09-28: chegou à `main` pelo
PR #114 (merge `1df3a0f`).

### Painel da plataforma x ERP do lojista

`src/config/host.ts` compara o primeiro label de `window.location.hostname` com
`VITE_HOST_PLATAFORMA` (default `admin`). No host do painel só o SUPER_ADMIN
entra (`/plataforma`, `/plataforma/tenants`, `/perfil`); fora dele o
SUPER_ADMIN vê a tela "Endereço errado", assim como qualquer outro papel no
host do painel — tela e não redirect, porque o cookie de sessão é host-only.
Em dev (`npm run dev`) as duas aplicações convivem em `localhost:3000`; use
`admin.localhost:3000` para exercitar o caminho de produção. O backend não
separa nada: `/api/plataforma/*` responde nos dois hosts, protegido por
`require_super_admin`.

Detalhes: [docs/05-frontend/setup/docker.md](../docs/05-frontend/setup/docker.md)
e [docs/06-operacao/deploy.md](../docs/06-operacao/deploy.md).

---

## Login

O admin não é hardcoded no frontend: ele é semeado por `api-gateway/seed.py`,
que lê `ADMIN_EMAIL` e `ADMIN_PASSWORD` do ambiente
(`api-gateway/seed.py:27-28`).

- **Desenvolvimento**: `docker-compose.dev.yml:209-210` cai nos defaults
  `admin@runas.com` / `Admin@123` quando as variáveis não estão no `.env`.
- **Produção**: `docker-compose.prod.yml:308-309` usa
  `${ADMIN_EMAIL:?...}` / `${ADMIN_PASSWORD:?...}` — sem valor no `.env` o
  compose falha. O default de dev não vaza para prod.

Se você quer outras credenciais em dev, defina `ADMIN_EMAIL`/`ADMIN_PASSWORD`
no `.env` da raiz antes de rodar o seed.

### Login social (OAuth)

Google e Microsoft têm callbacks implementados
(`src/pages/Auth/GoogleCallback.tsx`, `src/pages/Auth/MicrosoftCallback.tsx`),
rotas `/auth/callback/google` e `/auth/callback/microsoft`. Eles chamam
`/auth/cliente/oauth/*`: é o login do **cliente da loja online**; o `LoginPage`
do operador não tem botão social.
Variáveis: `VITE_GOOGLE_CLIENT_ID`, `VITE_MICROSOFT_CLIENT_ID`,
`VITE_MICROSOFT_TENANT_ID` (default `common`) e `VITE_OAUTH_REDIRECT_URI`
(`.env.example:53-56`).

Como configurar do lado dos provedores:
[docs/05-frontend/oauth/oauth-summary.md](../docs/05-frontend/oauth/oauth-summary.md).

---

## Estrutura

```
frontend/
├── public/                 # favicons + test.html
├── src/
│   ├── components/
│   │   ├── common/         # ErrorBoundary, MaskedInput, Modal, Responsive{Card,Container,Table}, RoleProtectedRoute
│   │   ├── layout/         # MainLayout, Navbar, Sidebar
│   │   └── (clientes/ estoque/ financeiro/ produtos/ vendas/ existem vazias, sem arquivo)
│   ├── pages/              # uma pasta por módulo (ver Status abaixo)
│   ├── services/
│   │   ├── api/            # axios.ts + um *Api.ts por domínio + apiPublica.ts
│   │   └── auth/           # authService.ts, tokenService.ts
│   ├── hooks/  contexts/  types/  utils/  styles/  img/
│   ├── config/             # env.ts, host.ts (painel x lojista por hostname)
│   ├── test/               # setup.ts do Vitest
│   ├── App.tsx             # rotas
│   └── main.tsx            # entry point
├── Dockerfile              # produção (build + nginx)
├── Dockerfile.dev          # desenvolvimento (hot reload)
├── nginx.conf              # config usada só na imagem de produção
├── index.html              # entry do Vite (na raiz de frontend/, não em public/)
├── vite.config.ts  vitest.config.ts  tsconfig.json  eslint.config.js
└── .env.example
```

Aliases de import (`@`, `@/components`, `@/pages`, …) estão em
`vite.config.ts:20-33`; o `vitest.config.ts` só replica o `@`.

---

## Estilo

- **Dark mode** como base, SCSS próprio — sem Tailwind.
- Fontes **Inter** e **JetBrains Mono**, importadas em `src/styles/global.scss:3`;
  `$font-family-base` em `src/styles/variables.scss:66`.
- Escala de espaçamento de **base 4px**, não múltiplos de 8:
  `$spacer-1: 4px` … `$spacer-10: 64px` (`variables.scss:94-101`, com
  `$spacer-0` e `$spacer-7: 80px` em `147-148`).
- `react-bootstrap` aparece em apenas 3 arquivos (os wrappers
  `Responsive{Card,Container,Table}`). Não existe `Button/` nem `Input/` em
  `components/common/`: os botões são `<button>` com classes SCSS (159
  ocorrências em 31 arquivos de `src/pages/`).

Especificação: [design/cores-tipografia.md](../docs/05-frontend/design/cores-tipografia.md)
e [design/componentes.md](../docs/05-frontend/design/componentes.md). Os dois
descrevem o design pretendido; onde divergirem do SCSS, o SCSS é a verdade.

---

## Scripts

Exatamente o que está em `package.json`:

| Script | Comando |
|---|---|
| `npm run dev` | `vite` |
| `npm run build` | `tsc && vite build` |
| `npm run preview` | `vite preview` |
| `npm run lint` | `eslint . --report-unused-disable-directives --max-warnings 115` |
| `npm run format` | `prettier --write "src/**/*.{ts,tsx,css,scss}"` |
| `npm run test` | `vitest` |
| `npm run test:coverage` | `vitest --coverage` |
| `npm run test:watch` | `vitest --watch` |

O `--max-warnings 115` é um teto herdado, não uma meta: o lint passa com até
115 warnings.

---

## Testes

Vitest + jsdom, setup em `src/test/setup.ts` (`vitest.config.ts:11`).
**10 arquivos de teste** hoje:

- `src/components/layout/Sidebar/__tests__/podeVer.test.ts`
- `src/config/__tests__/host.test.ts`
- `src/pages/Configuracoes/__tests__/{empresaSchema,integracoesSchema,usuarioSchema}.test.ts`
- `src/pages/Plataforma/__tests__/{assinaturaSchema,resumirTenants,tenantSchema}.test.ts`
- `src/services/api/__tests__/axios.test.ts`
- `src/utils/__tests__/errorLogger.test.ts`

Thresholds de cobertura configurados (`vitest.config.ts:25-30`): statements 70,
branches 65, functions 70, lines 70. **A CONFIRMAR**: a cobertura real medida —
os thresholds dizem o que é exigido, não o que é alcançado.

---

## Integração com o backend

`baseURL` do Axios = `env.apiUrl` (de `VITE_API_URL`, default `/api`), com
`withCredentials: true` — o auth usa cookies HTTP-only, não token no
localStorage (`src/services/api/axios.ts:17-24`). O `X-Empresa-Id` é injetado
pelo gateway a partir do JWT. Escritas (`POST/PUT/PATCH/DELETE`) recebem chave
de idempotência; `502/503/504` em métodos idempotentes são reenviados até 3
vezes, para cobrir a janela de deploy (`axios.ts:7-14`).

Rotas efetivamente chamadas por `src/services/`:

| Prefixo | Arquivo |
|---|---|
| `/auth/login`, `/auth/logout`, `/auth/me`, `/auth/forgot-password`, `/auth/reset-password` | `auth/authService.ts` |
| `/auth/admin/usuarios` | `api/usuariosApi.ts` |
| `/clientes/*` (endereços, histórico-crédito, crédito, ativar) | `api/clientesApi.ts` |
| `/produtos/*` | `api/produtosApi.ts` |
| `/estoque/*` (entrada, saída, ajuste, reservar, liberar-reserva, relatórios, lotes, movimentações) | `api/estoqueApi.ts` |
| `/empresas/{id}` | `api/empresaApi.ts` |
| `/plataforma/tenants/*`, `/plataforma/auditoria/*` | `api/plataformaApi.ts` |
| `/integracoes`, `/pagamentos/admin/status` | `api/integracoesApi.ts` |
| `/loja-online/produtos/{id}/publicar` | `api/lojaOnlineApi.ts` |

A loja pública não passa por esses clientes: usa `apiPublica` (`baseURL: '/api'`
fixo) direto em `hooks/useCarrinho.ts` e nas páginas de `LojaOnlinePublico/`
(`/empresas/publico/{slug}`, `/loja-online/publico/produtos`, `/loja/checkout`,
`/clientes/me`, `/auth/cliente/*`).

Não há cliente para `/vendas` nem `/financeiro` — os dois só aparecem em
`src/services/api/__tests__/axios.test.ts` como caminho de exemplo.

Referência da API: [docs/10-api-reference/](../docs/10-api-reference/) e
[docs/10-api-reference/plataforma-api.md](../docs/10-api-reference/plataforma-api.md).

---

## Status

### Funcionando com chamada real ao backend

- Autenticação por cookie HTTP-only + rotas protegidas e `RoleProtectedRoute`
- Layout (Navbar, Sidebar com filtro por permissão), Login, Perfil
- OAuth Google e Microsoft (login do cliente da loja online)
- **Clientes** — 4 páginas (lista, formulário, endereços, crédito)
- **Produtos** — 5 páginas (lista, formulário, detalhes, variantes, categorias)
- **Estoque** — 2 páginas + 4 componentes (modal de operação, badges, timeline)
- **Configurações** — empresa, usuários, integrações (com schemas Zod testados)
- **Plataforma** (super admin) — visão geral (`/plataforma`) e lista de
  tenants + detalhe (`/plataforma/tenants`), com auditoria, dumps e assinatura;
  páginas carregadas com `lazy()`
- **Loja Online** — painel de configuração + loja pública (catálogo, produto,
  carrinho, checkout, login do cliente, meus pedidos, rastreamento)
- Docker de dev e de produção, nginx na imagem de produção

### Stub ("em desenvolvimento" na tela)

- **Vendas** — `src/pages/Vendas/VendasPage.tsx` é uma tela "coming soon" com
  cards de features; nenhuma chamada de API
- **Financeiro** — idem, `src/pages/Financeiro/FinanceiroPage.tsx`
- **Pedidos Online** — `src/pages/LojaOnline/PedidosOnlinePage.tsx` tem 839 B

### Parcial

- **Gráficos no Dashboard** — os gráficos existem de verdade (`Line` e
  `Doughnut` do Chart.js, `DashboardPage.tsx:14`), mas os dados são estáticos
  dentro do próprio arquivo: `mockStats:32`, `lineChartData:122`,
  `doughnutData:162`. Renderizam; não refletem o banco.

Retrato mais detalhado (clientes HTTP, god components, dívidas):
[docs/05-frontend/frontend-current-state.md](../docs/05-frontend/frontend-current-state.md)
e [frontend-architectural-debt-log.md](../docs/05-frontend/frontend-architectural-debt-log.md).

---

## Documentação

Índice da documentação de frontend:
**[docs/05-frontend/README.md](../docs/05-frontend/README.md)**

Os mais usados no dia a dia:

- [setup/prerequisites.md](../docs/05-frontend/setup/prerequisites.md) — pré-requisitos
- [setup/docker.md](../docs/05-frontend/setup/docker.md) e
  [setup/docker-quick-start.md](../docs/05-frontend/setup/docker-quick-start.md)
- [guias/api-examples.md](../docs/05-frontend/guias/api-examples.md) — payloads de exemplo
- [design/](../docs/05-frontend/design/) — design system
- [deployment/production-checklist.md](../docs/05-frontend/deployment/production-checklist.md)

Fora da pasta de frontend: [../QUICK-START.md](../QUICK-START.md) para subir a
stack, [docs/03-arquitetura/](../docs/03-arquitetura/) para a visão dos
serviços e [.github/CONTRIBUTING.md](../.github/CONTRIBUTING.md) para o fluxo
de contribuição (branch, PR, checks).

---

**Última verificação contra o código**: 2026-09-26
