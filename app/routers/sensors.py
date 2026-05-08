from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.database import dict_from_row, get_connection, list_from_rows
from app.responses import ok
from app.routers.common import build_search, ensure_exists, get_or_404
from app.schemas import ReadingCreate, SensorCreate, SensorSearch, SensorUpdate
from app.services import evaluate_rules_for_reading

router = APIRouter()


def _datetime_to_text(value: datetime | None) -> str:
    if value is None:
        return datetime.now(timezone.utc).isoformat()
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.isoformat()


@router.get("/sensors")
def list_sensors(limit: int = 50, offset: int = 0) -> dict:
    return search_sensors(SensorSearch(limit=limit, offset=offset))


@router.post("/sensors")
def create_sensor(payload: SensorCreate) -> dict:
    with get_connection() as connection:
        ensure_exists(connection, "rooms", payload.room_id, "Room")
        cursor = connection.execute(
            """
            INSERT INTO sensors (room_id, name, sensor_type, unit, is_active)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                payload.room_id,
                payload.name,
                payload.sensor_type,
                payload.unit,
                int(payload.is_active),
            ),
        )
        connection.commit()
        sensor = dict_from_row(
            connection.execute("SELECT * FROM sensors WHERE id = ?", (cursor.lastrowid,)).fetchone()
        )
    return ok(sensor, {"created": True})


@router.get("/sensors/{sensor_id}")
def get_sensor(sensor_id: int) -> dict:
    with get_connection() as connection:
        sensor = get_or_404(connection, "sensors", sensor_id, "Sensor")
    return ok(sensor)


@router.patch("/sensors/{sensor_id}")
def update_sensor(sensor_id: int, payload: SensorUpdate) -> dict:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "is_active" in updates:
        updates["is_active"] = int(updates["is_active"])

    with get_connection() as connection:
        get_or_404(connection, "sensors", sensor_id, "Sensor")
        if "room_id" in updates:
            ensure_exists(connection, "rooms", updates["room_id"], "Room")

        fields = ", ".join(f"{field} = ?" for field in updates)
        connection.execute(f"UPDATE sensors SET {fields} WHERE id = ?", [*updates.values(), sensor_id])
        connection.commit()
        sensor = get_or_404(connection, "sensors", sensor_id, "Sensor")
    return ok(sensor, {"updated": True})


@router.delete("/sensors/{sensor_id}")
def delete_sensor(sensor_id: int) -> dict:
    with get_connection() as connection:
        sensor = get_or_404(connection, "sensors", sensor_id, "Sensor")
        connection.execute("DELETE FROM sensors WHERE id = ?", (sensor_id,))
        connection.commit()
    return ok(sensor, {"deleted": True})


@router.post("/sensors:search")
def search_sensors(payload: SensorSearch) -> dict:
    filters: list[str] = []
    params: list = []

    if payload.room_id is not None:
        filters.append("room_id = ?")
        params.append(payload.room_id)
    if payload.sensor_type:
        filters.append("sensor_type = ?")
        params.append(payload.sensor_type)
    if payload.is_active is not None:
        filters.append("is_active = ?")
        params.append(int(payload.is_active))

    sql, count_sql, query_params = build_search(
        "SELECT * FROM sensors", filters, params, payload.limit, payload.offset
    )
    with get_connection() as connection:
        rows = list_from_rows(connection.execute(sql, query_params).fetchall())
        total = connection.execute(count_sql, params).fetchone()["total"]
    return ok(rows, {"total": total, "limit": payload.limit, "offset": payload.offset})


@router.post("/sensors/{sensor_id}/readings")
def create_reading(sensor_id: int, payload: ReadingCreate) -> dict:
    measured_at = _datetime_to_text(payload.measured_at)

    with get_connection() as connection:
        sensor_row = connection.execute("SELECT * FROM sensors WHERE id = ?", (sensor_id,)).fetchone()
        if sensor_row is None:
            raise HTTPException(status_code=404, detail=f"Sensor with id={sensor_id} not found")
        if not sensor_row["is_active"]:
            raise HTTPException(status_code=409, detail="Sensor is inactive")

        cursor = connection.execute(
            """
            INSERT INTO sensor_readings (sensor_id, value, measured_at)
            VALUES (?, ?, ?)
            """,
            (sensor_id, payload.value, measured_at),
        )
        automation_meta = evaluate_rules_for_reading(connection, sensor_row, payload.value)
        connection.commit()

        reading = dict_from_row(
            connection.execute(
                "SELECT * FROM sensor_readings WHERE id = ?", (cursor.lastrowid,)
            ).fetchone()
        )

    return ok(reading, {"created": True, **automation_meta})


@router.get("/sensors/{sensor_id}/readings")
def list_sensor_readings(sensor_id: int, limit: int = 50, offset: int = 0) -> dict:
    with get_connection() as connection:
        ensure_exists(connection, "sensors", sensor_id, "Sensor")
        rows = list_from_rows(
            connection.execute(
                """
                SELECT * FROM sensor_readings
                WHERE sensor_id = ?
                ORDER BY measured_at DESC, id DESC
                LIMIT ? OFFSET ?
                """,
                (sensor_id, limit, offset),
            ).fetchall()
        )
        total = connection.execute(
            "SELECT COUNT(*) AS total FROM sensor_readings WHERE sensor_id = ?", (sensor_id,)
        ).fetchone()["total"]
    return ok(rows, {"total": total, "limit": limit, "offset": offset})
