---
id: ARCH-frontend-current-state
type: architecture
domain: frontend
status: active
source: AUD-2026-06-29-frontend
---

# Frontend — Current State (factual)

Factual current-state characteristics extracted from AUD-2026-06-29 evidence. No redesign, no recommendations.

**Reconstructed shape:** `App.tsx` (static route table) → page components → (directly) Axios, with a thin `AuthContext` for global auth state and a single real custom hook (`useCarrinho`). The intended Component → React Query hook → API service → Axios data-flow does not exist.

## Duplicated API clients
- `axios.create` in 12 files: canonical `services/api/axios.ts:7` plus 11 `apiPublica` copies in `useCarrinho.ts:5`, `CheckoutPage.tsx:14`, `GoogleCallback.tsx:7`, MicrosoftCallback, ClienteLoginPage, ClientePerfilPage, MeusPedidosPage, RastreamentoPedidoPage, ProdutoDetalhePage, LojaOnlinePublicoPage, ClienteLayout.
- Canonical client uses `baseURL: env.apiUrl`; every `apiPublica` hardcodes `baseURL: '/api'`. Only CheckoutPage's copy adds a response interceptor; the others have none.
- (Evidence: C3)

## Absence of React Query usage
- `useQuery|useMutation|useQueryClient|useInfiniteQuery` → 0 matches in src.
- `QueryClientProvider` with staleTime/gcTime/retry is configured in `main.tsx:15-24` but unused. React Query hooks used: 0.
- Data fetching is implemented ad hoc with useState/useEffect. Graphify shows no React-Query hook nodes anywhere in the frontend.
- (Evidence: C1)

## Lack of error boundaries
- `ErrorBoundary|componentDidCatch|getDerivedStateFromError` → 0 matches. Not present in `main.tsx` or `App.tsx`. Error boundaries: 0.
- (Evidence: C5)

## Direct API calls in components
- 84 `api.*`/`apiPublica.*` calls across 23 files (e.g., `ProdutosPage.tsx:59`, `ClienteFormPage.tsx` 7 calls, `CheckoutPage.tsx` 12 calls).
- (Evidence: C2)

## Missing service layer
- The spec's `services/api/{clientes,produtos,vendas,estoque,financeiro}Api.ts` modules do not exist — `services/api/` contains only `axios.ts`. No service god-node in Graphify.
- Endpoints, params, and DTO shapes are inlined in components.
- (Evidence: C2)

## God components
- `CheckoutPage.tsx` — 1,381 LOC (largest file by 3×, ~14% of all frontend code), 28 useState, inline `apiPublica` + interceptor, inline types (ClienteNovo/Endereco/Pagamento/Cliente/TipoEntrega/Step/ModoCheckout); handles cart, login, registration, OAuth return, guest checkout, CEP lookup, freight, payment, and a 3-step wizard.
- Files > 300 LOC: 5 (Checkout, ClienteForm 438, ClienteEnderecos 345, ClienteCredito 327, Produtos 308).
- (Evidence: C4)

## Stub modules
- `DashboardPage.tsx` uses hardcoded mockStats/mockAlerts and a "Gráfico será implementado em breve" placeholder — no API calls.
- `FinanceiroPage.tsx`, `EstoquePage.tsx`, `VendasPage.tsx` are 44-line "coming soon" screens; Configurações pages are 26–27-line stubs.
- 5 of the 11 functional modules in audit scope are non-functional. Graphify clustered these stubs with shared infra (Comm. 42), not their domains.
- (Evidence: C6)
