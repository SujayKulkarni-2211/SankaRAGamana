<div align="center">

# SankaRĀGamana

### श्रुतिस्मृतिपुराणानाम् आलयं करुणालयम् ।<br/>नमामि भगवत्पादं शङ्करं लोकशङ्करम् ॥

**A system that uses RAG grounded in Śaṅkarācārya's own words to meet the seeker's inquiry — not as a mouthpiece, but as a Guru.**

*अथातो ब्रह्म जिज्ञासा — Now, therefore, the inquiry into Brahman.*

</div>

---

## Table of Contents

- [What this is](#what-this-is)
- [The idea: a Guru, not a chatbot](#the-idea-a-guru-not-a-chatbot)
- [How it works (the pipeline)](#how-it-works-the-pipeline)
- [Features](#features)
- [The corpus](#the-corpus)
- [Tech stack](#tech-stack)
- [Project structure](#project-structure)
- [Running it yourself](#running-it-yourself)
  - [1. Prerequisites](#1-prerequisites)
  - [2. Clone & Python environment](#2-clone--python-environment)
  - [3. Environment variables](#3-environment-variables)
  - [4. Supabase: tables & functions](#4-supabase-tables--functions)
  - [5. Ingest the corpus](#5-ingest-the-corpus)
  - [6. Run the backend](#6-run-the-backend)
  - [7. Run the frontend](#7-run-the-frontend)
- [Deployment](#deployment)
- [API reference](#api-reference)
- [Design notes](#design-notes)
- [Credits & sources](#credits--sources)

---

## What this is

**SankaRĀGamana** (*Śaṅkara + RĀG + Āgamana* — "the coming of Śaṅkara through retrieval") retrieves Ādi Śaṅkarācārya's own words from a corpus of his authentic and attributed works, and weaves them into a response to a seeker's question — in **Sanskrit, English, Kannada, Hindi**, and more.

The words are his. The retrieval and the weaving are the machine's *sevā*. It never invents scripture: if the corpus does not hold the answer, it says so plainly and turns the seeker toward what the texts *do* teach.

---

## The idea: a Guru, not a chatbot

Śaṅkara never spoke the same way to everyone. To a grieving person — comfort first. To a young student — nurture. To a scholar — debate (*pūrvapakṣa–siddhānta*). To a devotee — song.

So before retrieving anything, the system **profiles the seeker**: who is asking, and why. That reading — level, intent, emotional tone, language — shapes *which* texts are drawn, *how many*, and *how* the final teaching is composed. For returning seekers, a **persistent memory** remembers them across visits.

This is not an optimization. It is the philosophical heart of the project.

---

## How it works (the pipeline)

A single question travels through a small **agreement of parts**, each doing one honest thing:

```
                         ┌─────────────────────┐
   seeker's question ──► │  1. Seeker Profiler  │  who is asking, and why?
                         └─────────┬───────────┘   (+ persistent memory for
                                   │                 returning seekers)
              ┌────────────────────┴────────────────────┐
              ▼                                          ▼
   ┌──────────────────────┐                  ┌──────────────────────┐
   │  2a. Agent A          │                  │  2b. Agent B          │
   │  the Sanskrit path    │                  │  the seeker's tongue  │
   │  translates the query │                  │  retrieves + explains │
   │  to classical Sanskrit│                  │  in plain language    │
   │  → retrieves in the   │                  │                       │
   │    corpus's own tongue│                  │                       │
   └───────────┬──────────┘                  └───────────┬──────────┘
               │       diversity-aware retrieval          │
               │   (book-centroid "laziness check" so     │
               │    several works speak, not one flood)   │
               └───────────────────┬──────────────────────┘
                                   ▼
                         ┌─────────────────────┐
                         │  3. Reflection       │  audits both paths,
                         │     + Synthesis      │  then composes ONE teaching:
                         └─────────┬───────────┘  authentic verses + clarity,
                                   │               grounded only in retrieved text
                                   ▼
                    final teaching, streamed token-by-token
```

**Why two paths?** The corpus is Sanskrit. A Sanskrit query embeds closer to it than an English one (≈0.09 cosine better on the same corpus). Agent A exploits that for authentic retrieval; Agent B keeps the seeker's own language for clarity. The Reflection step weaves the best of both and **grounds every claim in the retrieved material** — never in the model's training.

**The book-centroid "laziness check":** raw similarity lets a large text flood the results by sheer volume. Each book also has a *centroid* (its average meaning) stored in Supabase. When one source dominates, the query is checked against that centroid — *honest* domination (the book is truly about this) is allowed; *lazy* flooding is penalised so several works can speak.

---

## Features

- **Multi-agent RAG** — Sanskrit-path (Agent A) + language-path (Agent B) + Reflection/Synthesis.
- **Seeker profiling before retrieval** — level · intent · tone · language calibrate everything downstream.
- **Persistent seeker memory ("sleep consolidation")** — for logged-in seekers, a durable profile is distilled offline from past conversations and blended into each new question, so the Guru remembers them across visits.
- **Diversity-aware retrieval** with the **book-centroid laziness check** — answers cite several works, not one.
- **Live token streaming** over Server-Sent Events — the teaching appears as it is composed, with an inspectable "inner process" panel (profile, both agents, reflection).
- **Verse / prose distinction** — ślokas are detected and set apart in the manuscript Devanagari hand.
- **Anti-hallucination** — if the corpus lacks the answer, it says so; it never fabricates verses.
- **On-the-fly translation** of the interface and answers.
- **Conversation history & shareable darśana links** for signed-in seekers.
- **Rate limiting** — anonymous vs. logged-in tiers, backed by Supabase.
- **Resilient Groq access** — up to three API keys rotated round-robin with daily-exhaustion failover.
- **A bespoke "illuminated manuscript" UI** — Fraunces / Spectral / Tiro Devanagari typography, a self-inscribing praṇām-śloka, and a faint Raja Ravi Varma watermark of Śaṅkara.

---

## The corpus

**32 texts**, ~4,100 passages, sourced from [sanskritdocuments.org](https://sanskritdocuments.org) (ITRANS `.itx`) and [GRETIL](https://gretil.sub.uni-goettingen.de) (IAST), converted to Unicode Devanagari, chunked, and embedded.

It spans the **prakaraṇa-granthas** (Tattvabodha, Ātmabodha, Vivekacūḍāmaṇi, Upadeśasāhasrī, Aparokṣānubhūti, Dṛg-Dṛśya-Viveka, Vākyavṛtti, Pañcīkaraṇa, …), the **bhāṣyas** (Brahmasūtra Bhāṣya, Gītā Bhāṣya, Īśa / Kena / Praśna Upaniṣad Bhāṣyas), and the **stotras** (Bhajagovindam, Dakṣiṇāmūrti, Kālabhairava-aṣṭakam, Gaṇeśa-pañcaratnam, Guru-aṣṭakam, …).

> Authenticity is tracked per text. Nothing synthetic is ever added — no fabricated verses, no fake embeddings.

---

## Tech stack

| Layer | Technology |
|---|---|
| Backend | **FastAPI** (also serves the React build) |
| Embeddings | `intfloat/multilingual-e5-large` (1024-dim), loaded locally & at query time |
| Vector DB | **Supabase** pgvector |
| Generation | **Groq** — `llama-3.3-70b-versatile` (up to 3 keys, round-robin + failover) |
| Frontend | **React + Vite + Tailwind**, react-router, react-markdown |
| Auth & data | Supabase (Google sign-in, conversations, feedback, rate limits) |
| Hosting | Render (free tier), kept warm by a cron ping to `/health` |

> **e5 prefix rule (non-negotiable):** documents are embedded with a `passage: ` prefix and queries with a `query: ` prefix. The retriever and ingestion both honour this.

---

## Project structure

```
sankaragamana/
├── backend/
│   ├── main.py                 # FastAPI app: mounts routers, /health, serves frontend/dist
│   ├── api/
│   │   ├── stream.py           # POST /api/query/stream  (SSE — the main path)
│   │   ├── query.py            # POST /api/query         (non-streaming)
│   │   ├── conversation.py     # save / fetch / history
│   │   ├── feedback.py         # 👍/👎 → imprint distillation
│   │   ├── translate.py        # POST /api/translate
│   │   └── rate_limit.py       # anon vs. logged-in tiers
│   ├── rag/
│   │   ├── seeker_profiler.py  # per-query profile (who & why)
│   │   ├── seeker_memory.py    # persistent profile — "sleep consolidation"
│   │   ├── agent_a.py          # Sanskrit-path agent
│   │   ├── agent_b.py          # language-path agent
│   │   ├── retriever.py        # vector search + diversity + centroid laziness check
│   │   ├── reflection.py       # audit + streaming synthesis
│   │   ├── generator.py        # single-shot generation (non-streaming path)
│   │   ├── imprints.py         # global learning from feedback
│   │   ├── embedder.py         # e5-large, resident
│   │   ├── translator.py       # query/answer translation
│   │   └── groq_client.py      # 3-key round-robin + daily-exhaustion failover
│   └── requirements.txt
├── ingestion/
│   ├── run_all.py              # orchestrates the full ingestion
│   ├── scraper.py / gretil_fetcher.py          # fetch raw texts
│   ├── converter.py / gretil_iast_converter.py # ITRANS/IAST → Devanagari
│   ├── chunker.py / bhashya_chunker.py         # verse & prose chunking
│   ├── embedder_local.py / embed_new_texts.py  # embed + upsert to Supabase
│   ├── tracker.py
│   └── sql/
│       ├── book_centroids.sql      # centroid table + refresh + match RPC
│       └── seeker_profiles.sql     # persistent seeker memory table
├── frontend/
│   ├── src/
│   │   ├── App.jsx              # shell, header, routing
│   │   ├── pages/              # Chat, About, History, DarshanaView, Login, Admin
│   │   ├── components/         # ThinkingPanel, FinalResponse, Feedback, Footer, …
│   │   └── lib/supabase.js
│   └── public/shankara-bg.jpg  # Raja Ravi Varma watermark (public domain)
├── corpus/chunks/              # 32 *_chunks.json (committed)
├── render.yaml                 # Render deployment
└── README.md
```

---

## Running it yourself

### 1. Prerequisites

- **Python 3.10+**
- **Node 18+** and npm
- A free **[Supabase](https://supabase.com)** project (with the `pgvector` extension enabled)
- A free **[Groq](https://console.groq.com)** API key (one is enough to start; up to three are used if provided)
- `psql` (optional — for applying the SQL files from the CLI)

### 2. Clone & Python environment

```bash
git clone https://github.com/SujayKulkarni-2211/SankaRAGamana.git
cd SankaRAGamana

python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
```

> The first run downloads `intfloat/multilingual-e5-large` (~2.2 GB) into `model_cache/`.

### 3. Environment variables

Copy the template and fill it in:

```bash
cp .env.example .env
```

```dotenv
# Supabase
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_KEY=<service-role key>          # backend uses the service key

# Groq — 1 required; 2 & 3 optional (rotated round-robin across agents)
GROQ_API_KEY=
GROQ_API_KEY_2=
GROQ_API_KEY_3=

# Admin auth (reserved)
ADMIN_USERNAME=
ADMIN_PASSWORD=
JWT_SECRET=

# Model device: 'cpu' or 'cuda'
DEVICE=cpu
```

The **frontend** needs its own `frontend/.env.local` (the public anon key, never the service key):

```dotenv
VITE_SUPABASE_URL=https://<your-project>.supabase.co
VITE_SUPABASE_ANON_KEY=<anon/publishable key>
```

### 4. Supabase: tables & functions

In your Supabase project, enable `pgvector`, then create:

- **`corpus_chunks`** — the embedded passages: `chunk_id, text_name, text_title_devanagari, category, authenticity, source, language, content, verse_number, char_count, embedding vector(1024)` + an ivfflat cosine index.
- **`conversations`**, **`feedback`**, **`imprints`**, **`rate_limits`** — used by the app (history, learning, limits).
- The two SQL files in `ingestion/sql/`:

```bash
# via the Supabase SQL editor (paste each file), or via psql:
psql "$DATABASE_URL" -f ingestion/sql/book_centroids.sql     # centroids + match RPC
psql "$DATABASE_URL" -f ingestion/sql/seeker_profiles.sql    # persistent seeker memory
```

> `book_centroids.sql` also defines `refresh_book_centroids()` — **re-run it after any corpus change** so the laziness check stays in sync. No app-side recompute needed.

### 5. Ingest the corpus

Pre-chunked JSON lives in `corpus/chunks/`. To (re)embed and upsert into Supabase:

```bash
cd ingestion
python run_all.py            # fetch → convert → chunk → embed → upsert
# (or, to embed only newly-added texts:)
python embed_new_texts.py
```

Then refresh the centroids (step 4).

### 6. Run the backend

```bash
# from the repo root, with .venv active
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Check it: `curl http://localhost:8000/health` → `{"status":"ok","model_loaded":true}`

### 7. Run the frontend

```bash
cd frontend
npm install
npm run dev            # http://localhost:5173 (proxies /api to the backend)
```

For a production-like run, `npm run build` — FastAPI will serve `frontend/dist` at `/` automatically.

---

## Deployment

Deployed on **Render** (see [`render.yaml`](render.yaml)):

- **Build:** `pip install -r backend/requirements.txt` && `cd frontend && npm install && npm run build`
- **Start:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- Set the env vars from step 3 in the Render dashboard (`sync: false` keys).
- Keep the free instance warm with a cron ping (e.g. [cron-job.org](https://cron-job.org)) to `/health` every ~14 minutes.

One platform, one repo, one URL — FastAPI serves both the API and the built SPA.

---

## API reference

| Method | Path | Purpose |
|---|---|---|
| `POST` | `/api/query/stream` | **Main path.** SSE stream: `profile → agent_a_* → agent_b_* → reflection_reasoning → final_response → done`. |
| `POST` | `/api/query` | Non-streaming single response. |
| `POST` | `/api/translate` | Translate text to a target language. |
| `POST` | `/api/feedback` | 👍/👎 on a response → feeds imprint distillation. |
| `POST` | `/api/conversation/save` | Persist an exchange. |
| `GET`  | `/api/conversation/{session_id}` | Fetch a saved darśana. |
| `GET`  | `/api/conversations/history?user_id=…` | A seeker's history. |
| `GET`  | `/health` | Liveness + whether the embedder is loaded. |

**Stream request body:**

```json
{ "question": "What is the Self?", "user_id": "<uuid or null>", "history": [] }
```

---

## Design notes

- **The system prompt that makes Śaṅkara answer as himself is sacred** — grounded only in retrieved passages, Sanskrit first, same language as the question, honest about gaps. Don't change it without intent.
- **Persistent memory stays lean:** the durable profile is capped at the source, and only **one short line** is injected into synthesis (and only for returning seekers) — never per-query prompt bloat. A seeker with more than two exchanges is met as **advanced**.
- **Scalability:** centroids and seeker profiles live in Supabase (not local JSON), so adding texts or users needs no code change — embed, then `refresh_book_centroids()`.

---

## Credits & sources

- **Texts:** [sanskritdocuments.org](https://sanskritdocuments.org) · [GRETIL](https://gretil.sub.uni-goettingen.de)
- **Image:** Raja Ravi Varma, *Sankaracharya* (public domain, via Wikimedia Commons)
- **Built** by the grace of Ādi Śaṅkara and Devī Sarasvatī, by [Sujay V Kulkarni](https://github.com/SujayKulkarni-2211).

<div align="center">

---

*ब्रह्म सत्यं जगन्मिथ्या जीवो ब्रह्मैव नापरः*<br/>
<sub>Brahman alone is real; the world is appearance; the self is none other than Brahman.</sub>

</div>
