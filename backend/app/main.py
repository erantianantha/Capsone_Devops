from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.config import APP_VERSION, CORS_ORIGINS
from app.database import get_db
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
Instrumentator(excluded_handlers=["/metrics", "/health", "/ready"]).instrument(app).expose(
    app, include_in_schema=False
)


@app.get("/health", tags=["health"])
@app.get("/api/health", tags=["health"], include_in_schema=False)
def health():
    return {"status": "ok", "version": APP_VERSION}


@app.get("/ready", tags=["health"])
def ready(db: Session = Depends(get_db)):
    """Readiness: only report ready when the database answers, so Kubernetes
    stops routing traffic to a pod that has lost its DB connection."""
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(status_code=503, content={"status": "unavailable", "database": "down"})
    return {"status": "ready", "database": "up"}


@app.get("/api/categories", tags=["items"])
def categories():
    return CATEGORIES
