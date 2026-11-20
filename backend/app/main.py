import base64
import hashlib
import logging
import re
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

# Production only. Tells browsers "this site is HTTPS-only for the next year", so even a
# typed http:// link never goes out unencrypted (where the cookie could be intercepted).
HSTS_HEADER = (b"strict-transport-security", b"max-age=31536000; includeSubDomains")

_INLINE_SCRIPT = re.compile(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", re.DOTALL)


def content_security_policy(index_html: str) -> str:
    """CSP for the built React app: only our own files may run, nothing injected.

    If an attacker ever slipped a <script> into a page, the browser would refuse to run it.
    The one inline script we do have (the theme switch in index.html) is allowed by its
    SHA-256 fingerprint, computed from the built file so it stays right if the script changes.
    """
    hashes = [
        "'sha256-" + base64.b64encode(hashlib.sha256(body.encode()).digest()).decode() + "'"
        for body in _INLINE_SCRIPT.findall(index_html)
    ]
    return "; ".join(
        [
            "default-src 'self'",
            " ".join(["script-src 'self'", *hashes]),
            "style-src 'self' 'unsafe-inline'",  # charts set inline styles
            "img-src 'self' data:",
            "connect-src 'self'",
            "object-src 'none'",
            "base-uri 'self'",
            "form-action 'self'",
            "frame-ancestors 'none'",
        ]
    )


class SecurityHeadersMiddleware:
    """Adds cheap browser protections to every response."""

    def __init__(self, app: ASGIApp, headers: list[tuple[bytes, bytes]]) -> None:
        self.app = app
        self.headers = headers

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        async def send_with_headers(message: Message) -> None:
            if message["type"] == "http.response.start":
                message.setdefault("headers", [])
                message["headers"].extend(self.headers)
            await send(message)

        await self.app(scope, receive, send_with_headers if scope["type"] == "http" else send)


MAX_BODY_BYTES = 64 * 1024  # the largest real form (a finance entry) is about 3 KB


class BodySizeLimitMiddleware:
    """Refuse oversized request bodies before anything reads them into memory.

    Pydantic limits each field's length, but only after the whole body has been read and
    parsed. Without this, one 500 MB request could exhaust the server's memory.
    """

    def __init__(self, app: ASGIApp, max_bytes: int = MAX_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            if b"chunked" in headers.get(b"transfer-encoding", b"").lower():
                # A chunked body has no declared size, so we can't check it up front.
                # Browsers send Content-Length for fetch() bodies, so nothing real breaks.
                await self._reject(scope, send, 411, "Content-Length is required.")
                return
            length = headers.get(b"content-length", b"0")
            if not length.isdigit() or int(length) > self.max_bytes:
                await self._reject(scope, send, 413, "Request body too large.")
                return
        await self.app(scope, receive, send)

    @staticmethod
    async def _reject(scope: Scope, send: Send, status: int, detail: str) -> None:
        response = JSONResponse(status_code=status, content={"detail": detail})
        await response(scope, _no_receive, send)


async def _no_receive() -> Message:
    return {"type": "http.disconnect"}  # we never read the body we are refusing


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
    static_dir = Path(settings.static_dir) if settings.static_dir else None
    serve_frontend = static_dir is not None and static_dir.is_dir()

    # The interactive API docs are handy locally but just a map for attackers in production.
    show_docs = not settings.is_production
    app = FastAPI(
        title="Personal Tracker API",
        version="1.0.0",
        description="Todos and personal finance, per user. Auth is a JWT in an httpOnly cookie.",
        docs_url="/docs" if show_docs else None,
        redoc_url="/redoc" if show_docs else None,
        openapi_url="/openapi.json" if show_docs else None,
    )

    @app.exception_handler(AppError)
    def handle_app_error(_: Request, exc: AppError) -> JSONResponse:
        # Domain errors from services become HTTP responses here, in one place.
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})

    headers = list(SECURITY_HEADERS)
    if settings.is_production:
        headers.append(HSTS_HEADER)
    if serve_frontend and static_dir is not None:
        csp = content_security_policy((static_dir / "index.html").read_text(encoding="utf-8"))
        headers.append((b"content-security-policy", csp.encode()))

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type"],
    )
    app.add_middleware(BodySizeLimitMiddleware)
    # Added last = outermost, so even a 413 from the size limit gets these headers.
    app.add_middleware(SecurityHeadersMiddleware, headers=headers)
    app.include_router(api_router)

    if serve_frontend and static_dir is not None:
        _mount_frontend(app, static_dir)
    return app


app = create_app()
