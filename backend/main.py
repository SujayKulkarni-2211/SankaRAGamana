from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import os
from dotenv import load_dotenv

load_dotenv()

from backend.api.query import router as query_router
from backend.api.stream import router as stream_router
from backend.api.feedback import router as feedback_router
from backend.api.conversation import router as conversation_router
from backend.api.translate import router as translate_router
from backend.rag.embedder import Embedder

app = FastAPI(title="SankaRĀGamana", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_router)
app.include_router(stream_router)
app.include_router(feedback_router)
app.include_router(conversation_router)
app.include_router(translate_router)


@app.on_event("startup")
async def _warm_model():
    # Load e5-large into RAM at startup (~20-30s) so the FIRST query doesn't
    # hang while the 2.2GB model loads mid-stream — which read as a connection
    # error / HTTP2 protocol error on the client. The model is already cached in
    # the image (baked at build), so this is just the load-into-memory step.
    import asyncio
    def _load():
        try:
            Embedder.get()
            print("[startup] e5-large loaded into memory")
        except Exception as e:
            print(f"[startup] model warm-up failed: {e}")
    # run in a thread so it doesn't block the event loop / health checks
    asyncio.get_event_loop().run_in_executor(None, _load)


@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": Embedder.is_loaded()}


# Serve React build — must be last.
#
# SPA fallback: the React app uses client-side routing (/darshana/:id, /about,
# …). Those paths are NOT files on disk, so a direct visit / reload / shared
# link would otherwise hit the server and get a raw 404 JSON page (the
# "pretty-printed error" some users reported). A StaticFiles subclass that
# returns index.html for any missing path lets React Router take over instead.
from starlette.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


class SPAStaticFiles(StaticFiles):
    async def get_response(self, path, scope):
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            # Any unknown, non-API path → serve the SPA shell (200), so the
            # client router renders the route. Real 404s inside /api are
            # untouched (this mount only covers "/").
            if exc.status_code == 404:
                return FileResponse(os.path.join(frontend_dist, "index.html"))
            raise


if os.path.isdir(frontend_dist):
    app.mount("/", SPAStaticFiles(directory=frontend_dist, html=True), name="static")
