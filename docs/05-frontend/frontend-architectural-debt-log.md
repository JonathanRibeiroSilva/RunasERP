---
id: DEC-frontend-architectural-debt-log
type: decision
domain: frontend
status: active
source: AUD-2026-06-29-frontend
last_verified: 2026-09-25
---

# Frontend — Architectural Debt Log

Each critical and high issue (C1–C6, H1–H7) from AUD-2026-06-29 recorded as a debt entry. No solutions, no future architecture.

**Re-measured 2026-09-25 against `frontend/src` at branch `feat/g1b-plataforma-com-prova`.** The IDs are stable — the four frozen plans in `plans/` reference them, so nothing is renumbered or removed. Only the numbers, file/line evidence and statuses were re-measured. Entries that changed status carry a `Re-measured` line with the command-verifiable evidence. Where a sub-claim could not be re-verified, it is marked `A CONFIRMAR` instead of being restated.

Baseline for percentages: `frontend/src` totals **16,330 lines** across `.ts`/`.tsx`.

| ID | Status 2026-09-25 |
|----|-------------------|
| C1 | RESOLVED |
| C2 | RESOLVED (storefront residual) |
| C3 | RESOLVED (1 copy left) |
| C4 | OPEN — worse |
| C5 | RESOLVED |
| C6 | PARTIAL |
| H1 | OPEN — reduced |
| H2 | RESOLVED for Produtos (others A CONFIRMAR) |
| H3 | OPEN |
| H4 | OPEN — re-scoped |
| H5 | PARTIAL (2026-09-28, PR #113: só o painel da plataforma) |
| H6 | OPEN — reduced |
| H7 | RESOLVED (duplication residual) |
| M1 | OPEN — new 2026-09-25 |

---

### C1 — Server-state library (React Query) is configured but completely unused — Critical · Both
- **Problem:** React Query was configured but completely unused across the frontend.
- **Evidence summary (2026-06-29):** `useQuery|useMutation|useQueryClient|useInfiniteQuery` → 0 matches in src, while `QueryClientProvider` with staleTime/gcTime/retry is set in `main.tsx`.
- **Impact:** No caching, no request deduplication, no background refetch, no automatic invalidation, no built-in cancellation.
- **Re-measured 2026-09-25:** React Query is in use. Eight hooks in `frontend/src/hooks/` are built on it — `useClientes`, `useEmpresa`, `useEstoque`, `useIntegracoes`, `useLojaOnline`, `usePlataforma`, `useProdutos`, `useUsuarios` — plus four pages that call `useMutation`/`useQueryClient` directly (`ClienteFormPage`, `CategoriasPage`, `ProdutoDetalhesPage`, `ProdutoFormPage`). `useProdutos.ts` shows the full pattern: `queryKey`, `queryFn({ signal })`, `placeholderData: keepPreviousData`, and `invalidateQueries` on mutation success.
- **Status:** RESOLVED

---

### C2 — No API service layer; UI components call the network directly — Critical · Both
- **Problem:** No API service layer; UI components called the network directly.
- **Evidence summary (2026-06-29):** 84 `api.*`/`apiPublica.*` calls across 23 files; `services/api/` contained only `axios.ts`.
- **Impact:** URL/param drift, no single place for error/response normalization, untestable data logic.
- **Re-measured 2026-09-25:** The domain service layer exists. `frontend/src/services/api/` now holds eight domain modules — `clientesApi.ts`, `empresaApi.ts`, `estoqueApi.ts`, `integracoesApi.ts`, `lojaOnlineApi.ts`, `plataformaApi.ts`, `produtosApi.ts`, `usuariosApi.ts` — beside `axios.ts` and `apiPublica.ts`. The admin modules route through them (no Clientes page calls `api` directly: `ClienteFormPage`, `ClienteEnderecosPage` and `ClienteCreditoPage` import `clientesApi`, and `ClientesPage` goes through the `useClientes` hook).
- **Residual (tracked under H4, not reopened here):** the public storefront was not migrated — 36 direct `apiPublica.*` calls remain across 11 files (`CheckoutPage` 10, `ClienteLoginPage` 7, `useCarrinho` 5, `LojaOnlinePublicoPage` 4, `MeusPedidosPage` 3, plus 6 files with 1–2 each), and 16 direct `api.*` calls remain across 5 admin pages (`ProdutoVariantesPage` 5, `CategoriasPage` 4, `ProdutoFormPage` 4, `ProdutoDetalhesPage` 2, `PerfilPage` 1).
- **Status:** RESOLVED

---

### C3 — Axios client duplicated 12× (`apiPublica = axios.create`) — Critical · Both
- **Problem:** The Axios client was duplicated 12× via per-page `axios.create`.
- **Evidence summary (2026-06-29):** `axios.create` in 12 files — one canonical client plus 11 per-page copies of `baseURL: '/api'`.
- **Impact:** Cross-cutting concerns (auth redirect, timeout UX, error mapping) could not be applied uniformly.
- **Re-measured 2026-09-25:** Three `axios.create` calls remain in the whole of `frontend/src`, not twelve: `services/api/axios.ts:17` (canonical authenticated client), `services/api/apiPublica.ts:10` (single source for the storefront, which its own header documents as replacing the 11 copies), and `pages/LojaOnlinePublico/CheckoutPage.tsx:14` (the one surviving copy, with its own response interceptor at `:22-31`). Ten files now import the shared client (`from '@/services/api/apiPublica'`): the seven storefront files under `pages/LojaOnlinePublico/`, plus `hooks/useCarrinho.ts` and the two OAuth callbacks in `pages/Auth/`.
- **Residual:** CheckoutPage's private client — it does **not** import the shared `apiPublica` at all; it declares a local `const apiPublica = axios.create(...)` at `:14`, so the name resolves to the private copy throughout the file. Folded into C4.
- **Status:** RESOLVED

---

### C4 — `CheckoutPage.tsx` is a god component — Critical · Manual
- **Problem:** `CheckoutPage.tsx` is a god component holding all checkout concerns.
- **Evidence summary (2026-06-29):** 1,381 LOC, 28 useState, inline `apiPublica` + interceptor, inline types, 3-step wizard.
- **Re-measured 2026-09-25 — this got worse:** **1,507 LOC** (was 1,381, +126). It is the largest file in `frontend/src` by 3.3× (next: `PlataformaPage.tsx` at 460 LOC — medição de 2026-09-28, depois do PR #113: `PlataformaPage.tsx` caiu para 396 LOC e o segundo maior passou a ser `ProdutoFormPage.tsx`, 440 LOC, 3,4×) and is 9.2% of the 16,330-line frontend. It holds **27 `useState` declarations** and still creates its own Axios client plus response interceptor at `:14-31`, despite `services/api/apiPublica.ts` existing since the C3 consolidation.
- **Correction to the 2026-06-29 evidence:** the "423-LOC test file" claimed for CheckoutPage does not exist. `frontend/src` has nine test files (dez desde o PR #113, que acrescentou `config/__tests__/host.test.ts`) and none covers CheckoutPage; the 421-line one is `utils/__tests__/errorLogger.test.ts`. The god component is **untested**, which is worse than the original entry recorded.
- **Impact:** Untestable, unsafe to change, high render cost, prime defect site — and it is the single file blocking C3's last copy and H5's bundle split.
- **Status:** OPEN

---

### C5 — No Error Boundaries anywhere — Critical · Both
- **Problem:** There were no React error boundaries anywhere in the app.
- **Evidence summary (2026-06-29):** `ErrorBoundary|componentDidCatch|getDerivedStateFromError` → 0 matches.
- **Impact:** Any render-time throw unmounted the whole React tree to a blank screen.
- **Re-measured 2026-09-25:** `components/common/ErrorBoundary/ErrorBoundary.tsx` exists (class component with `getDerivedStateFromError` at `:19` and `componentDidCatch` at `:23`) and is mounted twice: around `<App />` in `main.tsx:30-32`, and per route in `MainLayout.tsx:82-84` with `key={location.pathname}` so a crashed page resets on navigation.
- **Status:** RESOLVED

---

### C6 — Dashboard, Inventory, Sales, Financial (and Config) are placeholders — Critical (scope) · Both
- **Problem:** Dashboard, Estoque, Vendas, Financeiro, and Configurações were placeholders, not implementations.
- **Evidence summary (2026-06-29):** hardcoded mock data in Dashboard; 44-line "coming soon" screens for Financeiro/Estoque/Vendas; 26–27-line Configurações stubs.
- **Re-measured 2026-09-25 — partially closed:**
  - **Still stubs:** `VendasPage.tsx` (47 LOC) and `FinanceiroPage.tsx` (47 LOC) are "coming soon" screens — `VendasPage.tsx:21` reads *"Esta funcionalidade está em desenvolvimento e será implementada em breve."*
  - **Still mock:** `DashboardPage.tsx` (326 LOC) renders real chart.js charts but over hardcoded data — `mockStats` at `:32`, `vendasRecentes` at `:39` — and the file makes **zero** `api.*`/`useQuery` calls. The old "Gráfico será implementado em breve" placeholder is gone; the mock data behind it is not.
  - **Out of stub:** Estoque (`EstoquePage.tsx` 336 LOC, `EstoqueDetalhePage.tsx` 239 LOC, backed by `useEstoque`/`estoqueApi`) and Configurações (`EmpresaPage.tsx` 305, `IntegracoesPage.tsx` 322, `UsuariosPage.tsx` 273, backed by `useEmpresa`/`useIntegracoes`/`useUsuarios`).
- **Impact:** Two functional modules (Vendas, Financeiro) plus the Dashboard's data layer remain non-existent; their architecture is still undefined.
- **Status:** PARTIAL — open for Vendas, Financeiro and Dashboard data

---

### H1 — Pervasive any and stringly-typed money; duplicated/conflicting domain & ApiError types — High · Both
- **Problem:** Pervasive `any`, stringly-typed money, and duplicated/conflicting domain and ApiError types.
- **Evidence summary (2026-06-29):** ~80 `any` across 29 files; `ApiError` declared twice with different shapes (`types/common.ts:20` vs `types/auth.ts:46`); money fields typed as string.
- **Re-measured 2026-09-25 — reduced, not closed:** `any` is down to **34 code occurrences across 9 files** outside `__tests__/` (from ~80/29); a plain `\bany\b` grep gives 36/10, which also counts `test/setup.ts:63` and the doc comment at `utils/errorLogger.ts:28`. `ApiError` is now declared **once**, at `types/common.ts:20` — the conflicting `types/auth.ts` copy is gone. Money is still a string: `useCarrinho.ts` now uses a named alias (`quantidade`/`preco_unitario`/`subtotal: Money`), but `types/common.ts:33` defines `export type Money = string`, so the runtime shape is unchanged — the alias documents the debt rather than fixing it.
- **A CONFIRMAR:** whether the inline redefinitions of Produto/Categoria/Cliente/Endereco across pages, and the `ProdutosResponse` vs `PaginatedResponse` divergence, still hold — not re-inventoried in this pass.
- **Status:** OPEN

---

### H2 — Tables: client-side filtering over a single page + no debounce — High (correctness) · Manual
- **Problem:** Table search/filter ran client-side over only the current page, with no debounce.
- **Evidence summary (2026-06-29):** `ProdutosPage.tsx` filtered the current 10-item page on the client and refetched on every keystroke.
- **Re-measured 2026-09-25 — closed for Produtos:** `ProdutosPage.tsx` (293 LOC) no longer filters on the client. Search is debounced 300 ms (`:33-40`, `setTimeout` + `clearTimeout` cleanup) and the term goes to the server as a query param: `useProdutos({ skip, limit, busca: debouncedSearch, categoria_id, apenas_deletados })` at `:42-48`; pagination reads `produtosData?.total` at `:54`.
- **A CONFIRMAR:** the other tables (Clientes, Estoque, Usuários, Plataforma) were not re-measured for server-side filtering or debounce. Sorting, row selection and virtualization were likewise not re-checked.
- **Status:** RESOLVED for Produtos; remainder A CONFIRMAR

---

### H3 — Broken/again-stale auth refresh in the interceptor — High · Manual
- **Problem:** The 401 interceptor does not refresh-and-retry; it hard-redirects to login.
- **Evidence summary, re-confirmed 2026-09-25:** `services/api/axios.ts:57-81` — the response interceptor casts the request to `{ _retry?: boolean }` at `:57` and tests `!originalRequest._retry` at `:60`, but **never sets `_retry`, never calls a refresh, and never retries**. After exempting `/auth/login`, `/auth/register` and `/auth/me`, it calls `tokenService.clearTokens()` and sets `window.location.href = '/login'` at `:78`. `authService.refreshToken` (`services/auth/authService.ts:41-46`) is still a deprecated no-op: it logs `'[authService] refreshToken is deprecated with HTTP-only cookies'` and returns `''`.
- **Impact:** A single expired-access-token 401 on any non-exempt request hard-redirects the user mid-task (lost form state), even when the refresh cookie may be valid; the "automatic refresh" claim in the comment above the interceptor is false in code.
- **Status:** OPEN

---

### H4 — No request cancellation; race conditions on unmount/refetch — High · Both
- **Problem:** No request cancellation, producing race conditions on unmount/refetch.
- **Evidence summary (2026-06-29):** `AbortController|signal|CancelToken|abort(` → 0 matches.
- **Re-measured 2026-09-25 — the "0 matches" claim is no longer true; the entry is re-scoped:** cancellation now exists wherever React Query was adopted. Nineteen `queryFn: ({ signal }) => …Api.…({ signal })` call sites across the eight hooks pass the abort signal through to Axios (`useProdutos.ts:17,24,36,45`, `useEstoque.ts:19,26,33,42,50`, `usePlataforma.ts:8,38,45`, `useLojaOnline.ts:10,25`, `useIntegracoes.ts:8,30`, `useEmpresa.ts:10`, `useClientes.ts:8`, `useUsuarios.ts:8`).
- **Residual — what is still uncancelled:** no explicit `AbortController` exists anywhere in `frontend/src`, so every path that did *not* migrate to React Query still sets state after `await` with no abort: the 36 manual `apiPublica.*` calls across the 11 storefront files listed in C2, and the 16 direct `api.*` calls in the 5 admin pages. Fast filter/typing or quick navigation on those screens can still apply an out-of-order response.
- **Status:** OPEN (storefront and the 5 unmigrated admin pages)

---

### H5 — No route-level code splitting — High (perf/spec) · Both
- **Problem:** No route-level code splitting; the whole app ships in one bundle.
- **Evidence summary, re-confirmed 2026-09-25:** `lazy(`/`Suspense` → **0 matches** in all of `frontend/src`. `App.tsx:3-21` statically imports **34 page components** — every admin page, every storefront page, and the 1,507-line `CheckoutPage`. `chart.js` and `react-chartjs-2` (both in `frontend/package.json`) are imported only by `DashboardPage.tsx:3-14`, so the public storefront still pays for the chart libraries.
- **Impact:** Large first-load payload; public storefront users download the entire admin app.
- **Re-medido em 2026-09-28 (PR #113, commit `4643422`) — parcial:** `lazy(` → **2 ocorrências** em `frontend/src`, ambas em `App.tsx:28-29` (`PlataformaPage` e `PlataformaDashboard`), com um `<Suspense fallback={<LoadingScreen />}>` em volta das `<Routes>` (`App.tsx:126`). Segundo a mensagem do commit, o build separa `PlataformaPage` (16,8 kB), `PlataformaDashboard` (3,2 kB) e `assinaturaSchema` (2,1 kB) do `index.js` (A CONFIRMAR: tamanhos não re-medidos nesta revisão). `App.tsx:5-22` ainda importa estaticamente **33 páginas**, inclusive todo o storefront e o `CheckoutPage`; o `chart.js` continua no bundle principal via `DashboardPage`. O storefront continua baixando o app administrativo inteiro, menos o painel da plataforma.
- **Status:** PARTIAL (só as páginas do painel da plataforma são lazy)

---

### H6 — Shared component library is dead code; every page re-implements UI — High · Both
- **Problem:** The shared component library is dead code; pages re-implement UI.
- **Evidence summary (2026-06-29):** `ResponsiveTable`/`ResponsiveCard`/`ResponsiveContainer` exported with zero page imports; `MaskedInput` imported only by CheckoutPage.
- **Re-measured 2026-09-25 — reduced, core claim still true:** `ResponsiveContainer`, `ResponsiveTable` and `ResponsiveCard` are still exported by `components/common/index.ts:2-4` and imported by **nothing outside their own folders** — and that barrel itself has zero importers (`from '@/components/common'` → 0 matches). They are dead code.
- **What did come alive:** `components/common/` now also holds `ErrorBoundary/` (used, see C5), `RoleProtectedRoute.tsx` (used, see H7) and `Modal/` (imported by `UsuariosPage`, `EstoqueOperacaoModal`, `PlataformaPage`, `TenantDetalhe`). `MaskedInput` is no longer CheckoutPage-only — it is imported by `EmpresaPage`, `CheckoutPage` and `PlataformaPage`.
- **A CONFIRMAR:** the spec's Button/Table/Pagination/Loading/Card/Badge/ConfirmDialog do not exist as directories under `components/common/`, but whether each page still hand-rolls raw `<table>`/badge/spinner markup was not re-inventoried page by page in this pass.
- **Status:** OPEN (the three Responsive* components)

---

### H7 — Stub feature routes have no permission protection — High (security) · Manual
- **Problem:** Stub feature routes (estoque, vendas, financeiro) had no permission protection, and role checks were duplicated.
- **Evidence summary (2026-06-29):** estoque, vendas and financeiro were reachable by any authenticated user; only `configuracoes/*` was wrapped in `RoleProtectedRoute`.
- **Re-measured 2026-09-25 — the access hole is closed:** every feature route is now wrapped. `App.tsx:202` (`estoque`) and `:210` (`estoque/:id`) and `:220` (`vendas`) use `<RoleProtectedRoute requiredRole={['ADMIN', 'OPERADOR']}>`; `:230` (`financeiro`) uses `requiredRole={['ADMIN']}`. `configuracoes/*` stayed ADMIN-only and `:263` (`plataforma`) and `:273` (`plataforma/tenants`) are `['SUPER_ADMIN']`, registered only on the panel host (linhas re-medidas em 2026-09-28, depois do commit `045c0c0`). `RoleProtectedRoute` denies with a toast and `<Navigate to="/dashboard" replace />`.
- **Residual — the duplication was not fixed:** three independent role-check implementations still coexist, with different semantics. `AuthContext.hasRole` (`AuthContext.tsx:71`) is strict equality `user?.role === role`; `RoleProtectedRoute` (`RoleProtectedRoute.tsx:20`) is `requiredRole.includes(user.role)`; `Sidebar.podeVer` (`Sidebar.tsx:153`, exported and covered by `Sidebar/__tests__/podeVer.test.ts`) is a third. The role set has grown to include `SUPER_ADMIN`, so the "ADMIN/OPERADOR only" note no longer holds, and there is still no action-level gating — only route-level.
- **Status:** RESOLVED for route protection; duplication residual OPEN

---

### M1 — No real 404 page; unknown routes silently become the dashboard — Medium · Manual
- **Problem:** The application has no 404 screen. Any unmatched URL is redirected to the dashboard instead of reporting that the route does not exist.
- **Evidence summary (2026-09-25):** `App.tsx:244` — `<Route path="*" element={<Navigate to="/dashboard" replace />} />`, the only catch-all in the router, under a `{/* 404 */}` comment. There is no `NotFound`/`404` page component anywhere in `frontend/src/pages/`.
- **Re-medido em 2026-09-28 (depois do commit `045c0c0`):** o catch-all agora está em `App.tsx:292`, sem mudança de comportamento. Em produção, fora do host do painel, `/plataforma*` também cai nele, porque essas rotas não são registradas ali. A única resposta 404 de verdade é a do `frontend/nginx.conf:71-76`, e vale só para `/plataforma` fora de `admin.*`.
- **Impact:** A typo'd or dead link looks like a successful navigation, so broken links are invisible in use and in bug reports; storefront visitors with no session are bounced through the dashboard route into the login redirect, losing the URL they asked for. `replace` also erases the bad URL from history, so Back cannot recover it for debugging.
- **Status:** OPEN — new entry, added 2026-09-25
