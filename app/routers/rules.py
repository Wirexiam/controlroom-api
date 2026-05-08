from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.database import dict_from_row, get_connection
from app.responses import ok
from app.routers.common import build_search, ensure_exists, get_or_404, rows_with_payload
from app.schemas import RuleCreate, RuleSearch, RuleUpdate
from app.services import decode_payload_fields, json_dump

router = APIRouter()


@router.get("/rules")
def list_rules(limit: int = 50, offset: int = 0) -> dict:
    return search_rules(RuleSearch(limit=limit, offset=offset))


@router.post("/rules")
def create_rule(payload: RuleCreate) -> dict:
    with get_connection() as connection:
        ensure_exists(connection, "rooms", payload.room_id, "Room")
        cursor = connection.execute(
            """
            INSERT INTO control_rules (
                room_id, name, metric_type, operator, threshold_value,
                target_device_type, command_type, command_payload, is_enabled
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                payload.room_id,
                payload.name,
                payload.metric_type,
                payload.operator,
                payload.threshold_value,
                payload.target_device_type,
                payload.command_type,
                json_dump(payload.command_payload),
                int(payload.is_enabled),
            ),
        )
        connection.commit()
        rule = dict_from_row(
            connection.execute("SELECT * FROM control_rules WHERE id = ?", (cursor.lastrowid,)).fetchone()
        )
    return ok(decode_payload_fields(rule), {"created": True})


@router.get("/rules/{rule_id}")
def get_rule(rule_id: int) -> dict:
    with get_connection() as connection:
        rule = get_or_404(connection, "control_rules", rule_id, "Control rule")
    return ok(decode_payload_fields(rule))


@router.patch("/rules/{rule_id}")
def update_rule(rule_id: int, payload: RuleUpdate) -> dict:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "is_enabled" in updates:
        updates["is_enabled"] = int(updates["is_enabled"])
    if "command_payload" in updates:
        updates["command_payload"] = json_dump(updates["command_payload"])

    with get_connection() as connection:
        get_or_404(connection, "control_rules", rule_id, "Control rule")
        fields = ", ".join(f"{field} = ?" for field in updates)
        connection.execute(f"UPDATE control_rules SET {fields} WHERE id = ?", [*updates.values(), rule_id])
        connection.commit()
        rule = get_or_404(connection, "control_rules", rule_id, "Control rule")
    return ok(decode_payload_fields(rule), {"updated": True})


@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int) -> dict:
    with get_connection() as connection:
        rule = get_or_404(connection, "control_rules", rule_id, "Control rule")
        connection.execute("DELETE FROM control_rules WHERE id = ?", (rule_id,))
        connection.commit()
    return ok(decode_payload_fields(rule), {"deleted": True})


@router.post("/rules:search")
def search_rules(payload: RuleSearch) -> dict:
    filters: list[str] = []
    params: list = []

    if payload.room_id is not None:
        filters.append("room_id = ?")
        params.append(payload.room_id)
    if payload.metric_type:
        filters.append("metric_type = ?")
        params.append(payload.metric_type)
    if payload.is_enabled is not None:
        filters.append("is_enabled = ?")
        params.append(int(payload.is_enabled))

    sql, count_sql, query_params = build_search(
        "SELECT * FROM control_rules", filters, params, payload.limit, payload.offset
    )
    with get_connection() as connection:
        rows = rows_with_payload(connection.execute(sql, query_params).fetchall())
        total = connection.execute(count_sql, params).fetchone()["total"]
    return ok(rows, {"total": total, "limit": payload.limit, "offset": payload.offset})
