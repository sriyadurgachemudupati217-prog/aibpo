"""Domain exceptions and their FastAPI handlers.

Services raise these instead of HTTPException so business logic stays
framework-agnostic; routers never need try/except blocks.
"""
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.core.logging import logger


class AppError(Exception):
    """Base class for all domain errors."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    detail: str = "An unexpected error occurred."

    def __init__(self, detail: str | None = None):
        if detail:
            self.detail = detail
        super().__init__(self.detail)


class NotFoundError(AppError):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Resource not found."


class AlreadyExistsError(AppError):
    status_code = status.HTTP_409_CONFLICT
    detail = "Resource already exists."


class InvalidCredentialsError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Invalid email or password."


class NotAuthenticatedError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "Not authenticated."


class InvalidTokenError(AppError):
    status_code = status.HTTP_401_UNAUTHORIZED
    detail = "This token is invalid, expired, or has already been used."


class PermissionDeniedError(AppError):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "You do not have permission to perform this action."


class ValidationFailedError(AppError):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Validation failed."


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    @app.exception_handler(Exception)
    async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception(f"Unhandled error on {request.method} {request.url.path}: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"detail": "Internal server error."},
        )
