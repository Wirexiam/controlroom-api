from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.database import dict_from_row, get_connection, list_from_rows
from app.responses import ok
from app.routers.common import build_search, ensure_exists, get_or_404, rows_with_payload
from app.schemas import DeviceCreate, DeviceSearch, DeviceUpdate, ManualCommandCreate
from app.services import json_dump

router = APIRouter()


@router.get("/devices")
def list_devices(limit: int = 50, offset: int = 0) -> dict:
    return search_devices(DeviceSearch(limit=limit, offset=offset))


@router.post("/devices")
def create_device(payload: DeviceCreate) -> dict:
    with get_connection() as connection:
        ensure_exists(connection, "rooms", payload.room_id, "Room")
        cursor = connection.execute(
            """
            INSERT INTO devices (room_id, name, device_type, status, mode, power_kw)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                payload.room_id,
                payload.name,
                payload.device_type,
                payload.status,
                payload.mode,
                payload.power_kw,
            ),
        )
        connection.commit()
        device = dict_from_row(
            connection.execute("SELECT * FROM devices WHERE id = ?", (cursor.lastrowid,)).fetchone()
        )
    return ok(device, {"created": True})


@router.get("/devices/{device_id}")
def get_device(device_id: int) -> dict:
    with get_connection() as connection:
        device = get_or_404(connection, "devices", device_id, "Device")
    return ok(device)


@router.patch("/devices/{device_id}")
def update_device(device_id: int, payload: DeviceUpdate) -> dict:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    with get_connection() as connection:
        get_or_404(connection, "devices", device_id, "Device")
        if "room_id" in updates:
            ensure_exists(connection, "rooms", updates["room_id"], "Room")

        fields = ", ".join(f"{field} = ?" for field in updates)
        connection.execute(f"UPDATE devices SET {fields} WHERE id = ?", [*updates.values(), device_id])
        connection.commit()
        device = get_or_404(connection, "devices", device_id, "Device")
    return ok(device, {"updated": True})


@router.delete("/devices/{device_id}")
def delete_device(device_id: int) -> dict:
    with get_connection() as connection:
        device = get_or_404(connection, "devices", device_id, "Device")
        connection.execute("DELETE FROM devices WHERE id = ?", (device_id,))
        connection.commit()
    return ok(device, {"deleted": True})


@router.post("/devices:search")
def search_devices(payload: DeviceSearch) -> dict:
    filters: list[str] = []
    params: list = []

    if payload.room_id is not None:
        filters.append("room_id = ?")
        params.append(payload.room_id)
    if payload.device_type:
        filters.append("device_type = ?")
        params.append(payload.device_type)
    if payload.status:
        filters.append("status = ?")
        params.append(payload.status)

    sql, count_sql, query_params = build_search(
        "SELECT * FROM devices", filters, params, payload.limit, payload.offset
    )
    with get_connection() as connection:
        rows = list_from_rows(connection.execute(sql, query_params).fetchall())
        total = connection.execute(count_sql, params).fetchone()["total"]
    return ok(rows, {"total": total, "limit": payload.limit, "offset": payload.offset})


@router.post("/devices/{device_id}/commands")
def create_manual_command(device_id: int, payload: ManualCommandCreate) -> dict:
    with get_connection() as connection:
        get_or_404(connection, "devices", device_id, "Device")
        cursor = connection.execute(
            """
            INSERT INTO control_commands (device_id, command_type, payload, requested_by)
            VALUES (?, ?, ?, ?)
            """,
            (device_id, payload.command_type, json_dump(payload.payload), payload.requested_by),
        )
        connection.execute("UPDATE devices SET last_command_at = CURRENT_TIMESTAMP WHERE id = ?", (device_id,))
        connection.commit()
        command = dict_from_row(
            connection.execute(
                "SELECT * FROM control_commands WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        )
    return ok(command, {"created": True})


@router.get("/commands")
def list_commands(limit: int = 50, offset: int = 0) -> dict:
    with get_connection() as connection:
        rows = rows_with_payload(
            connection.execute(
                "SELECT * FROM control_commands ORDER BY id DESC LIMIT ? OFFSET ?",
                (limit, offset),
            ).fetchall()
        )
        total = connection.execute("SELECT COUNT(*) AS total FROM control_commands").fetchone()["total"]
    return ok(rows, {"total": total, "limit": limit, "offset": offset})
