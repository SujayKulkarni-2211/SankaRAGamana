# SankaRĀGamana — अथातो ब्रह्म जिज्ञासा

> A system that uses RAG techniques grounded in Śaṅkarācārya's own words to respond to the seeker's inquiry.

## Overview

SankaRĀGamana retrieves Adi Shankaracharya's own words from a corpus of authentic and attributed texts, and expresses them in response to a seeker's question — in Sanskrit, English, or Kannada. The words are his. The retrieval is the machine's sevā.

## Stack

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI |
| Hosting | Render (free tier) |
| Embeddings | `intfloat/multilingual-e5-small` |
| Vector DB | Supabase pgvector |
| Generator | Groq — `llama-3.3-70b-versatile` |
| Frontend | React + Vite |

## Structure

```
sankaRAgamana/
├── backend/         # FastAPI app + RAG pipeline
├── ingestion/       # One-time local ingestion scripts
├── frontend/        # React SPA (built and served by FastAPI)
└── corpus/          # tracker.json (committed to git)
```

## Setup

1. Copy `.env.example` to `.env` and fill in your keys.
2. Run ingestion locally: `cd ingestion && python run_all.py`
3. Start backend: `uvicorn backend.main:app --reload`
4. Frontend dev: `cd frontend && npm install && npm run dev`

## Deployment

Deployed on Render. See `render.yaml`. Kept alive by a cron-job.org ping to `/health` every 14 minutes.

---

*अथातो ब्रह्म जिज्ञासा — Now, therefore, the inquiry into Brahman.*
