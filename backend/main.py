"""Main FastAPI Application Entrypoint for SupeRR Intelligence Lab."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from backend.api.routes import (
    competitions,
    datasets,
    health,
    matches,
    methodology,
    overview,
    players,
    rankings,
    reports,
)
from backend.api.services.data_loader import AnalyticsDataStore

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("superr_api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up SupeRR Intelligence Lab API server...")
    # Pre-warm singleton datastore
    AnalyticsDataStore.get_instance()
    logger.info("SupeRR Intelligence Lab API ready to serve requests.")
    yield


app = FastAPI(
    title="SupeRR Intelligence Lab API",
    description="Production-grade sports analytics and pressure intelligence platform for SupeRR Selector Season 2.",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Enable CORS for Vite dev server and production clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception on %s %s: %s", request.method, request.url.path, exc, exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error occurred.", "path": request.url.path, "error": str(exc)},
    )

# Mount API routers
app.include_router(health.router, prefix="/api")
app.include_router(overview.router, prefix="/api")
app.include_router(datasets.router, prefix="/api")
app.include_router(competitions.router, prefix="/api")
app.include_router(matches.router, prefix="/api")
app.include_router(players.router, prefix="/api")
app.include_router(rankings.router, prefix="/api")
app.include_router(methodology.router, prefix="/api")
app.include_router(reports.router, prefix="/api")

# Static figures mount for charts
FIGURES_DIR = Path(__file__).resolve().parent.parent / "submission" / "figures"
if FIGURES_DIR.exists():
    app.mount("/api/figures", StaticFiles(directory=str(FIGURES_DIR)), name="figures")

# Mount production frontend build if available
FRONTEND_DIST = Path(__file__).resolve().parent.parent / "frontend" / "dist"
if FRONTEND_DIST.exists():
    if (FRONTEND_DIST / "assets").exists():
        app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="assets")

    from fastapi.responses import FileResponse

    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Do not intercept api or docs paths
        if full_path.startswith("api") or full_path.startswith("docs") or full_path.startswith("openapi.json"):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        target_path = (FRONTEND_DIST / full_path).resolve()
        # Strictly prevent path traversal outside FRONTEND_DIST
        if not str(target_path).startswith(str(FRONTEND_DIST.resolve())):
            return JSONResponse(status_code=403, content={"detail": "Access denied: path traversal forbidden"})
        if target_path.exists() and target_path.is_file():
            return FileResponse(target_path)
        return FileResponse(FRONTEND_DIST / "index.html")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)

