from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.database import get_connection, list_from_rows
from app.responses import ok
from app.routers.common import build_search, get_or_404
from app.schemas import AlertSearch

router = APIRouter()


class AlertUpdate(BaseModel):
    status: str


@router.get("/alerts")
def list_alerts(limit: int = 50, offset: int = 0) -> dict:
    return search_alerts(AlertSearch(limit=limit, offset=offset))


@router.get("/alerts/{alert_id}")
def get_alert(alert_id: int) -> dict:
    with get_connection() as connection:
        alert = get_or_404(connection, "alerts", alert_id, "Alert")
    return ok(alert)


@router.patch("/alerts/{alert_id}")
def update_alert(alert_id: int, payload: AlertUpdate) -> dict:
    if payload.status not in {"open", "acknowledged", "closed"}:
        raise HTTPException(status_code=422, detail="Invalid alert status")

    closed_expr = ", closed_at = CURRENT_TIMESTAMP" if payload.status == "closed" else ""
    with get_connection() as connection:
        get_or_404(connection, "alerts", alert_id, "Alert")
        connection.execute(
            f"UPDATE alerts SET status = ?{closed_expr} WHERE id = ?",
            (payload.status, alert_id),
        )
        connection.commit()
        alert = get_or_404(connection, "alerts", alert_id, "Alert")
    return ok(alert, {"updated": True})


@router.post("/alerts:search")
def search_alerts(payload: AlertSearch) -> dict:
    filters: list[str] = []
    params: list = []

    if payload.room_id is not None:
        filters.append("room_id = ?")
        params.append(payload.room_id)
    if payload.status:
        filters.append("status = ?")
        params.append(payload.status)
    if payload.severity:
        filters.append("severity = ?")
        params.append(payload.severity)

    sql, count_sql, query_params = build_search(
        "SELECT * FROM alerts", filters, params, payload.limit, payload.offset
    )
    with get_connection() as connection:
        rows = list_from_rows(connection.execute(sql, query_params).fetchall())
        total = connection.execute(count_sql, params).fetchone()["total"]
    return ok(rows, {"total": total, "limit": payload.limit, "offset": payload.offset})
