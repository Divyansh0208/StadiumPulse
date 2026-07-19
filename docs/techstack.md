# Tech Stack — StadiumPulse
*(corrected: fully free-tier stack, single GenAI vendor)*

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
│ (chat/voice)       │    │ (map + alert queue)│
└────────────────────┘    └─────────────────────┘
```

## Backend

- **FastAPI** — both Navigator and Orchestrator APIs.
- **Multi-agent orchestration** — 3 signal agents (crowd, transport, incident), rule-based/deterministic correlation in code + 1 orchestrator step that calls GenAI only for the human-readable action text.
- **NVIDIA NIM** — single GenAI vendor for **both** translation and reasoning (recommended-action text, navigator answers, dispatch tie-break explanations). Free tier: no card, ~1,000 free inference credits on signup, ~40 req/min. `build.nvidia.com`.
  - ~~Gemini (Vertex AI)~~ — **removed.** Requires a billing-enabled GCP project for anything beyond a small, shrinking free quota; not reliably free.
  - ~~Claude API fallback~~ — **removed.** No standing free tier, pay-per-token from first call.
- **sentence-transformers** — local, free, open-weight embeddings for venue KB (no API cost, runs on CPU).
- **pgvector (PostgreSQL)** — RAG vector store for venue data (gates, seating, amenities, accessibility routes).
- **WebSockets / SSE** — real-time push to both dashboards.

## Frontend

- **React + Vite** — both Fan Navigator chat UI and Ops Dashboard.
- Fan UI: chat + voice input (browser Web Speech API, free/no key), heatmap overlay (canvas/SVG zone map), large-touch accessibility mode.
- Ops UI: zone map, live alert queue, one-click dispatch action, incident timeline.

## Dispatch Ranker

- Deterministic scoring (proximity + skill tag match), computed entirely in code — no GenAI call required for the ranking itself. NIM only generates a short explanation sentence on ties.

## Data / Simulation

- Seeded random generators for crowd density, transport delay, incident reports — replaces real sensor/CV/transit API for demo purposes. Zero cost, no external calls.
- Venue KB seeded as structured JSON → embedded into pgvector at startup via local sentence-transformers model (downloaded once, then fully offline).

## Infra

- **Docker Desktop (Windows)** — local dev, runs all services via Docker Compose. Uses WSL2 backend automatically; no manual Linux setup needed.
- **Render (free web service tier) or local-only demo** — deployment target. Avoid Cloud Run for the free-tier constraint — Cloud Run itself is pay-per-use beyond a free quota, fine for light demo traffic but not "completely free" the way Render's free tier / local demo is.
- **GitHub** — fresh repo, clean commit history (no copied files from prior projects, per platform's plagiarism-detector history).

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
| Realtime | FastAPI WebSockets or SSE | free/OSS |
| DB | PostgreSQL | free/OSS |

## What changed from the original draft

1. **Removed Gemini (Vertex AI)** as reasoning engine — not free at meaningful scale, needs billing enabled.
2. **Removed Claude API fallback** — paid, no free tier.
3. **Consolidated all GenAI calls onto NVIDIA NIM** — one key, one vendor, genuinely free tier, no card.
4. **Dropped "LangGraph or CrewAI-style graph"** framing for the agents — replaced with plain deterministic Python correlation (agents already didn't need a graph framework's runtime; adding one added a dependency with no free-tier implication either way, but it also added complexity the demo doesn't need).
5. Deployment note added: Cloud Run is pay-per-use past a quota, not flatly free — prefer Render free tier or local-only for a zero-cost demo.
