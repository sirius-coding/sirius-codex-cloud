from fastapi import APIRouter, HTTPException

from ..config import get_settings
from ..db import check_db_connection

router = APIRouter(tags=["health"])
settings = get_settings()


@router.get("/health/live")
def liveness():
    return {"status": "alive", "service": settings.app_name}


@router.get("/health/ready")
def readiness():
    try:
        check_db_connection()
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"database unavailable: {exc}") from exc
    return {"status": "ready", "service": settings.app_name}


@router.get("/health")
def health():
    return readiness()
