# Aurora Hub

CS MCQ practice app for Dhaka University CS MSc admission prep (exam is 100% MCQ).
Mobile-first, dark-mode, single user (no auth yet).

- **Web plan & phases:** [`PLAN.md`](./PLAN.md)
- **Mobile (Android + iOS) plan:** [`MOBILE.md`](./MOBILE.md)

## Monorepo layout

```
Aurora_Hub/
  frontend/   Next.js 15 App Router, TS, Tailwind, static export, Capacitor
  backend/    FastAPI async, Beanie/Motor, Pydantic v2, MongoDB, scripts
```

## Prerequisites

- Node 22, Python 3.12, MongoDB 8 running locally (`mongodb://localhost:27017`).

## Setup

```bash
cp .env.example backend/.env          # fill in keys
echo 'NEXT_PUBLIC_API_BASE_URL=http://localhost:8000' > frontend/.env.local
```

## Backend (FastAPI)

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"                        # add ,llm for the authoring plane (gemini/claude SDKs)
uvicorn app.main:app --reload --port 8000     # http://localhost:8000  (docs at /docs)
pytest                                         # run backend tests (uses an ephemeral mongod)
```

## Frontend (web)

```bash
cd frontend
npm install
npm run dev          # http://localhost:3000
npm run build        # static export → frontend/out/
```

## Scripts (added in later phases)

| Script | Purpose | Phase |
|--------|---------|:----:|
| `python -m app.scripts.seed` | Seed 9 courses + subtopics | 1 |
| `python -m app.scripts.ingest_exemplars` | Ingest provided PYQs/notes → exemplars | 4 |
| `python -m app.scripts.generate` | Few-shot generate + verify + dedup | 5 |

## Mobile (Capacitor)

See [`MOBILE.md`](./MOBILE.md). Daily build command (after web is stable):

```bash
nvm use 22 && cd frontend && npm run build && npx cap sync android
```
