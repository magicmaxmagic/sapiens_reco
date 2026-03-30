import json

from fastapi import APIRouter, Depends, Query
from fastapi.responses import PlainTextResponse

from app.core.auth import AuthContext, require_admin_user
from app.services.audit_log_service import read_audit_events

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/logs/export", response_model=None)
def export_audit_logs(
    export_format: str = Query(default="json", alias="format", pattern="^(json|jsonl)$"),
    limit: int = Query(default=500, ge=1, le=5000),
    _: AuthContext = Depends(require_admin_user),
) -> dict[str, object] | PlainTextResponse:
    events = read_audit_events(limit=limit)

    if export_format == "jsonl":
        payload = "\n".join(json.dumps(event, ensure_ascii=True) for event in events)
        if payload:
            payload = f"{payload}\n"
        return PlainTextResponse(payload, media_type="application/x-ndjson")

    return {
        "count": len(events),
        "items": events,
    }
