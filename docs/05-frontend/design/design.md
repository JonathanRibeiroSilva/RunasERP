# Design Document: Frontend ERP Runas

## Overview

O frontend do ERP Runas é uma SPA em React + TypeScript, com Bootstrap/React Bootstrap e SCSS próprio (dark-first), servida pelo Vite na porta 3000 em dev e por nginx (porta 80 do container) em produção, falando com o backend FastAPI exclusivamente pelo API Gateway.

**Características (conferidas no código):**
- Tema escuro único, com tokens em `frontend/src/styles/variables.scss`
- Autenticação por cookie HTTP-only (`withCredentials: true` em `frontend/src/services/api/axios.ts`)
- Três papéis: `ADMIN`, `OPERADOR` e `SUPER_ADMIN` (`frontend/src/types/auth.ts`)
- Estado de servidor com TanStack React Query; estado de sessão com Context API (`AuthContext`)
- Formulários com React Hook Form + Zod
- Loja online pública em `/c/:empresaSlug`, fora do layout autenticado

## Tech Stack

Versões conforme `frontend/package.json` (faixas semver declaradas, não a versão instalada):

| Área | Biblioteca | Versão declarada |
|------|-----------|------------------|
| UI | `react`, `react-dom` | ^19.3.0 |
| Linguagem | `typescript` | ^5.2.2 |
| Build/dev server | `vite` | ^8.3.0 |
| Roteamento | `react-router-dom` | ^7.18.4 |
| CSS | `bootstrap` | ^5.3.2 |
| Componentes | `react-bootstrap` | ^2.9.1 |
| Ícones | `react-icons` (conjunto `fi`) | ^5.7.0 |
| Pré-processador | `sass` | ^1.104.1 |
| Server state | `@tanstack/react-query` | ^5.103.1 |
| Formulários | `react-hook-form` + `@hookform/resolvers` | ^7.88.0 / ^5.9.1 |
| Validação | `zod` | ^4.6.5 |
| HTTP | `axios` | ^1.20.0 |
| Datas | `date-fns` | ^4.4.0 |
| Toasts | `react-toastify` | ^11.1.0 |
| Gráficos | `chart.js` + `react-chartjs-2` | ^4.4.1 / ^5.2.0 |
| Testes | `vitest` + Testing Library + `jsdom` | ^5.0.1 |

Observações:
- Não há Zustand nem outra lib de estado cliente.
- `react-loading-skeleton` está nas dependências, mas nenhum arquivo em `frontend/src/` o importa.

## Architecture

### High-Level Architecture

```
Browser
  ↓
Frontend (dev: Vite na porta 3000; prod: nginx na porta 80 do container frontend-prod)
  ↓  /api/*
API Gateway (porta 8000)
  ↓
Microsserviços (8001-8007)
```

O `baseURL` do axios vem de `VITE_API_URL`, com padrão `/api` (`frontend/src/config/env.ts`). Em dev, o Vite faz proxy de `/api` para `VITE_API_GATEWAY_TARGET` (padrão `http://api-gateway:8000`), removendo o prefixo `/api`; `VITE_USE_PROXY=false` desliga o proxy (`frontend/vite.config.ts`). Em produção quem faz esse papel é o `frontend/nginx.conf`: `location /api/` tira o prefixo e encaminha para `api-gateway-prod:8000`.

### Component Architecture

Composição real de `frontend/src/main.tsx` e `frontend/src/App.tsx`:

```
QueryClientProvider (React Query)
├── AuthProvider (Context)
│   ├── ErrorBoundary
│   │   └── App → BrowserRouter → Suspense (fallback LoadingScreen)
│   │       ├── Rotas públicas: /login, /forgot-password (PublicRoute), /reset-password
│   │       ├── Loja pública: /c/:empresaSlug/...
│   │       ├── Callbacks OAuth: /auth/callback/google, /auth/callback/microsoft
│   │       └── "/" → ProtectedRoute → MainLayout
│   │           ├── Navbar
│   │           ├── Sidebar
│   │           └── main.main-content → ErrorBoundary → <Outlet />
│   └── ToastContainer (theme="dark", autoClose 3000)
└── ReactQueryDevtools (só com VITE_ENABLE_DEVTOOLS=true)
```

Não existe Footer nem Breadcrumbs. Rotas desconhecidas redirecionam para `/dashboard` (não há página 404).

`ProtectedRoute` decide o destino com `escolherPorta()` (`frontend/src/config/host.ts`): o `SUPER_ADMIN` vai para `/plataforma` em qualquer rota que não comece com `/plataforma` ou `/perfil`, os outros papéis vão para `/dashboard` se pedirem `/plataforma*` (só em dev: em produção essas rotas nem são registradas fora do host do painel), e quem está no host errado vê a tela "Endereço errado" (`PortaErrada`, em `App.tsx`).

**Separação por host.** O mesmo bundle serve o ERP dos lojistas e o painel da plataforma. `ehPainelPlataforma` é verdadeiro quando o primeiro label de `window.location.hostname` é `VITE_HOST_PLATAFORMA` (padrão `admin`). Com a separação ativa, SUPER_ADMIN fora do host do painel ou outro papel dentro dele recebe `PortaErrada` — uma tela, não um redirect, porque o cookie de sessão é host-only e não iria para o outro host. `/perfil` vale nos dois lados. Em produção, fora do host do painel, as rotas `/plataforma*` não são registradas (em dev, em `localhost`, continuam), e o `nginx.conf` devolve 404 em `/plataforma` para host que não comece com `admin.`. Em dev (`import.meta.env.DEV`) a separação só liga quando o host já é o do painel: as duas aplicações convivem em `localhost` e `admin.localhost:3000` exercita o caminho de produção. A separação é só da interface: `/api` é relativo (same-origin em qualquer host) e `/api/plataforma/*` responde nos dois hosts, protegido por `require_super_admin`. Em produção desde 2026-09-28 (o PR #113 chegou à `main` pelo PR #114).

Rotas com restrição de papel usam `RoleProtectedRoute` (`frontend/src/components/common/RoleProtectedRoute.tsx`):

| Rota | Papéis |
|------|--------|
| `/estoque`, `/estoque/:id`, `/vendas` | ADMIN, OPERADOR |
| `/financeiro`, `/configuracoes/empresa`, `/configuracoes/usuarios`, `/configuracoes/integracoes` | ADMIN |
| `/plataforma`, `/plataforma/tenants` | SUPER_ADMIN |

### Data Flow

```
Componente
  ↓ useQuery / useMutation (hooks em src/hooks/)
React Query
  ↓
Serviço (src/services/api/*Api.ts)
  ↓ instância `api` (axios, withCredentials)
Interceptor de request (Idempotency-Key em POST/PUT/PATCH/DELETE)
  ↓
API Gateway
  ↓ resposta
Interceptor de response (401 → /login; 502/503/504 em GET/HEAD/OPTIONS → até 3 retries)
  ↓
Cache do React Query → re-render
```

## Folder Structure

Estrutura real de `frontend/` (resumida):

```
frontend/
├── public/                 # favicon-32/48/180.png, test.html
├── src/
│   ├── components/
│   │   ├── common/         # ErrorBoundary, MaskedInput, Modal, ResponsiveCard,
│   │   │                   # ResponsiveContainer, ResponsiveTable, RoleProtectedRoute.tsx
│   │   ├── layout/         # MainLayout, Navbar, Sidebar
│   │   └── clientes/ produtos/ estoque/ vendas/ financeiro/   # (vazias)
│   ├── pages/              # Auth, Clientes, Configuracoes, Dashboard, Estoque, Financeiro,
│   │                       # Login, LojaOnline, LojaOnlinePublico, Perfil, Plataforma,
│   │                       # Produtos, Vendas
│   ├── services/
│   │   ├── api/            # axios.ts, apiPublica.ts, clientesApi.ts, empresaApi.ts,
│   │   │                   # estoqueApi.ts, integracoesApi.ts, lojaOnlineApi.ts,
│   │   │                   # plataformaApi.ts, produtosApi.ts, usuariosApi.ts
│   │   └── auth/           # authService.ts, tokenService.ts
│   ├── hooks/              # useAuth, useCarrinho, useClientes, useEmpresa, useEstoque,
│   │                       # useIntegracoes, useLojaOnline, usePlataforma, useProdutos, useUsuarios
│   ├── contexts/           # AuthContext.tsx
│   ├── types/              # auth, clientes, common, empresa, estoque, integracao,
│   │                       # plataforma, produtos, usuario
│   ├── utils/              # errorLogger.ts, masks.ts, toast.ts, validators.ts
│   ├── config/             # env.ts, host.ts (+ __tests__/host.test.ts)
│   ├── styles/             # global.scss, variables.scss, mixins.scss
│   ├── img/                # logo.png, logo1.png, background.png
│   ├── test/setup.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── vite-env.d.ts
├── .env.example
├── Dockerfile / Dockerfile.dev / nginx.conf
├── eslint.config.js / .prettierrc
├── index.html
├── package.json
├── tsconfig.json / tsconfig.node.json
├── vite.config.ts
└── vitest.config.ts
```

As pastas de domínio em `components/` não têm arquivos; os componentes de cada módulo vivem dentro de `pages/<Módulo>/`. Não há `ThemeContext` nem `usePermissions`; não há `vendasApi.ts` nem `financeiroApi.ts`.

## Core Patterns

### 1. Autenticação

```typescript
// frontend/src/types/auth.ts
export interface AuthContextType {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => Promise<void>;
  setAuthUser: (user: User) => void;
  hasRole: (role: UserRole) => boolean;
}
```

- No boot, `AuthProvider` chama `GET /auth/me` (exceto em `/c/*`, a loja pública).
- `authService` usa `POST /auth/login`, `POST /auth/logout`, `GET /auth/me`, `POST /auth/forgot-password` e `POST /auth/reset-password`.
- Os tokens ficam em cookies HTTP-only definidos pelo backend. Em `tokenService`, a única função com efeito é `clearTokens()` (limpa chaves legadas do `localStorage`); os getters devolvem `null`, os setters só emitem aviso e estão marcados como deprecated.
- Em 401 (fora de `/auth/login`, `/auth/register` e `/auth/me`) o interceptor limpa o `localStorage` legado e redireciona para `/login`. O frontend **não** chama `POST /auth/refresh`, embora a rota exista no gateway (`api-gateway/routers/auth.py`).

### 2. Serviço de API

Cada módulo tem um objeto de serviço que é o único lugar que conhece URLs. Exemplo real (`frontend/src/services/api/clientesApi.ts`, trecho):

```typescript
export const clientesApi = {
  listar(params: ListarClientesParams, config?: AxiosRequestConfig) {
    return api.get<ClientesListResult>('/clientes', { params, ...config }).then((r) => r.data);
  },
  obter(id: string) {
    return api.get<Cliente>(`/clientes/${id}`).then((r) => r.data);
  },
  criar(data: Partial<Cliente>) {
    return api.post<Cliente>('/clientes', data).then((r) => r.data);
  },
  atualizar(id: string, data: Partial<Cliente>) {
    return api.patch<Cliente>(`/clientes/${id}`, data).then((r) => r.data);
  },
  desativar(id: string) {
    return api.delete(`/clientes/${id}`).then(() => undefined);
  },
  // ... reativar, endereços, crédito, bloquear/desbloquear
};
```

### 3. Hook React Query

```typescript
// frontend/src/hooks/useClientes.ts
export const useClientes = (params: ListarClientesParams) =>
  useQuery({
    queryKey: ['clientes', params],
    queryFn: ({ signal }) => clientesApi.listar(params, { signal }),
    placeholderData: keepPreviousData,
  });

export const useDesativarCliente = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => clientesApi.desativar(id),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['clientes'] }),
  });
};
```

### 4. Validação de formulário

React Hook Form + `zodResolver` nas páginas de Login, Perfil, Clientes (form, endereços, crédito), Produtos (form), Configurações (empresa, usuários, integrações) e Plataforma. Em Configurações e Plataforma os schemas ficam em arquivos próprios (`empresaSchema.ts`, `usuarioSchema.ts`, `integracoesSchema.ts`, `tenantSchema.ts`, `assinaturaSchema.ts`), com testes em `__tests__/`.

## UI/UX Design Principles

> Detalhes do design system nos documentos irmãos:
> - **[Cores e Tipografia](./cores-tipografia.md)**
> - **[Componentes](./componentes.md)**
> - **[Layouts e Responsividade](./layouts.md)**
>
> A fonte da verdade é o SCSS em `frontend/src/styles/`; se um documento divergir dele, vale o código.

### Runas Brand Identity

**Filosofia:** Clareza, inteligência e controle. Inspirado em Linear, Vercel, Stripe e Notion.

**O que somos:**
- Ferramenta operacional moderna
- Interface inteligente e clara
- Design profissional e confiável

**O que NÃO somos:**
- Software fiscal legado
- Interface cyberpunk/neon
- Design exagerado ou chamativo

### Color Palette (Dark Mode First)

Valores de `frontend/src/styles/variables.scss`:

```scss
// Background
$background: #080A0F;
$surface: #10141D;
$surface-hover: #171C28;
$surface-elevated: #1A202C;

// Primary - ciano/azul
$primary: #0EA5E9;
$primary-hover: #38BDF8;
$primary-active: #0284C7;
$primary-light: rgba(14, 165, 233, 0.15);

// Secondary - índigo
$secondary: #6366F1;
$secondary-hover: #818CF8;
$secondary-light: rgba(99, 102, 241, 0.15);

// Text
$text-primary: #FFFFFF;
$text-secondary: #94A3B8;
$text-tertiary: #64748B;
$text-disabled: #475569;

// Semantic
$success: #10B981;
$warning: #F59E0B;
$error: #EF4444;   // alias: $danger
$info: #3B82F6;

// Bordas
$border-subtle: rgba(255, 255, 255, 0.04);
$border-default: rgba(255, 255, 255, 0.08);
$border-hover: rgba(255, 255, 255, 0.15);
$border-strong: rgba(255, 255, 255, 0.25);

// Glassmorphism
$glass-bg: rgba(16, 20, 29, 0.65);
$glass-border: rgba(255, 255, 255, 0.08);
$glass-blur: blur(16px);
```

**Regras:**
- Vermelho (`$error`) apenas para erros e ações destrutivas, não para decoração.
- Não existe token de dourado em `variables.scss`; um acento dourado não faz parte da paleta atual.

### Typography

```scss
$font-family-base: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
$font-family-monospace: 'JetBrains Mono', 'Fira Code', 'Courier New', monospace;

$font-size-xs: 0.75rem;     // 12px
$font-size-sm: 0.875rem;    // 14px
$font-size-base: 0.9375rem; // 15px
$font-size-lg: 1.0625rem;   // 17px
$font-size-xl: 1.25rem;     // 20px
$font-size-2xl: 1.5rem;     // 24px
$font-size-3xl: 2rem;       // 32px

$h1-font-size: 2.5rem;
$h2-font-size: 2rem;
$h3-font-size: 1.75rem;
$h4-font-size: 1.5rem;
```

Inter e JetBrains Mono são carregadas do Google Fonts no topo de `frontend/src/styles/global.scss`.

### Spacing

```scss
$spacer-0: 0;
$spacer-1: 0.25rem; // 4px
$spacer-2: 0.5rem;  // 8px
$spacer-3: 0.75rem; // 12px
$spacer-4: 1rem;    // 16px
$spacer-5: 1.5rem;  // 24px
$spacer-6: 2rem;    // 32px
$spacer-7: 5rem;    // 80px
$spacer-8: 3rem;    // 48px
$spacer-10: 4rem;   // 64px
```

Atenção: `$spacer-7` (80px) é maior que `$spacer-8` (48px); é definido no bloco "Missing Spacers", dentro da seção de aliases legados de `variables.scss`.

### Responsive Breakpoints

Mixins de `frontend/src/styles/mixins.scss` (não há `xxl`):

```scss
@mixin media-xs { @media (max-width: 575px) { @content; } }
@mixin media-sm { @media (min-width: 576px) { @content; } }
@mixin media-md { @media (min-width: 768px) { @content; } }
@mixin media-lg { @media (min-width: 992px) { @content; } }
@mixin media-xl { @media (min-width: 1200px) { @content; } }
```

Detalhes de layout em [layouts.md](./layouts.md).

### Component States

- **Loading**: spinner do Bootstrap (`spinner-border` / `<Spinner>`) na tela de carregamento de `App.tsx` e nas páginas de Clientes, Produtos e Estoque; não há skeleton loaders em uso.
- **Erro de renderização**: `ErrorBoundary` global e outro por rota dentro do `MainLayout` (com `key={location.pathname}`, reseta ao navegar).
- **Feedback**: toasts via `react-toastify` (canto superior direito, 3s, tema escuro).

### Accessibility

Diretrizes (não há auditoria automatizada no repositório):
- Contraste mínimo 4.5:1 (WCAG AA)
- Foco visível: mixins `focus-ring`, `focus-glow` e `focus-ring-shadow`
- Labels em todos os inputs
- Navegação por teclado
- Mensagens de erro associadas aos campos

## Key Features Design

Estado atual de cada módulo, conferido nas páginas:

### 1. Dashboard (`pages/Dashboard/DashboardPage.tsx`)

- **Dados 100% mockados** (`mockStats`, `vendasRecentes`, `topProdutos`, `categoriasVendas`); a página não chama nenhuma API.
- Cards de métrica em `.stats-grid` (`repeat(auto-fit, minmax(240px, 1fr))`).
- Gráfico de linha "Vendas dos Últimos 7 Dias" e rosca "Vendas por Categoria" (react-chartjs-2).
- Tabela "Vendas Recentes" e lista "Top Produtos".
- Linhas em `1.8fr 1fr` que viram 1 coluna abaixo de 1024px.

### 2. Clientes (`pages/Clientes/`)

- Lista com paginação (`ClientesPage`), formulário de criar/editar (`ClienteFormPage`), endereços (`ClienteEnderecosPage`) e crédito (`ClienteCreditoPage`).
- Busca de endereço por CEP no ViaCEP (`https://viacep.com.br/ws/{cep}/json/`), no form do cliente e na página de endereços.
- Ações de desativar/reativar e bloquear/desbloquear via `clientesApi`.

### 3. Produtos (`pages/Produtos/`)

- Lista, formulário, detalhes, variantes (`ProdutoVariantesPage`) e categorias (`CategoriasPage`).

### 4. Estoque (`pages/Estoque/`)

- Lista (`EstoquePage`), detalhe por item (`EstoqueDetalhePage`), modal de operação (`EstoqueOperacaoModal`) e timeline de movimentações (`MovimentacaoTimeline`).

### 5. Vendas e 6. Financeiro

- **Placeholders**: `VendasPage.tsx` e `FinanceiroPage.tsx` só exibem "Esta funcionalidade está em desenvolvimento e será implementada em breve."

### Outros módulos

- **Loja Online (admin)**: pedidos online e configurações da loja (`pages/LojaOnline/`).
- **Loja Online pública**: vitrine, produto, carrinho, checkout, rastreamento, login e área do cliente (`pages/LojaOnlinePublico/`).
- **Configurações** (ADMIN): empresa, usuários e integrações.
- **Plataforma** (SUPER_ADMIN): visão geral em `/plataforma` (`PlataformaDashboard`) e gestão de tenants em `/plataforma/tenants` (`PlataformaPage`, `TenantDetalhe`).
- **Perfil**: dados do usuário e troca de senha.

## Performance Optimization

### Code Splitting

Parcial. Só as duas páginas do painel da plataforma são `lazy()` (`PlataformaPage` e `PlataformaDashboard`, `App.tsx:28-29`), sob um `Suspense` com `LoadingScreen` que envolve as rotas; no host do lojista nenhuma rota pede esses chunks. As demais páginas, inclusive todo o storefront, continuam importadas estaticamente em `App.tsx`.

### React Query Configuration

```typescript
// frontend/src/main.tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5 * 60 * 1000, // 5 minutes
      gcTime: 10 * 60 * 1000,   // 10 minutes
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});
```

### Resiliência a deploy

O interceptor de response repete GET/HEAD/OPTIONS que recebem 502/503/504 até 3 vezes, esperando 1s, 2s e 3s (`frontend/src/services/api/axios.ts`). Escritas não são repetidas.

### Build

`npm run build` roda `tsc && vite build`, saída em `dist/` com `sourcemap: true` (`frontend/vite.config.ts`). Em produção o `frontend/nginx.conf` liga `gzip` (sem brotli).

## Security

### Sessão

- Tokens em cookies HTTP-only, enviados pelo navegador (`withCredentials: true`); o JavaScript não lê nem grava tokens.
- O header `X-Empresa-Id` não é enviado pelo frontend; o gateway o deriva do JWT (comentário em `axios.ts`).

### Idempotência

Toda escrita (POST/PUT/PATCH/DELETE) recebe um `Idempotency-Key` (`crypto.randomUUID()`), preservado em reenvios, que o gateway usa para não duplicar operações (`api-gateway/proxy/idempotency.py`).

### Sanitização

Não há DOMPurify nem sanitização de HTML no frontend. Em produção o `frontend/nginx.conf` envia um `Content-Security-Policy` restritivo (`script-src 'self'`, `connect-src 'self' https://viacep.com.br`, `frame-ancestors 'none'`).

## Testing Strategy

- Runner: Vitest com ambiente `jsdom` (`frontend/vitest.config.ts`), setup em `frontend/src/test/setup.ts`.
- Scripts: `npm run test`, `npm run test:watch`, `npm run test:coverage`.
- Testes existentes em `__tests__/`: `services/api/__tests__/axios.test.ts`, `components/layout/Sidebar/__tests__/podeVer.test.ts`, `config/__tests__/host.test.ts` (`escolherPorta`), `utils/__tests__/errorLogger.test.ts`, schemas de Configurações e Plataforma e `resumirTenants.test.ts`.
- Não há testes E2E (sem Playwright/Cypress).

## Deployment

### Build

```bash
cd frontend
npm run build
# Saída: dist/
```

### Environment Variables

Lidas em `frontend/src/config/env.ts`, `frontend/src/config/host.ts` e `frontend/vite.config.ts` (modelo em `frontend/.env.example`):

| Variável | Padrão no código |
|----------|------------------|
| `VITE_API_URL` | `/api` |
| `VITE_API_TIMEOUT` | `30000` |
| `VITE_USE_PROXY` | proxy ativo, exceto se `false` |
| `VITE_API_GATEWAY_TARGET` | `http://api-gateway:8000` |
| `VITE_APP_NAME` | `Runas` |
| `VITE_APP_VERSION` | `1.0.0` |
| `VITE_ENABLE_DEVTOOLS` | desligado |
| `VITE_ENABLE_ANALYTICS` | desligado |
| `VITE_TOKEN_REFRESH_THRESHOLD` | `300000` |
| `VITE_GOOGLE_CLIENT_ID`, `VITE_MICROSOFT_CLIENT_ID` | vazio |
| `VITE_MICROSOFT_TENANT_ID` | `common` |
| `VITE_OAUTH_REDIRECT_URI` | `http://localhost:3000/auth/callback` |
| `VITE_HOST_PLATAFORMA` | `admin` (primeiro label do hostname que monta o painel; lida em `host.ts`; comentada no `.env.example`) |

### Docker

`frontend/Dockerfile` é multi-stage: `node:22-alpine` roda `npm ci` e `npm run build`; `nginx:alpine` serve `dist/` com `frontend/nginx.conf`, expõe a porta 80 e tem `HEALTHCHECK` via `wget` em `http://127.0.0.1/` (em produção o `docker-compose.prod.yml` sobrescreve para `http://127.0.0.1/health`). Para desenvolvimento há `frontend/Dockerfile.dev`.

### CI/CD

- `.github/workflows/ci.yml`, job `frontend`: Node 22, `npm ci`, `npm run lint`, `npm run build`, `npm run test -- --run`.
- `.github/workflows/deploy.yml`: gera e publica as imagens no ghcr e dispara o deploy no Coolify, que puxa as imagens e reinicia a stack.

## Monitoring

- `frontend/src/utils/errorLogger.ts`: log estruturado de erros no console.
- `VITE_ENABLE_ANALYTICS` vira `env.enableAnalytics` em `env.ts`, mas nenhum código lê essa flag.
- Não há Sentry, Google Analytics nem Web Vitals integrados.

## API Documentation

- Swagger UI do gateway em `http://localhost:8000/docs`, apenas quando `DOCS_ENABLED` está ligado (`api-gateway/main.py`).
- Mapeamento de rotas: [docs/10-api-reference/mapeamento-rotas.md](../../10-api-reference/mapeamento-rotas.md).

## Pendências conhecidas

1. Dashboard ligado a dados reais (hoje é mock).
2. Telas de Vendas e Financeiro (hoje são placeholders).
3. Renovação de sessão via `POST /auth/refresh` no frontend.
4. Code splitting das rotas (hoje só as páginas da Plataforma são `lazy()`).
