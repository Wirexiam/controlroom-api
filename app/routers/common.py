from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import HTTPException

from app.database import dict_from_row, list_from_rows
from app.services import decode_payload_fields


def get_or_404(connection: sqlite3.Connection, table: str, item_id: int, name: str) -> dict[str, Any]:
    row = connection.execute(f"SELECT * FROM {table} WHERE id = ?", (item_id,)).fetchone()
    item = dict_from_row(row)
    if item is None:
        raise HTTPException(status_code=404, detail=f"{name} with id={item_id} not found")
    return item


def ensure_exists(connection: sqlite3.Connection, table: str, item_id: int, name: str) -> None:
    row = connection.execute(f"SELECT id FROM {table} WHERE id = ?", (item_id,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"{name} with id={item_id} not found")


def build_search(base_sql: str, filters: list[str], params: list[Any], limit: int, offset: int):
    where = ""
    if filters:
        where = " WHERE " + " AND ".join(filters)
    sql = f"{base_sql}{where} ORDER BY id DESC LIMIT ? OFFSET ?"
    count_sql = f"SELECT COUNT(*) AS total FROM ({base_sql}{where}) AS filtered"
    return sql, count_sql, [*params, limit, offset]


def rows_with_payload(rows) -> list[dict[str, Any]]:
    return [decode_payload_fields(item) for item in list_from_rows(rows)]
