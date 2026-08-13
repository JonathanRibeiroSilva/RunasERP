---
id: DEC-frontend-architectural-debt-log
type: decision
domain: frontend
status: active
source: AUD-2026-06-29-frontend
---

# Frontend — Architectural Debt Log

Each critical and high issue (C1–C6, H1–H7) from AUD-2026-06-29 recorded as a debt entry. No solutions, no future architecture.

---

### C1 — Server-state library (React Query) is configured but completely unused — Critical · Both
- **Problem:** React Query is configured but completely unused across the frontend.
- **Evidence summary:** `useQuery|useMutation|useQueryClient|useInfiniteQuery` → 0 matches in src, while `QueryClientProvider` with staleTime/gcTime/retry is set in `main.tsx:15-24`. Graphify shows no React-Query hook nodes. Affected: every data page (Produtos, Clientes, Loja*, etc.).
- **Impact:** No caching, no request deduplication, no background refetch, no automatic invalidation, no built-in cancellation — all the benefits the spec relies on are absent. Every screen reinvents loading/error/empty handling. This is the single largest divergence from the spec.
- **Status:** OPEN

---

### C2 — No API service layer; UI components call the network directly — Critical · Both
- **Problem:** No API service layer; UI components call the network directly.
- **Evidence summary:** 84 `api.*`/`apiPublica.*` calls across 23 files (e.g., `ProdutosPage.tsx:59`, `ClienteFormPage.tsx` 7 calls, `CheckoutPage.tsx` 12 calls). The spec's `services/api/{clientes,produtos,vendas,estoque,financeiro}Api.ts` modules do not exist — `services/api/` contains only `axios.ts`. No service god-node in Graphify.
- **Impact:** URL/param drift, no single place for error/response normalization, untestable data logic, high coupling of UI to transport.
- **Status:** OPEN

---

### C3 — Axios client duplicated 12× (`apiPublica = axios.create`) — Critical · Both
- **Problem:** The Axios client is duplicated 12× via per-page `axios.create`.
- **Evidence summary:** `axios.create` in 12 files — canonical `services/api/axios.ts:7` plus 11 copies (useCarrinho, CheckoutPage, GoogleCallback, MicrosoftCallback, ClienteLoginPage, ClientePerfilPage, MeusPedidosPage, RastreamentoPedidoPage, ProdutoDetalhePage, LojaOnlinePublicoPage, ClienteLayout). Canonical uses `baseURL: env.apiUrl`; every `apiPublica` hardcodes `baseURL: '/api'`; only CheckoutPage's copy has a response interceptor.
- **Impact:** Cross-cutting concerns (auth redirect, timeout UX, error mapping) cannot be applied uniformly; behavior differs by page; 11 places to change for any client policy update.
- **Status:** OPEN

---

### C4 — `CheckoutPage.tsx` is a 1,381-line god component (28 useState) — Critical · Manual
- **Problem:** `CheckoutPage.tsx` is a 1,381-line god component holding 28 useState and all checkout concerns.
- **Evidence summary:** 1,381 LOC (largest file by 3×, ~14% of frontend); 28 useState; inline `apiPublica` + interceptor; inline types (ClienteNovo/Endereco/Pagamento/Cliente/TipoEntrega/Step/ModoCheckout); handles cart, login, registration, OAuth return, guest checkout, CEP lookup, freight, payment, and a 3-step wizard. Bug-prone enough to warrant its own 423-LOC test file.
- **Impact:** Untestable, unsafe to change, high render cost, prime defect site.
- **Status:** OPEN

---

### C5 — No Error Boundaries anywhere — Critical · Both
- **Problem:** There are no React error boundaries anywhere in the app.
- **Evidence summary:** `ErrorBoundary|componentDidCatch|getDerivedStateFromError` → 0 matches; not present in `main.tsx` or `App.tsx`, though the spec lists `components/common/ErrorBoundary/`.
- **Impact:** Any render-time throw unmounts the whole React tree to a blank screen with no recovery. Combined with heavy any (H1), crash risk is real.
- **Status:** OPEN

---

### C6 — Dashboard, Inventory, Sales, Financial (and Config) are placeholders — Critical (scope) · Both
- **Problem:** Dashboard, Estoque, Vendas, Financeiro, and Configurações are placeholders, not implementations.
- **Evidence summary:** `DashboardPage.tsx` uses hardcoded mockStats/mockAlerts and a "Gráfico será implementado em breve" placeholder with no API calls; `FinanceiroPage.tsx`, `EstoquePage.tsx`, `VendasPage.tsx` are 44-line "coming soon" screens; Configurações pages are 26–27-line stubs. Graphify clustered these stubs with shared infra (Comm. 42).
- **Impact:** 5 of the 11 functional modules in audit scope are non-functional; the architecture of those modules effectively does not exist yet.
- **Status:** OPEN

---

### H1 — Pervasive any and stringly-typed money; duplicated/conflicting domain & ApiError types — High · Both
- **Problem:** Pervasive `any`, stringly-typed money, and duplicated/conflicting domain and ApiError types.
- **Evidence summary:** ~80 any across 29 files (e.g., `catch (error: any)`, `errorLogger.ts` 7×, `useCarrinho.ts` 5×). `ApiError` declared twice with different shapes (`types/common.ts:20` vs `types/auth.ts:46`; axios.ts imports the auth one). Produto/Categoria/Cliente/Endereco redefined inline across pages. Money fields typed as string in `useCarrinho.ts:19-28`. `ProdutosResponse` uses skip/limit, diverging from the unused shared `PaginatedResponse`.
- **Impact:** No DTO/Entity/ViewModel separation; type drift between pages and backend; runtime-shape assumptions that error boundaries (C5) don't catch.
- **Status:** OPEN

---

### H2 — Tables: client-side filtering over a single page + no debounce — High (correctness) · Manual
- **Problem:** Table search/filter runs client-side over only the current page, with no debounce.
- **Evidence summary:** `ProdutosPage.tsx:81-90` filters by search term and category on the client against only the current 10-item page; search is wired into a useEffect (`:53-55`) that refetches on every keystroke with no debounce. No sorting, row selection, or virtualization anywhere.
- **Impact:** Search/filter silently miss matches not on the current page (wrong results); pagination counts misrepresent filtered sets; unnecessary request volume.
- **Status:** OPEN

---

### H3 — Broken/again-stale auth refresh in the interceptor — High · Manual
- **Problem:** The 401 interceptor does not refresh-and-retry; it hard-redirects to login.
- **Evidence summary:** `axios.ts:33-66`: on 401 it declares `_retry` but never sets it, never calls a refresh, never retries the original request — it clears legacy localStorage and sets `window.location.href = '/login'`. `authService.refreshToken` is a deprecated no-op.
- **Impact:** A single expired-access-token 401 on any non-login request hard-redirects the user mid-task (lost form state), even when the refresh cookie may be valid; the "automatic refresh" claim is false in code.
- **Status:** OPEN

---

### H4 — No request cancellation; race conditions on unmount/refetch — High · Both
- **Problem:** No request cancellation, producing race conditions on unmount/refetch.
- **Evidence summary:** `AbortController|signal|CancelToken|abort(` → 0 matches. Manual useEffect fetches (e.g., ProdutosPage on `[currentPage, searchTerm, categoriaFilter, statusFilter]`) set state after await with no abort.
- **Impact:** Fast filter/typing or quick navigation produces out-of-order responses overwriting newer state, plus setState-after-unmount warnings/leaks.
- **Status:** OPEN

---

### H5 — No route-level code splitting — High (perf/spec) · Both
- **Problem:** No route-level code splitting; the whole app ships in one bundle.
- **Evidence summary:** `lazy(`/`Suspense` → 0 matches. `App.tsx:1-24` statically imports all ~30 page modules, including the 1,381-line checkout and unused chart libs.
- **Impact:** Large first-load payload; public storefront users download the entire admin app.
- **Status:** OPEN

---

### H6 — Shared component library is dead code; every page re-implements UI — High · Both
- **Problem:** The shared component library is dead code; pages re-implement UI.
- **Evidence summary:** `ResponsiveTable`/`ResponsiveCard`/`ResponsiveContainer` are exported by `components/common/index.ts` but have zero page imports (only `MaskedInput` is imported, only by CheckoutPage). Graphify isolates them as a disconnected island (Comm. 94). The spec's Button/Modal/Table/Pagination/Loading/ErrorBoundary/Card/Badge/ConfirmDialog mostly don't exist.
- **Impact:** Duplicated raw `<table>`/card/badge/spinner markup in every page, inconsistent UX, no single styling/behavior contract.
- **Status:** OPEN

---

### H7 — Stub feature routes have no permission protection — High (security) · Manual
- **Problem:** Stub feature routes (estoque, vendas, financeiro) have no permission protection, and role checks are duplicated.
- **Evidence summary:** `App.tsx:174-181`: estoque, vendas, financeiro are reachable by any authenticated user; only `configuracoes/*` is wrapped in `RoleProtectedRoute`. Three independent role-check implementations exist: `AuthContext.hasRole` (`AuthContext.tsx:71`), `RoleProtectedRoute` (`RoleProtectedRoute.tsx:20`), `Sidebar.canViewItem` (`Sidebar.tsx:133`). Permissions are coarse (ADMIN/OPERADOR only); no action-level gating.
- **Impact:** Inconsistent enforcement; when these modules are built, the access model is undefined and duplicated logic will drift.
- **Status:** OPEN
