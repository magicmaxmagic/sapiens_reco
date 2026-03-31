from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.database import get_db

router = APIRouter(prefix="/notes", tags=["notes"])


@router.get("")
def list_notes(limit: int = 100, db: Session = Depends(get_db)) -> list[dict]:
    """Return rows from a `notes` table if present in the connected database.

    This endpoint is intentionally minimal: it executes a raw SELECT against
    a `notes` table and returns the rows as JSON. If the table does not exist
    or another DB error occurs a 404 is returned to indicate the resource is
    not available.
    """
    try:
        stmt = text("SELECT * FROM notes LIMIT :limit")
        result = db.execute(stmt, {"limit": limit})
    except Exception:
        raise HTTPException(status_code=404, detail="Notes table not found or DB error")

    rows = result.mappings().all()
    return [dict(r) for r in rows]
