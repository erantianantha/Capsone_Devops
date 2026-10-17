from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from app.config import APP_VERSION, CORS_ORIGINS
from app.routers import items
from app.schemas import CATEGORIES

app = FastAPI(title="PantryPal API", version=APP_VERSION)

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(items.router)

# Exposes request count, latency histogram and in-progress gauges at /metrics
Instrumentator(excluded_handlers=["/metrics", "/health"]).instrument(app).expose(
    app, include_in_schema=False
)


@app.get("/health", tags=["health"])
@app.get("/api/health", tags=["health"], include_in_schema=False)
def health():
    return {"status": "ok", "version": APP_VERSION}


@app.get("/api/categories", tags=["items"])
def categories():
    return CATEGORIES
