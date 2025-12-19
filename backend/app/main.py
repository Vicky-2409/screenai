from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.router import api_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_per_minute}/minute"],
    storage_uri=settings.redis_url,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(
        "Starting %s (env=%s, ai_provider=%s, embedding_dim=%s)",
        settings.project_name,
        settings.environment,
        settings.resolved_ai_provider,
        settings.active_embedding_dim,
    )
    yield
    logger.info("Shutting down")


app = FastAPI(
    title=settings.project_name,
    version="0.1.0",
    description="AI-powered resume screening ATS API",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok", "service": settings.project_name, "environment": settings.environment}


@app.get("/", tags=["health"])
def root():
    return {"message": f"{settings.project_name} API", "docs": "/docs"}


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


app.include_router(api_router)
