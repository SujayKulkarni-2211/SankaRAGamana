# ─────────────────────────────────────────────────────────────────────────────
# SankaRĀGamana — single-image deploy (Hugging Face Spaces, Docker SDK).
#
# One container: build the React frontend, then run FastAPI which serves both
# the API and the built SPA. The e5-large embedding model (~2.2 GB RAM) is
# downloaded at build time and baked in, so the first request is fast.
#
# HF Spaces requires the app to listen on port 7860.
# ─────────────────────────────────────────────────────────────────────────────

# ── Stage 1: build the frontend ──────────────────────────────────────────────
FROM node:18-slim AS frontend

WORKDIR /frontend
COPY frontend/package*.json ./
# npm ci = clean, reproducible install straight from package-lock.json
RUN npm ci
COPY frontend/ ./

# Fetch the crisp Śaṅkara watermark at build time (the binary isn't committed to
# git — HF rejects committed binaries). Raja Ravi Varma, public domain. Downscale
# to a web-friendly 1100px so Vite bundles a sharp static /shankara-bg.jpg. If the
# fetch ever fails, the app falls back to the inlined base64, so the build still
# succeeds and the watermark still shows. (HF allows HTTPS during build.)
# Try to fetch the crisp original at build time; HF's build network may block
# external hosts, so this is NON-FATAL — on failure the app serves the inlined
# 1300px/q92 base64 fallback (assets-shankara.js), which is the same quality.
RUN apt-get update && apt-get install -y --no-install-recommends curl imagemagick \
 && ( curl -fL --retry 3 --connect-timeout 15 -A "Mozilla/5.0 (SankaRAGamana build)" \
        "https://upload.wikimedia.org/wikipedia/commons/e/e3/Raja_Ravi_Varma_-_Sankaracharya.jpg" \
        -o /tmp/sk.jpg \
      && convert /tmp/sk.jpg -resize 1300x -quality 92 -unsharp 0x0.5 public/shankara-bg.jpg \
      && echo "shankara-bg.jpg generated" \
    || echo "build-time image fetch failed — using base64 fallback (same quality)" ) \
 && rm -rf /var/lib/apt/lists/* /tmp/sk.jpg || true

# Supabase keys are build-time for Vite (import.meta.env.VITE_*). HF passes
# these as build args (set them as Space "Variables", not Secrets — they are
# the PUBLIC anon key + URL, safe to embed in the client bundle).
ARG VITE_SUPABASE_URL
ARG VITE_SUPABASE_ANON_KEY
ENV VITE_SUPABASE_URL=$VITE_SUPABASE_URL
ENV VITE_SUPABASE_ANON_KEY=$VITE_SUPABASE_ANON_KEY

RUN npm run build          # -> /frontend/dist (includes public/shankara-bg.jpg)


# ── Stage 2: the backend + model ─────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

# System deps kept minimal; sentence-transformers/torch wheels are self-contained.
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r backend/requirements.txt

# App code + corpus + the built frontend from stage 1.
COPY backend/ ./backend/
COPY corpus/ ./corpus/
COPY --from=frontend /frontend/dist ./frontend/dist

# Cache the e5-large model into the image at build time so cold starts don't
# pay the ~2.2 GB download on the first query.
ENV MODEL_CACHE=/app/model_cache
ENV DEVICE=cpu
RUN python -c "from sentence_transformers import SentenceTransformer; \
    SentenceTransformer('intfloat/multilingual-e5-large', cache_folder='/app/model_cache')"

# HF Spaces listens on 7860.
EXPOSE 7860
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "7860"]
