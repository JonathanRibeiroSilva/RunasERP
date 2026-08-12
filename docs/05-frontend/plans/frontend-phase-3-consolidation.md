---
id: PLAN-frontend-phase-3-consolidation
type: plan
domain: frontend
status: active
source: AUD-2026-06-29-frontend
addresses: [C4, H6, M3, H5, M4]
---

# Frontend Phase 3 — Decompose & consolidate (High maintainability/UX)

Structural segmentation of the AUD-2026-06-29 prioritized backlog. Items mapped directly; no interpretation or expansion.

- **C4** Break up CheckoutPage into step components + hooks.
- **H6 + M3** Build/adopt the real shared component library (Table, Pagination, ConfirmDialog, Loading/Empty/Error, Badge), retire dead Responsive* or fold their logic in, unify on one toast abstraction.
- **H5** Route-level code splitting (lazy/Suspense).
- **M4** Wire structured logging + error reporting (Sentry) app-wide; generalize logCheckoutError.
