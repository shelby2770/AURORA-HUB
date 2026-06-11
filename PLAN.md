# Aurora Hub — Web Plan (source of truth for the web build)

CS MCQ practice app for Dhaka University CS MSc admission prep (exam is 100% MCQ).
Mobile-first, dark-mode, single user (no auth yet). **The mobile/native build is tracked
separately in [`MOBILE.md`](./MOBILE.md) and is built only after the web version is stable.**

---

## 1. PRD (short)

**What it is.** A mobile-first, dark-mode MCQ practice web app. Single user for now, no auth.

**Core user flow.**
1. Pick a **course** (1 of 9) and optionally a **subtopic**.
2. Pick **count** (10/20/30/40; up to 50 when scope = whole course).
3. Pick **difficulty** (easy/medium/hard/random).
4. Pick **mode**: **Exam** (timed, answers revealed only at the end) or **Practice** (instant feedback + explanation per question).
5. Take the quiz — **one question per screen**, big tap targets, animated transitions, math/code rendered properly.
6. See **score** + **per-question review** (your answer, correct answer, explanation, why each distractor is wrong).

**Hard product rules.**
- Quiz serving never blocks on LLM generation — it's a plain Mongo read of `verified:true` questions.
- Real exam questions (`source:exemplar`) are served **first**, generated ones fill the remaining count.
- Generated questions are guaranteed verified + deduped before they're ever servable.

**Out of scope (now).** Accounts/auth, multi-user, leaderboards, spaced repetition, payment, push.
`userId` is kept optional in the schema so multi-user can be added later without migration.

**Quality bar.** No trivia. Every item is scenario / code-trace / computation based at university level.
Exemplars (real GATE CS PYQs + your notes) are the quality ceiling; generated items test the *same
concepts* as new questions, never reworded clones.

**Defaulted decisions (override if you disagree):**
- Exam timer → **whole-quiz countdown** of `90s × question count`, top bar, auto-submit at 0.
- Embedding dedup → **in-process cosine** over embeddings stored in Mongo (Atlas Vector Search is a drop-in swap behind the same interface).
- LLM providers → **gemini** generator, **groq** cross-check verifier (env-selectable; claude optional). Embeddings → **gemini** (Groq/Claude have no embeddings API).

---

## 2. Architecture

**Monorepo layout**
```
Aurora_Hub/
  frontend/          Next.js 15 App Router, TS, Tailwind, static export, Capacitor
  backend/           FastAPI async, Beanie/Motor, Pydantic v2, scripts
  PLAN.md            (this file — web)
  MOBILE.md          (Android + iOS source of truth)
  README.md
  .env.example
```

**Frontend (client-only SPA).**
- `next.config`: `output:'export'`, `images.unoptimized:true`, `trailingSlash:true`. No SSR, no API routes, no server fetching — every screen is a client component calling FastAPI.
- TanStack Query for all API calls; Zustand for live quiz session state (current index, answers, timer, mode).
- shadcn/ui; **sonner** for all toasts; lucide-react; Framer Motion for transitions; KaTeX/react-katex for math; Shiki (preferred) for code.

**Backend (two clearly separated planes).**
- **Serving plane (hot path):** `/quiz` endpoints do plain Mongo queries by course/subtopic/difficulty, `verified:true` only, exemplars first, capped at requested count. No LLM, no vector search.
- **Authoring plane (offline + optional async):** ingestion script, generation+verification script, optional async "generate N more for subtopic+difficulty" endpoint. LLM adapters, execution-verify, cross-check, and dedup live here.
- **LLM adapter:** `LLMProvider` with `complete()` / `embed()`; concrete `GeminiProvider`, `GroqProvider`, `ClaudeProvider`; env-selected; generator vs verifier differ.
- **Execution-verify sandbox:** runs model-emitted Python checks in a constrained subprocess (no network, time + memory limits, restricted builtins).

**Data flow.** Exemplar corpus → spot-verified by execution, mismatches flagged → authoring retrieves
2–3 exemplars as few-shot anchor → LLM generates new → execute-verify / cross-check → dedup vs
exemplars + existing → persist `generated, verified:true` → serving reads exemplars-first.

---

## 3. Data model (Beanie documents)

- **Course** `{ name, slug, isActive }` — seed 9.
- **Subtopic** `{ courseId, name, slug }` — seeded per course, editable.
- **Question** `{ courseId, subtopicId, difficulty(easy|medium|hard), questionText, codeSnippet?, latex?, options[4], correctIndex(0–3), explanation, distractorRationales[4], source(exemplar|generated), examName?, year?, verified(bool), verifiedBy, embedding?(float[]), createdAt }`.
- **QuizSession** `{ mode, scope{courseId, subtopicId?}, difficulty, questionIds[], answers[], score, startedAt, finishedAt, userId?(optional) }`.

**Indexes:** `Question` on `(courseId, subtopicId, difficulty, verified, source)`; `Course.slug` unique; `Subtopic.(courseId, slug)` unique.

**Seed — 9 courses:** Theory of Computation, Programming, Data Structures & Algorithms, Computer
Architecture, Operating Systems, Computer Networks, DBMS, Distributed Systems, Artificial Intelligence
(each with a sensible, editable subtopic list).

---

## 4. API surface (FastAPI)

- `GET /health`
- `GET /courses` → active courses.
- `GET /courses/{slug}/subtopics`
- `POST /quiz/start` `{courseId, subtopicId?, count, difficulty, mode}` → creates session; correctIndex/explanation **withheld in Exam mode**, included in Practice mode.
- `POST /quiz/{id}/submit` `{answers[]}` → scores, persists, returns full review.
- `POST /authoring/generate` `{subtopicId, difficulty, n}` → async job (authoring plane, optional).

Serving endpoints never leak the answer key to the client during an Exam.

---

## 5. Phase plan (web)

Each phase ends with **tests green + a pause for review** before the next.
One PR per phase minimum; branch naming `web/phase-N-<slug>`.

### Phase 0 — Scaffold & contracts
- Monorepo; both apps boot.
- FastAPI skeleton + `/health`, Mongo connection, Beanie models, Pydantic schemas.
- `.env.example` (Mongo URI, provider keys, model names, similarity threshold), README skeleton.
- Next.js static-export config + Tailwind + shadcn + dark theme + sonner provider.
- **Tests:** pytest health + model round-trip; `next build && export` clean.

### Phase 1 — Data layer & seed
- Course/Subtopic/Question/QuizSession documents, indexes.
- Seed script (9 courses + per-course subtopics), idempotent.
- **Tests:** pytest seed idempotency + index presence.

### Phase 2 — Serving plane
- `/courses`, `/subtopics`, `/quiz/start`, `/quiz/submit`.
- Exemplars-first ordering; count cap (50 only for whole-course scope); Exam vs Practice answer withholding; scoring.
- **Tests:** pytest for ordering, cap rules, answer-withholding, scoring math.

### Phase 3 — Quiz UI (web)
- Config screen → quiz runner (one-per-screen, Framer Motion, KaTeX, Shiki, big tap targets) → results + per-question review.
- Zustand session store, TanStack Query, Exam timer + auto-submit, Practice instant feedback.
- **Tests:** Playwright e2e — config flow, exam timer, practice feedback, scoring.

### Phase 4 — LLM adapters & exemplar ingestion
- `LLMProvider` interface + Gemini/Claude providers.
- Ingestion script (local files / pasted text → categorize → parse to schema → `exemplar, verified:true`).
- Execution-verify sandbox; spot-verify computable exemplars and **flag mismatches** for review.
- **Tests:** pytest with mock provider for parsing/categorization; sandbox executes a known check + rejects a wrong key.

### Phase 5 — Generation + verification + dedup
- Few-shot anchored generator (thinking on, no-trivia system prompt, worked explanation + distractor rationales).
- Execute-verify computable answers; cross-check non-computable with a *different* model.
- Embedding dedup (cosine in Mongo) vs exemplars + existing generated; persist survivors `generated, verified:true`.
- Wire optional async `POST /authoring/generate`.
- **Tests:** pytest — verifier discards mismatches, dedup rejects near-copies above threshold, no-trivia prompt contract.

### Phase 6 — Web hardening & handoff to mobile
- Full pytest + Playwright suites green.
- README run steps: web (`next dev`), backend (`uvicorn`), ingestion, generation, `.env.example`.
- **Web declared stable here** → mobile/native work begins per [`MOBILE.md`](./MOBILE.md).

---

## 6. Deliverables checklist
- [ ] Working monorepo (`/frontend`, `/backend`).
- [ ] Seed script (courses + subtopics).
- [ ] Exemplar ingestion script.
- [ ] Few-shot generation + verification script.
- [ ] `.env.example` (Mongo URI, provider keys, model names, similarity threshold).
- [ ] README run steps (web, backend, ingestion, generation, Capacitor builds → see MOBILE.md).
- [ ] Passing Playwright + pytest suites.
