# StadiumPulse

GenAI Smart Stadium & Tournament Operations Platform. PromptWars Challenge 4.

100% free stack — single GenAI vendor (NVIDIA NIM, free tier, no card), local
embeddings, free/OSS everything else. Built with actual production hygiene, not
just a demo shell: real auth, retries, rate limiting, structured logging, tests, CI.

## 1. Install Docker Desktop (Windows)

1. Download: https://www.docker.com/products/docker-desktop/
2. Run installer, keep "Use WSL 2 instead of Hyper-V" checked (default).
3. Open Docker Desktop, wait for "Engine running".
4. Verify: `docker --version` and `docker compose version`

## 2. Get a free NVIDIA NIM key

1. https://build.nvidia.com → sign in (free, no card) → profile → Generate API Key
2. Free tier: ~1,000 inference credits on signup, ~40 requests/min

## 3. Run

```powershell
Expand-Archive stadiumpulse.zip -DestinationPath .
cd stadiumpulse
Copy-Item .env.example .env
notepad .env      # paste your nvapi-... key, optionally change SEED_STAFF_PASSWORD
docker compose up --build
```

The `seed` service runs once: embeds `data/venue_kb.json` into pgvector, seeds demo
volunteers, and creates the ops-dashboard staff login (hashed password, not
hardcoded — see §Auth below).

Open:
- Fan chat → http://localhost:5173
- Ops dashboard → http://localhost:5174 (login via `SEED_STAFF_USERNAME` /
  `SEED_STAFF_PASSWORD` from your `.env`, defaults `staff` / `demo`)
- Navigator API docs → http://localhost:8001/docs
- Orchestrator API docs → http://localhost:8002/docs

Stop: `docker compose down` (add `-v` to also wipe the DB volume).

## Manual (non-Docker) setup

For local development with hot-reload outside containers:

```powershell
py -3.12 -m venv venv          # 3.13 currently lacks a psycopg2-binary wheel
venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt

docker run -d --name stadiumpulse-pg -e POSTGRES_USER=stadium -e POSTGRES_PASSWORD=stadium -e POSTGRES_DB=stadiumpulse -p 5432:5432 ankane/pgvector

$env:PYTHONPATH="."
$env:VENUE_KB_PATH="data\venue_kb.json"
python -m backend.shared.seed

uvicorn backend.navigator.app.main:app --port 8001 --reload
# new terminal, same venv:
uvicorn backend.orchestrator.app.main:app --port 8002 --reload
```

Frontends: `cd frontend\fan-ui && npm install && npm run dev` (repeat for `ops-ui`).

`.env` is auto-loaded via `python-dotenv` — no need to set env vars manually if
it's in the project root.

## Testing

```powershell
pip install -r backend\requirements.txt   # includes pytest
pytest -v
```

14 unit tests, no DB or network required — they exercise pure logic directly:
dispatch-ranker scoring, password hashing/JWT roundtrip, rate-limit middleware
behavior. Run from the project root (not `backend\`) — `pytest.ini` sets
`pythonpath = .` so `backend.X` imports resolve correctly.

## CI

`.github/workflows/ci.yml` runs on every push/PR: backend tests + lint (ruff,
non-blocking for now), and a build check for both frontend apps. Push this repo
to GitHub and it runs automatically — no secrets needed since tests don't touch
NIM or a live DB.

## Auth

Ops dashboard login is a real DB-backed user (`StaffUser` model, bcrypt-hashed
password via `passlib`), not a hardcoded string comparison. The seed script
creates one default user from `SEED_STAFF_USERNAME`/`SEED_STAFF_PASSWORD` env
vars — **change the password before sharing this beyond your own machine**, since
the repo's `.env.example` default (`demo`) is public.

## Reliability

- NIM calls retry with exponential backoff (3 attempts) on timeouts/5xx/429 via
  `tenacity`, instead of failing on the first blip.
- If NIM is genuinely down after retries: `/ask` returns a proper `503` with a
  human-readable message instead of a stack trace; `translate()` degrades to
  returning the original text rather than failing the whole request.
- Per-IP rate limiting (in-memory, no Redis needed) protects the free NIM quota
  from being exhausted by one client — configurable via `RATE_LIMIT_PER_MINUTE`.

## Config

All settings centralized in `backend/shared/config.py` (pydantic-settings) —
validated at startup, one place to see every env var the app reads. See
`.env.example` for the full list with comments.

## Frontend

Both apps share a dark stadium-themed design system (navy background, turf-green
accent, amber/crimson severity colors, Oswald headers + Inter body text).

- **Fan Navigator** (`fan-ui`) — multilingual chat assistant for wayfinding,
  accessibility routing, and crowd conditions, plus an interactive SVG stadium
  map (`StadiumMap.jsx`) showing live per-zone crowd density from `/heatmap`,
  color-coded green/amber/crimson and clickable per gate.
- **Ops Orchestrator** (`ops-ui`) — staff dashboard showing GenAI-correlated
  recommended actions per zone, ranked by severity, with source-signal detail
  and live refresh.

Icons via `lucide-react` in both apps.

## Structure

```
backend/
  shared/         # config, db models/session, logging, rate limiting, KB + staff seeding
  navigator/      # Fan Navigator: RAG + NIM translation/reasoning + chat API
  orchestrator/   # Ops Orchestrator: 3 signal agents + correlation + severity
                  # scoring + dispatch ranker + auth
  tests/          # pytest unit tests (dispatch ranker, auth, rate limiting)
frontend/
  fan-ui/         # React chat UI + interactive stadium map, accessibility mode
  ops-ui/         # React staff dashboard, JWT login
data/
  venue_kb.json   # seed venue knowledge base
docs/
  PRD.md          # corrected PRD (zero-cost constraint, §8)
  techstack.md    # corrected tech stack (Gemini/Claude removed, NIM-only)
.github/workflows/ci.yml   # test + lint + build on push
```

## Cost breakdown

| Component | Cost |
|---|---|
| NVIDIA NIM (translation + reasoning) | Free tier, no card |
| sentence-transformers embeddings | Free, runs locally |
| PostgreSQL + pgvector | Free, OSS |
| React/Vite/Tailwind frontend | Free, OSS |
| Docker Desktop | Free for personal/small business use |
| GitHub Actions CI | Free for public repos (2,000 min/month private) |

## Known limitations (honest, not swept under the rug)

This is a strong portfolio piece, not a production stadium system. Specifically
still missing before real deployment:

- **Simulated data only** — crowd/transport/incident feeds are seeded random
  generators, no real sensor/CV/transit integration (explicitly out of scope
  per PRD).
- **No DB migrations** — uses `Base.metadata.create_all()`, fine for a from-
  scratch demo DB, not for evolving a real production schema. Alembic would be
  the next step.
- **No HTTPS/TLS** — plain HTTP for local/demo use.
- **No horizontal scaling** — single process each, no load balancer.
- **WebSocket endpoint exists but isn't pushed to yet** — client polls; real
  push wiring is a follow-up.
- **In-memory rate limiter** — fine for one process; a multi-instance
  deployment would need Redis-backed limiting instead.
- **No refresh tokens** — JWT expires after 8 hours, no refresh flow, staff
  just re-logs in.
- **Volunteer dispatch not yet in the ops-ui** — `/dispatch/rank` and
  `/dispatch/{volunteer_id}` are implemented and unit-tested but not yet
  surfaced as a UI panel; usable today via the API docs at `/docs`.

## What changed from the original draft (see docs/)

- Dropped Gemini/Claude — not free at meaningful scale; NIM is the sole vendor.
- Added real auth, retries, rate limiting, structured logging, centralized
  config, and a real pytest suite + CI — none of which existed in the original
  hackathon-scoped draft.
- Full visual redesign of both frontends (dark stadium theme) plus a new
  interactive live stadium map on the fan-ui side.