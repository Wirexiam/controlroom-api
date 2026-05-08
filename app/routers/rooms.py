from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.database import dict_from_row, get_connection, list_from_rows
from app.responses import ok
from app.routers.common import build_search, get_or_404
from app.schemas import RoomCreate, RoomSearch, RoomUpdate

router = APIRouter()


@router.get("/rooms")
def list_rooms(limit: int = 50, offset: int = 0) -> dict:
    payload = RoomSearch(limit=limit, offset=offset)
    return search_rooms(payload)


@router.post("/rooms")
def create_room(payload: RoomCreate) -> dict:
    with get_connection() as connection:
        try:
            cursor = connection.execute(
                """
                INSERT INTO rooms (name, floor, purpose, target_temperature)
                VALUES (?, ?, ?, ?)
                """,
                (payload.name, payload.floor, payload.purpose, payload.target_temperature),
            )
            connection.commit()
        except Exception as exc:
            raise HTTPException(status_code=409, detail="Room with this name already exists") from exc

        room = dict_from_row(
            connection.execute("SELECT * FROM rooms WHERE id = ?", (cursor.lastrowid,)).fetchone()
        )
    return ok(room, {"created": True})


@router.get("/rooms/{room_id}")
def get_room(room_id: int) -> dict:
    with get_connection() as connection:
        room = get_or_404(connection, "rooms", room_id, "Room")
    return ok(room)


@router.patch("/rooms/{room_id}")
def update_room(room_id: int, payload: RoomUpdate) -> dict:
    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No fields to update")

    fields = ", ".join(f"{field} = ?" for field in updates)
    params = [*updates.values(), room_id]

    with get_connection() as connection:
        get_or_404(connection, "rooms", room_id, "Room")
        try:
            connection.execute(f"UPDATE rooms SET {fields} WHERE id = ?", params)
            connection.commit()
        except Exception as exc:
            raise HTTPException(status_code=409, detail="Room with this name already exists") from exc
        room = get_or_404(connection, "rooms", room_id, "Room")
    return ok(room, {"updated": True})


@router.delete("/rooms/{room_id}")
def delete_room(room_id: int) -> dict:
    with get_connection() as connection:
        room = get_or_404(connection, "rooms", room_id, "Room")
        connection.execute("DELETE FROM rooms WHERE id = ?", (room_id,))
        connection.commit()
    return ok(room, {"deleted": True})


@router.post("/rooms:search")
def search_rooms(payload: RoomSearch) -> dict:
    filters: list[str] = []
    params: list = []

    if payload.name_contains:
        filters.append("LOWER(name) LIKE LOWER(?)")
        params.append(f"%{payload.name_contains}%")
    if payload.floor is not None:
        filters.append("floor = ?")
        params.append(payload.floor)
    if payload.purpose:
        filters.append("purpose = ?")
        params.append(payload.purpose)

    sql, count_sql, query_params = build_search(
        "SELECT * FROM rooms", filters, params, payload.limit, payload.offset
    )
    with get_connection() as connection:
        rows = list_from_rows(connection.execute(sql, query_params).fetchall())
        total = connection.execute(count_sql, params).fetchone()["total"]
    return ok(rows, {"total": total, "limit": payload.limit, "offset": payload.offset})
