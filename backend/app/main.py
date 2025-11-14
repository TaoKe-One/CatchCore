"""FastAPI application factory."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import init_db
from app.api.v1_auth import router as auth_router
from app.api.v1_assets import router as assets_router
from app.api.v1_tasks import router as tasks_router
from app.api.v1_vulnerabilities import router as vulnerabilities_router
from app.api.v1_websocket import router as websocket_router
from app.api.v1_pocs import router as pocs_router
from app.api.v1_reports import router as reports_router
from app.api.v1_search import router as search_router
from app.api.v1_tools import router as tools_router
from app.api.v1_nodes import router as nodes_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager for startup and shutdown events."""
    # Startup
    print(f"Starting {settings.APP_NAME} v{settings.APP_VERSION}")
    await init_db()
    print("Database initialized")
    yield
    # Shutdown
    print(f"Shutting down {settings.APP_NAME}")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(auth_router, prefix=settings.API_V1_PREFIX)
    app.include_router(assets_router, prefix=settings.API_V1_PREFIX)
    app.include_router(tasks_router, prefix=settings.API_V1_PREFIX)
    app.include_router(vulnerabilities_router, prefix=settings.API_V1_PREFIX)
    app.include_router(websocket_router, prefix=settings.API_V1_PREFIX)
    app.include_router(pocs_router, prefix=settings.API_V1_PREFIX)
    app.include_router(reports_router, prefix=settings.API_V1_PREFIX)
    app.include_router(search_router, prefix=settings.API_V1_PREFIX)
    app.include_router(tools_router, prefix=settings.API_V1_PREFIX)
    app.include_router(nodes_router, prefix=settings.API_V1_PREFIX)

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        return {"status": "ok", "version": settings.APP_VERSION}

    return app


app = create_app()
