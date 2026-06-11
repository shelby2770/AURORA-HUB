# Aurora Hub

CS MCQ practice app for Dhaka University CS MSc admission prep (the exam is 100% MCQ).
Mobile-first, dark-mode, single user (no auth yet).

- **Web plan & phases:** [`PLAN.md`](./PLAN.md)
- **Mobile (Android + iOS) plan:** [`MOBILE.md`](./MOBILE.md)

> **Status:** the web app is **stable** (Phase 6 complete — full `pytest` + Playwright suites green).
> Native/mobile work begins next, per [`MOBILE.md`](./MOBILE.md).

## Monorepo layout

```
Aurora_Hub/
  frontend/   Next.js 15 App Router, TS, Tailwind, static export (Capacitor-ready)
  backend/    FastAPI async, Beanie 2.x (PyMongo async driver), Pydantic v2, MongoDB
```

The two planes never cross on the hot path:

- **Serving** — plain Mongo reads of *verified* questions; exemplars-first; never blocks on an LLM.
- **Authoring** (offline) — few-shot generation → execute/cross-check verification → embedding dedup.

## Prerequisites

- Node 22, Python 3.12, MongoDB 8 running locally (`mongodb://localhost:27017`).

## Setup

```bash
cp .env.example backend/.env                              # fill in keys (see Providers below)
echo 'NEXT_PUBLIC_API_BASE_URL=http://localhost:8000' > frontend/.env.local
```

## Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"          # core + test deps
pip install -e ".[llm]"          # authoring plane: google-genai + groq SDKs (only if generating)
uvicorn app.main:app --reload --port 8000     # http://localhost:8000  (OpenAPI docs at /docs)
pytest                                         # backend tests (spins up an ephemeral mongod)
```

Seed the database before serving or authoring:

```bash
python -m app.scripts.seed       # 9 courses + subtopics (idempotent)
```

## Frontend (web)

```bash
cd frontend
npm install
npm run dev          # dev server at http://localhost:3000
npm run build        # static export → frontend/out/
npm run test:e2e     # Playwright (auto-runs `next build` first, serves out/, API mocked)
```

> The app is a **static export** (`output: 'export'`). Routing is verified against the built
> `out/` (the e2e suite serves it) — `next dev` does not exercise the trailing-slash paths the
> static build uses.

## Authoring plane — providers

The authoring plane is the **only** place LLMs are used; it never touches the serving hot path.
Configure it in `backend/.env` (template in [`.env.example`](./.env.example)):

| Role | Default | Env | Notes |
|------|---------|-----|-------|
| Generator | Gemini | `LLM_GENERATOR_PROVIDER=gemini`, `GEMINI_API_KEY` | Google AI Studio |
| Cross-check verifier | Groq | `LLM_VERIFIER_PROVIDER=groq`, `GROQ_API_KEY` | independent re-solve; set `GROQ_VERIFIER_MODEL` |
| Embeddings (dedup) | Gemini | `LLM_EMBEDDING_PROVIDER=gemini` | Groq/Claude have **no** embeddings API |

Generator and verifier **should differ** so the verification re-solve is genuinely independent.
Claude stays pluggable (`=claude` + `ANTHROPIC_API_KEY`) but needs no key for the default stack.

## Authoring run steps

```bash
# 1. Ingest provided exemplars (PYQs / notes) as high-quality anchors.
#    Accepts .txt/.md/.json files or directories. Computable items are spot-verified
#    by execution; key mismatches are FLAGGED for your review (not trusted blindly).
python -m app.scripts.ingest_exemplars ./path/to/exemplars/

# 2. Few-shot generate + verify + dedup new questions for one subtopic & difficulty.
#    Computable items are executed; others are cold cross-checked; near-duplicates dropped.
python -m app.scripts.generate <course-slug> <subtopic-slug> <difficulty> <n>
#    e.g. python -m app.scripts.generate operating-systems virtual-memory-page-replacement medium 10
```

The same generation flow is exposed async over HTTP: `POST /authoring/generate` → `202` + job id,
poll `GET /authoring/jobs/{id}`.

## Scripts

| Script | Purpose |
|--------|---------|
| `python -m app.scripts.seed` | Seed 9 courses + subtopics (idempotent) |
| `python -m app.scripts.author_questions [json]` | Load hand-authored exemplar questions (default `data/authored_questions.json`, idempotent) |
| `python -m app.scripts.ingest_exemplars <path>…` | Ingest provided PYQs/notes → exemplars |
| `python -m app.scripts.generate <course> <subtopic> <difficulty> <n>` | Few-shot generate + verify + dedup |

## Mobile (Capacitor)

See [`MOBILE.md`](./MOBILE.md). Daily build command (web is stable, so this can begin):

```bash
nvm use 22 && cd frontend && npm run build && npx cap sync android
```
