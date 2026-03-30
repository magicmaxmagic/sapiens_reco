import json
import logging
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.router import api_router
from app.core.auth import try_extract_auth_context
from app.core.config import get_settings
from app.core.database import Base, engine
from app.core.security import InMemoryRateLimiter
from app.services.audit_log_service import append_audit_event

settings = get_settings()
request_logger = logging.getLogger("optimus.audit")
security_logger = logging.getLogger("optimus.security")


@asynccontextmanager
async def lifespan(_: FastAPI):
    insecure_defaults: list[str] = []
    if settings.admin_password == "change-me":
        insecure_defaults.append("ADMIN_PASSWORD")
    if settings.jwt_secret_key == "change-this-jwt-secret-in-prod":
        insecure_defaults.append("JWT_SECRET_KEY")

    if settings.auth_required and insecure_defaults:
        if settings.app_env.lower() == "production":
            joined = ", ".join(insecure_defaults)
            raise RuntimeError(
                f"Insecure default auth settings in production: {joined}"
            )

        security_logger.warning(
            "insecure_default_auth_values env=%s fields=%s",
            settings.app_env,
            ",".join(insecure_defaults),
        )

    if settings.auto_create_tables:
        Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, debug=settings.app_debug, lifespan=lifespan)

allowed_origins = [
    origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()
]
trusted_hosts = [host.strip() for host in settings.trusted_hosts.split(",") if host.strip()]
rate_limiter = InMemoryRateLimiter(
    max_requests=settings.rate_limit_max_requests,
    window_seconds=settings.rate_limit_window_seconds,
)

app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts or ["*"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def security_and_audit_middleware(request: Request, call_next):
    request_id = uuid4().hex
    request.state.request_id = request_id
    auth_context = try_extract_auth_context(request.headers.get("authorization"))

    client_ip = request.client.host if request.client else "unknown"
    start = perf_counter()

    if not rate_limiter.allow(f"{client_ip}:{request.method}"):
        security_event = {
            "request_id": request_id,
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
        }
        security_logger.warning(
            json.dumps(
                {
                    "event": "rate_limit_exceeded",
                    **security_event,
                },
                ensure_ascii=True,
                separators=(",", ":"),
            )
        )
        append_audit_event(
            "rate_limit_exceeded",
            {
                **security_event,
                "actor": auth_context.subject if auth_context else None,
                "actor_role": auth_context.role if auth_context else None,
            },
        )
        response = JSONResponse(
            status_code=429,
            content={
                "detail": "Too many requests",
                "request_id": request_id,
            },
        )
    else:
        response = await call_next(request)

    duration_ms = (perf_counter() - start) * 1000
    request_event = {
        "request_id": request_id,
        "method": request.method,
        "path": request.url.path,
        "query": request.url.query,
        "status_code": response.status_code,
        "duration_ms": round(duration_ms, 2),
        "client_ip": client_ip,
        "user_agent": request.headers.get("user-agent"),
        "actor": auth_context.subject if auth_context else None,
        "actor_role": auth_context.role if auth_context else None,
    }
    append_audit_event("http_request", request_event)
    request_logger.info(
        json.dumps(request_event, ensure_ascii=True, separators=(",", ":"))
    )

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Content-Security-Policy"] = "default-src 'none'; frame-ancestors 'none'"
    if not settings.app_debug:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"

    return response


app.include_router(api_router, prefix="/api")
