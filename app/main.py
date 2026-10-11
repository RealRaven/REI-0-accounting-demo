from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.api.v1.router import api_router
from app.config import get_settings
from app.core.vector.collections import ensure_collections
from app.logging import configure_logging, log
from app.web.routes import web_router

configure_logging()
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("startup", model=settings.llm_model, qdrant=settings.qdrant_url)
    try:
        await ensure_collections()
    except Exception as e:
        log.warning("collections_init_failed", error=str(e))
    yield
    log.info("shutdown")


app = FastAPI(
    title="REI-0-accounting-demo",
    version="0.1.0",
    description="Local RAG accounting assistant.",
    lifespan=lifespan,
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(web_router, prefix="/ui")

app.mount("/static", StaticFiles(directory="app/web/static"), name="static")


@app.get("/")
async def root():
    return RedirectResponse(url="/ui/chat")