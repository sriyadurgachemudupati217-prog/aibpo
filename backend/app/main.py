"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import logger
from app.routers import auth, tasks, uploads, users

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title="AI Business Process Optimizer",
        description="Enterprise SaaS platform for ML/NLP-driven operations optimization.",
        version="0.1.0",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.environment == "development" else [],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    register_exception_handlers(app)

    app.include_router(auth.router, prefix="/api/v1")
    app.include_router(users.router, prefix="/api/v1")
    app.include_router(uploads.router, prefix="/api/v1")
    app.include_router(tasks.router, prefix="/api/v1")

    @app.get("/api/v1/health", tags=["health"])
    def health() -> dict:
        return {"status": "ok", "environment": settings.environment}

    @app.on_event("startup")
    def on_startup() -> None:
        logger.info(f"Starting AI Business Process Optimizer [{settings.environment}]")

    return app


app = create_app()
