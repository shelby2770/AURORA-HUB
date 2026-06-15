# Deploying Aurora Hub (backend + MongoDB, live)

Backend → **Render** (free web service). Database → **MongoDB Atlas** (free M0).
The repo already includes a [`render.yaml`](render.yaml) blueprint.

---

## 1. MongoDB Atlas (the live database)

1. Create an account at <https://www.mongodb.com/cloud/atlas/register>.
2. **Build a Database → M0 (Free)**. Pick a cloud/region near your users (e.g. AWS, Mumbai `ap-south-1`).
3. **Database Access** → Add a database user (username + strong password). Save these.
4. **Network Access** → Add IP `0.0.0.0/0` (allow from anywhere).
   Render's free tier has no static outbound IP, so allow-all is required here.
   Security comes from the user/password + the random `mongodb+srv` host.
5. **Connect → Drivers** → copy the connection string. It looks like:
   ```
   mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority
   ```
   Replace `USER`/`PASSWORD` with the credentials from step 3. This is your `MONGODB_URI`.

> The app already speaks `mongodb+srv` (PyMongo `AsyncMongoClient` in
> [backend/app/core/db.py](backend/app/core/db.py)) — no code change needed.

---

## 2. Seed the live database (run once, from your machine)

The serving API reads questions from the DB, so load content into Atlas before
(or right after) deploying. `load_all` is idempotent — safe to re-run.

```bash
cd backend
source .venv/bin/activate
export MONGODB_URI="mongodb+srv://USER:PASSWORD@cluster0.xxxxx.mongodb.net/?retryWrites=true&w=majority"
export MONGODB_DB="aurora_hub"
python -m app.scripts.load_all
```

This seeds the course/subtopic taxonomy and loads every authored question set
from `backend/data/*.json` into Atlas.

---

## 3. Deploy the backend to Render

1. Push your repo to GitHub (the `render.yaml` must be committed).
2. Go to <https://dashboard.render.com> → **New → Blueprint** → connect this repo.
3. Render reads `render.yaml` and creates the `aurora-hub-backend` web service.
4. When prompted, fill the secret env vars (these are `sync: false`):
   - `MONGODB_URI` — the Atlas string from step 1.5
   - `GEMINI_API_KEY`, `GROQ_API_KEY` — only if you'll run authoring/ingestion in
     the cloud; the quiz-serving endpoints don't need them.
5. **Create** → first build runs `pip install -e .` then starts uvicorn.
6. Your API is live at `https://aurora-hub-backend.onrender.com`.
   Verify: `https://aurora-hub-backend.onrender.com/health` → `{"status":"ok",...}`
   API docs: `/docs`.

### Free-tier note
Render free web services **sleep after 15 min idle**; the next request cold-starts
in ~30–60s. Fine for a demo/portfolio. To avoid sleep, upgrade to the Starter
plan ($7/mo) or switch to Railway/Fly.

---

## 4. Wire up the frontend (when you deploy it)

Add the frontend's live origin to `CORS_ORIGINS` in the Render dashboard
(comma-separated), e.g.:
```
https://aurora-hub.vercel.app,http://localhost:3000
```
and point the frontend at the API with
`NEXT_PUBLIC_API_BASE_URL=https://aurora-hub-backend.onrender.com`.

---

## Quick reference

| Piece     | Where                | Cost      |
|-----------|----------------------|-----------|
| Database  | MongoDB Atlas M0     | Free      |
| Backend   | Render web service   | Free*     |
| Secrets   | Render env vars      | —         |

\* sleeps when idle on the free plan.
