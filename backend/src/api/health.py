import sqlite3

from fastapi import APIRouter

from db.database import get_db

router = APIRouter()


@router.get("/health")
def health_check():
    """
    Health check endpoint for Jetson Orin Nano watchdog monitor.
    """
    db_status = "healthy"
    try:
        with get_db() as conn:
            conn.execute("SELECT 1")
    except (sqlite3.Error, OSError) as e:
        db_status = f"unhealthy: {type(e).__name__}"

    return {
        "status": "ok" if db_status == "healthy" else "degraded",
        "service": "TutorBox Backend",
        "database": db_status,
    }
