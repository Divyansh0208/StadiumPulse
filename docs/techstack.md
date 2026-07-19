# Tech Stack — StadiumPulse
*(corrected: fully free-tier stack, single GenAI vendor. Also updated Infra
and Frontend sections below to reflect the final build — local Docker Compose
only, no Render deployment was actually done; UI redesign details added.)*

## Architecture

```
                     ┌─────────────────────┐
                     │   Venue Data Layer    │
                     │ PostgreSQL + pgvector │
                     │ (venue map, amenities,│
                     │  routes, live feeds)  │
                     └──────────┬────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
┌───────▼────────┐     ┌────────▼─────────┐   ┌─────────▼────────┐
│  Fan Navigator   │     │  Ops Orchestrator │   │  Simulated Feeds  │
│  (FastAPI + RAG) │     │  (multi-agent)    │   │  (crowd/transport/│
│                  │     │                   │   │   incident gen)   │
└───────┬──────────┘     └────────┬──────────┘   └───────────────────┘
        │                         │
┌───────▼──────────┐    ┌─────────▼──────────┐
│ React Fan Chat UI │    │ React Ops Dashboard │
│ (chat + live map)  │    │ (map + alert queue)│
└────────────────────┘    └─────────────────────┘
```

## Backend

- **FastAPI** — both Navigator and Orchestrator APIs.
- **Multi-agent orchestration** — 3 signal agents (crowd, transport, incident), rule-based/deterministic correlation in code + 1 orchestrator step that calls GenAI only for the human-readable action text.
- **Severity scoring** — each signal type (crowd density, transport delay,
  incident severity) is scaled independently to a 0–10 range; the final
  severity is the worst single signal, with a small additive bump for
  multiple concurrent signals. This replaced an earlier fixed-weight sum
  that under-weighted crowd density and could never reach "high" severity
  from crowd alone — a bug caught during manual testing (a 95%+ density
  zone was scoring "Low" while the GenAI action text correctly said
  "evacuate immediately").
- **NVIDIA NIM** — single GenAI vendor for **both** translation and reasoning (recommended-action text, navigator answers, dispatch tie-break explanations). Free tier: no card, ~1,000 free inference credits on signup, ~40 req/min. `build.nvidia.com`.
  - ~~Gemini (Vertex AI)~~ — **removed.** Requires a billing-enabled GCP project for anything beyond a small, shrinking free quota; not reliably free.
  - ~~Claude API fallback~~ — **removed.** No standing free tier, pay-per-token from first call.
- **sentence-transformers** — local, free, open-weight embeddings for venue KB (no API cost, runs on CPU).
- **pgvector (PostgreSQL)** — RAG vector store for venue data (gates, seating, amenities, accessibility routes).
- **WebSockets / SSE** — endpoint exists (`/ws/heatmap`); not yet pushed to by clients in the current build — both frontends currently poll `/heatmap` on a timer instead. Real push wiring is a follow-up.

## Frontend

- **React + Vite** — both Fan Navigator chat UI and Ops Dashboard.
- Shared dark stadium design system: navy background, turf-green accent,
  amber/crimson severity colors, Oswald (headers) + Inter (body) — both apps
  visually match as one product suite.
- **lucide-react** — icon set, used in both `fan-ui` and `ops-ui`.
- Fan UI: chat + voice input (browser Web Speech API, free/no key), plus an
  interactive SVG stadium map (`StadiumMap.jsx`) — gate zones colored by live
  `/heatmap` density, clickable/keyboard-accessible, syncs with chat answer
  citations — and a large-touch accessibility mode.
- Ops UI: zone map, live alert queue with severity badges, collapsible source
  signals, refresh control. One-click dispatch action from the dashboard is
  not yet built (dispatch ranking works at the API level — see Dispatch
  Ranker below); incident timeline not yet built.

## Dispatch Ranker

- Deterministic scoring (proximity + skill tag match), computed entirely in
  code — no GenAI call required for the ranking itself. NIM only generates a
  short explanation sentence on ties.
- **Status:** implemented and unit-tested (`backend/tests/test_dispatch_ranker.py`),
  reachable via `/dispatch/rank` and `/dispatch/{volunteer_id}` in the
  Orchestrator API. Not yet surfaced as a panel in the Ops Dashboard UI —
  usable today through `/docs`, UI wiring is a next step.

## Data / Simulation

- Seeded random generators for crowd density, transport delay, incident reports — replaces real sensor/CV/transit API for demo purposes. Zero cost, no external calls.
- Venue KB seeded as structured JSON → embedded into pgvector at startup via local sentence-transformers model (downloaded once, then fully offline).

## Infra

- **Docker Desktop (Windows)** — local dev and the actual run environment used
  for build, test, and submission. All services run via Docker Compose;
  WSL2 backend used automatically, no manual Linux setup needed.
- **Deployment target:** local-only for this submission. Render's free web
  service tier remains the recommended path if/when a hosted demo is wanted
  later — Cloud Run is intentionally avoided since it's pay-per-use past a
  free quota, not flatly free the way Render's free tier / local demo is.
- **GitHub** — fresh public repo, clean commit history (no copied files from
  prior projects, per platform's plagiarism-detector history). Repo size
  confirmed well under the 10 MB submission cap (`git count-objects -vH`).

## Auth (minimal, hackathon scope)

- JWT for Ops Dashboard staff login only. Fan Navigator stays anonymous/no-auth for demo speed.

## Key Libraries

| Layer | Library | Cost |
|---|---|---|
| API | FastAPI, uvicorn | free/OSS |
| Agents | plain Python (rule-based correlation) | free/OSS |
| Embeddings | sentence-transformers (local) | free/OSS |
| Vector store | pgvector | free/OSS |
| Translation | NVIDIA NIM | free tier |
| Reasoning | NVIDIA NIM | free tier |
| Frontend | React, Vite, Tailwind | free/OSS |
| Icons | lucide-react | free/OSS |
| Realtime | FastAPI WebSockets or SSE (endpoint built, not yet pushed to) | free/OSS |
| DB | PostgreSQL | free/OSS |

## What changed from the original draft

1. **Removed Gemini (Vertex AI)** as reasoning engine — not free at meaningful scale, needs billing enabled.
2. **Removed Claude API fallback** — paid, no free tier.
3. **Consolidated all GenAI calls onto NVIDIA NIM** — one key, one vendor, genuinely free tier, no card.
4. **Dropped "LangGraph or CrewAI-style graph"** framing for the agents — replaced with plain deterministic Python correlation (agents already didn't need a graph framework's runtime; adding one added a dependency with no free-tier implication either way, but it also added complexity the demo doesn't need).
5. Deployment note added: Cloud Run is pay-per-use past a quota, not flatly free — prefer Render free tier or local-only for a zero-cost demo. Final submission uses local-only.
6. **Full dark-theme UI redesign** of both frontends, plus a new interactive
   live stadium map on the fan-ui side (`StadiumMap.jsx`).
7. **Severity scoring bug fixed** — see Backend section above; single
   critical signal (e.g. crowd density) can now reach high severity on its
   own instead of being capped by a fixed-weight sum.
8. **Dispatch ranker UI panel deferred** — API and tests complete, dashboard
   surfacing not done in time for this submission; documented as a known
   next-step rather than silently left out.
