from __future__ import annotations

from typing import Any


def ok(data: Any = None, meta: dict[str, Any] | None = None) -> dict[str, Any]:
    return {"data": data, "errors": [], "meta": meta or {}}


def error(message: str, code: str = "bad_request", details: dict[str, Any] | None = None) -> dict[str, Any]:
    return {
        "data": None,
        "errors": [{"code": code, "message": message, "details": details or {}}],
        "meta": {},
    }
