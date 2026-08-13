---
id: PLAN-frontend-phase-2-architecture
type: plan
domain: frontend
status: active
source: AUD-2026-06-29-frontend
addresses: [C1, C2, C3, H1, H4]
---

# Frontend Phase 2 — Establish the missing architecture (Critical structural)

Structural segmentation of the AUD-2026-06-29 prioritized backlog. Items mapped directly; no interpretation or expansion.

- **C1 + C2 + C3** Adopt the intended layering: a single shared API client + per-domain service modules + React Query hooks; eliminate the 11 apiPublica copies and 84 inline calls.
- **H1** Centralize domain types (DTO/Entity/ViewModel), dedupe ApiError, retire any from catch/data paths, fix string-typed money.
- **H4** Request cancellation (delivered for free once RQ adoption lands).
