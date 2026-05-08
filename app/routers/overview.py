from __future__ import annotations

from fastapi import APIRouter

from app.database import get_connection
from app.responses import ok

router = APIRouter()


@router.get("/overview")
def get_overview() -> dict:
    with get_connection() as connection:
        rooms = connection.execute("SELECT COUNT(*) AS value FROM rooms").fetchone()["value"]
        devices = connection.execute("SELECT COUNT(*) AS value FROM devices").fetchone()["value"]
        sensors = connection.execute("SELECT COUNT(*) AS value FROM sensors").fetchone()["value"]
        open_alerts = connection.execute(
            "SELECT COUNT(*) AS value FROM alerts WHERE status != 'closed'"
        ).fetchone()["value"]
        queued_commands = connection.execute(
            "SELECT COUNT(*) AS value FROM control_commands WHERE status = 'queued'"
        ).fetchone()["value"]
        device_statuses = connection.execute(
            "SELECT status, COUNT(*) AS count FROM devices GROUP BY status"
        ).fetchall()
    return ok(
        {
            "rooms": rooms,
            "devices": devices,
            "sensors": sensors,
            "open_alerts": open_alerts,
            "queued_commands": queued_commands,
            "devices_by_status": {row["status"]: row["count"] for row in device_statuses},
        }
    )
