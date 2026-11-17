import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.api.router import api_router
from app.core.config import get_settings
from app.core.errors import AppError

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

SECURITY_HEADERS = [
    (b"x-content-type-options", b"nosniff"),
    (b"x-frame-options", b"DENY"),
    (b"referrer-policy", b"strict-origin-when-cross-origin"),
]


class SecurityHeadersMiddleware:
    """Adds a few cheap browser protections to every response."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"].extend(SECURITY_HEADERS)
            await send(message)

        await self.app(scope, receive, send_with_headers if scope["type"] == "http" else send)


def _mount_frontend(app: FastAPI, static_dir: Path) -> None:
    """Production: serve the built React app from the same origin as the API.

    Same origin means the SameSite=Lax auth cookie just works, and CORS is not needed.
    """
    root = static_dir.resolve()
    if (root / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=root / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str) -> FileResponse:
        if path == "api" or path.startswith("api/"):
            raise HTTPException(status_code=404, detail="Not found.")
        candidate = (root / path).resolve()
        # is_relative_to blocks "../../etc/passwd" style path traversal.
        if path and candidate.is_file() and candidate.is_relative_to(root):
            return FileResponse(candidate)
        # Any other path is a client-side route (e.g. /dashboard): React Router handles it.
        return FileResponse(root / "index.html")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Personal Tracker API",
        version="1.0.0",
        description="Todos and personal finance, per user. Auth is a JWT in an httpOnly cookie.",
    )

    @app.exception_handler(AppError)
    def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        # Domain errors from services become HTTP responses here, in one place.
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.add_middleware(SecurityHeadersMiddleware)
    app.include_router(api_router)

    if settings.static_dir and Path(settings.static_dir).is_dir():
        _mount_frontend(app, Path(settings.static_dir))
    return app


app = create_app()
