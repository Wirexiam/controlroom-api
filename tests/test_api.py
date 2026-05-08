from __future__ import annotations

import os
from pathlib import Path

os.environ["CONTROLROOM_DB_PATH"] = "./test_controlroom.sqlite3"

from fastapi.testclient import TestClient  # noqa: E402

from app.database import reset_db  # noqa: E402
from app.main import app  # noqa: E402

client = TestClient(app)


def setup_function() -> None:
    Path("./test_controlroom.sqlite3").unlink(missing_ok=True)
    reset_db()


def test_healthcheck() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["data"]["status"] == "ok"


def test_create_room_and_device() -> None:
    room_response = client.post(
        "/api/v1/rooms",
        json={"name": "Аудитория 101", "floor": 1, "purpose": "lecture"},
    )
    assert room_response.status_code == 200
    room_id = room_response.json()["data"]["id"]

    device_response = client.post(
        "/api/v1/devices",
        json={
            "room_id": room_id,
            "name": "Кондиционер 101",
            "device_type": "climate",
            "power_kw": 1.2,
        },
    )
    assert device_response.status_code == 200
    assert device_response.json()["data"]["room_id"] == room_id


def test_sensor_reading_triggers_rule_command_and_alert() -> None:
    room_id = client.post(
        "/api/v1/rooms",
        json={"name": "Лаборатория 305", "floor": 3, "purpose": "laboratory"},
    ).json()["data"]["id"]

    client.post(
        "/api/v1/devices",
        json={"room_id": room_id, "name": "Климат 305", "device_type": "climate"},
    )
    sensor_id = client.post(
        "/api/v1/sensors",
        json={
            "room_id": room_id,
            "name": "Температура 305",
            "sensor_type": "temperature",
            "unit": "°C",
        },
    ).json()["data"]["id"]
    client.post(
        "/api/v1/rules",
        json={
            "room_id": room_id,
            "name": "Включить охлаждение при перегреве",
            "metric_type": "temperature",
            "operator": ">",
            "threshold_value": 25,
            "target_device_type": "climate",
            "command_type": "set_mode",
            "command_payload": {"mode": "cooling", "target_temperature": 22},
        },
    )

    reading_response = client.post(
        f"/api/v1/sensors/{sensor_id}/readings",
        json={"value": 28.4},
    )

    assert reading_response.status_code == 200
    meta = reading_response.json()["meta"]
    assert meta["triggered_rules"] == 1
    assert meta["generated_alerts"] == 1
    assert meta["generated_commands"] == 1

    alerts = client.get("/api/v1/alerts").json()["data"]
    commands = client.get("/api/v1/commands").json()["data"]
    assert len(alerts) == 1
    assert len(commands) == 1
    assert commands[0]["command_type"] == "set_mode"


def test_room_search() -> None:
    client.post("/api/v1/rooms", json={"name": "Серверная", "floor": 1, "purpose": "server"})
    client.post("/api/v1/rooms", json={"name": "Лаборатория", "floor": 2, "purpose": "lab"})

    response = client.post("/api/v1/rooms:search", json={"floor": 1})
    assert response.status_code == 200
    body = response.json()
    assert body["meta"]["total"] == 1
    assert body["data"][0]["name"] == "Серверная"
