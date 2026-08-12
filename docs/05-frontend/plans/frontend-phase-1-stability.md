---
id: PLAN-frontend-phase-1-stability
type: plan
domain: frontend
status: active
source: AUD-2026-06-29-frontend
addresses: [C5, H3, H2, M1, M2, H7]
---

# Frontend Phase 1 — Stop the bleeding (Critical correctness & resilience)

Structural segmentation of the AUD-2026-06-29 prioritized backlog. Items mapped directly; no interpretation or expansion.

- **C5** Introduce error boundaries (app shell + per-route) — crash containment.
- **H3** Fix the 401/refresh interceptor (real refresh-and-retry vs. hard redirect).
- **H2** Server-side search/filter/pagination contract for tables (correctness bug).
- **M1** Remove the hardcoded distribuidora-central / default tenant slugs.
- **M2** Strip cookie/debug `console.*` from production paths.
- **H7** Define and apply route/action permission model to all real modules.
