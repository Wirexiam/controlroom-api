from __future__ import annotations

from app.database import get_connection, init_db, reset_db
from app.services import json_dump


def seed() -> None:
    reset_db()
    init_db()
    with get_connection() as connection:
        room_ids = []
        for room in [
            ("Лаборатория автоматики 301", 3, "laboratory", 22.0),
            ("Серверная кафедры", 2, "server_room", 19.0),
            ("Аудитория 204", 2, "lecture", 22.5),
        ]:
            cursor = connection.execute(
                """
                INSERT INTO rooms (name, floor, purpose, target_temperature)
                VALUES (?, ?, ?, ?)
                """,
                room,
            )
            room_ids.append(cursor.lastrowid)

        connection.executemany(
            """
            INSERT INTO devices (room_id, name, device_type, status, mode, power_kw)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (room_ids[0], "Кондиционер 301-А", "climate", "online", "auto", 1.8),
                (room_ids[0], "Вытяжная вентиляция 301", "ventilation", "online", "auto", 0.9),
                (room_ids[1], "Прецизионный кондиционер SRV", "climate", "online", "cooling", 2.4),
                (room_ids[2], "Световая группа 204", "lighting", "maintenance", "manual", 0.6),
            ],
        )

        sensor_ids = []
        for sensor in [
            (room_ids[0], "Температура 301", "temperature", "°C", 1),
            (room_ids[0], "CO2 301", "co2", "ppm", 1),
            (room_ids[1], "Температура серверной", "temperature", "°C", 1),
            (room_ids[2], "Влажность 204", "humidity", "%", 1),
        ]:
            cursor = connection.execute(
                """
                INSERT INTO sensors (room_id, name, sensor_type, unit, is_active)
                VALUES (?, ?, ?, ?, ?)
                """,
                sensor,
            )
            sensor_ids.append(cursor.lastrowid)

        connection.executemany(
            """
            INSERT INTO control_rules (
                room_id, name, metric_type, operator, threshold_value,
                target_device_type, command_type, command_payload, is_enabled
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    room_ids[0],
                    "Охлаждение лаборатории при перегреве",
                    "temperature",
                    ">",
                    26,
                    "climate",
                    "set_mode",
                    json_dump({"mode": "cooling", "target_temperature": 22}),
                    1,
                ),
                (
                    room_ids[0],
                    "Проветривание при высоком CO2",
                    "co2",
                    ">=",
                    900,
                    "ventilation",
                    "set_mode",
                    json_dump({"mode": "boost", "duration_minutes": 20}),
                    1,
                ),
                (
                    room_ids[1],
                    "Аварийное охлаждение серверной",
                    "temperature",
                    ">",
                    23,
                    "climate",
                    "set_mode",
                    json_dump({"mode": "cooling", "target_temperature": 18}),
                    1,
                ),
            ],
        )

        connection.executemany(
            "INSERT INTO sensor_readings (sensor_id, value) VALUES (?, ?)",
            [(sensor_ids[0], 23.4), (sensor_ids[1], 720), (sensor_ids[2], 20.1), (sensor_ids[3], 41)],
        )

        connection.commit()


if __name__ == "__main__":
    seed()
    print("Demo data has been created in controlroom.sqlite3")
