# PRD — StadiumPulse
### GenAI Smart Stadium & Tournament Operations Platform
**Challenge:** PromptWars Virtual — Challenge 4: Smart Stadiums & Tournament Operations
**Event context:** FIFA World Cup 2026

*(corrected: added explicit zero-cost constraint; see §8. No other section changed —
original scope/goals/features were already vendor-agnostic.)*

---

## 1. Problem

Large tournament venues juggle two failure points simultaneously:
- **Fans** get lost, miss gates, can't navigate in their language, don't know accessible routes.
- **Ops staff** get incident/crowd/transport signals from a dozen disconnected sources with no correlated, actionable view.

StadiumPulse solves both with one GenAI core: a multi-agent orchestrator for staff, and a multilingual conversational navigator for fans — sharing the same real-time venue data layer.

## 2. Users

| Persona | Need |
|---|---|
| Fan (any language) | Find gate/seat/restroom/exit fast, know crowd conditions, get transit ETA |
| Fan with accessibility needs | Wheelchair-safe routing, screen-reader-first responses |
| Volunteer | Know where to be dispatched, get task context instantly |
| Venue ops staff | Correlated real-time view: crowd density + incidents + transport, with GenAI-generated recommended actions |
| Tournament organizer | Post-event/ongoing operational intelligence briefings |

## 3. Goals

1. Cut fan wayfinding confusion via multilingual GenAI chat/voice assistant.
2. Give ops staff a single correlated real-time decision-support view instead of siloed feeds.
3. Auto-generate recommended actions (not just alerts) — e.g. "Gate C density 92%, reroute incoming to Gate D, dispatch 2 volunteers."
4. Demonstrate GenAI covering ≥4 of the 8 challenge categories: navigation, crowd management, accessibility, multilingual assistance, operational intelligence, real-time decision support (transportation + sustainability as stretch).

## 4. Core Features

### 4.1 Fan Navigator (fan-facing)
- Chat + voice interface, auto-detects/switches language (NIM translation).
- RAG over venue data: gates, seating map, amenities, exits, accessibility routes.
- Live crowd heatmap overlay per zone.
- Transit ETA to next kickoff / from current location.
- Accessibility mode: wheelchair-routing, screen-reader-optimized responses, larger-touch-target UI.

### 4.2 Ops Orchestrator (staff-facing)
- Multi-agent backend, each agent owns one signal stream:
  - Crowd density agent (simulated sensor/CV feed)
  - Transport delay agent
  - Incident report agent (volunteer/staff submitted)
- Orchestrator step correlates signals deterministically → GenAI generates only the human-readable recommended-action text, ranked by a deterministic severity score.
- Dispatch sub-system: deterministic + GenAI hybrid ranking of nearest/best-fit available volunteer (reuse of prior ranking methodology).
- Live dashboard: zone map, active incidents, recommended actions queue, one-click "dispatch."

### 4.3 Shared layer
- Single venue knowledge base (RAG store) feeds both Navigator and Orchestrator.
- WebSocket/SSE push for real-time updates on both sides.

## 5. User Stories

- As a fan, I ask "where's the nearest accessible restroom" in Spanish and get a routed answer in Spanish.
- As a fan, I ask "is Gate B crowded" and see a live heatmap + suggested alternate gate.
- As ops staff, I see a correlated alert: "Zone 3 density 89% + 12-min transit delay → recommend early gate opening, dispatch 3 volunteers" instead of three separate raw alerts.
- As a volunteer, I get pushed a dispatch with location + task, ranked as best-fit by proximity + skill tag.

## 6. Success Metrics (demo-measurable)

- Navigator: correct multilingual answer rate on a test query set (target ≥90%).
- Orchestrator: time from raw signal → recommended action shown (target <5s in demo).
- Coverage: demo touches navigation, crowd mgmt, accessibility, multilingual, operational intelligence, real-time decision support.

## 7. Scope

**In scope (hackathon window):** Navigator chat UI, Orchestrator dashboard, 3 agent types, simulated live data feeds, RAG venue KB, dispatch ranker.

**Out of scope:** Real sensor/CV hardware integration, production auth/SSO, real transit API integration (mock/stub instead), multi-stadium scaling.

## 8. Constraints

- Hackathon timebox — prioritize working demo over completeness.
- Same platform (Hack2skill) previously flagged a submission for plagiarism via Git Blob detector → **all code must be freshly written, no reused repo files from prior projects**, even though architecture patterns are reused conceptually.
- **Zero-cost GenAI constraint (added):** the entire stack must run on genuinely free tiers, no credit card, no billing-enabled account anywhere in the chain. This ruled out Gemini/Vertex AI (needs a billing-enabled GCP project past a small quota) and the Claude API (no free tier at all). NVIDIA NIM is the sole GenAI vendor — free signup credits, no card — for both translation and reasoning. Embeddings run locally via sentence-transformers, so RAG has no per-call cost either.
- Dev environment: primary build/test machine is Windows, via Docker Desktop (WSL2 backend) — no native Linux assumed anywhere in setup or run instructions.

## 9. Assumptions

- Live sensor/transit feeds are simulated with seeded/randomized data generators for demo purposes.
- Single stadium scope for MVP; multi-venue mentioned as future work in pitch.
- NVIDIA NIM's free-tier rate limit (~40 req/min) is sufficient for a live demo audience size; not sized for production traffic.
