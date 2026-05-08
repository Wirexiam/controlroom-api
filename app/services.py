from __future__ import annotations

import json
import operator
import sqlite3
from typing import Any

COMPARATORS = {
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le,
    "==": operator.eq,
    "!=": operator.ne,
}


def json_dump(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def json_load(value: str | None) -> dict[str, Any]:
    if not value:
        return {}
    try:
        data = json.loads(value)
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def decode_payload_fields(item: dict[str, Any]) -> dict[str, Any]:
    for field in ("payload", "command_payload"):
        if field in item:
            item[field] = json_load(item[field])
    return item


def rule_matches(value: float, operator_name: str, threshold: float) -> bool:
    comparator = COMPARATORS[operator_name]
    return bool(comparator(value, threshold))


def evaluate_rules_for_reading(
    connection: sqlite3.Connection,
    sensor: sqlite3.Row,
    reading_value: float,
) -> dict[str, int]:
    rules = connection.execute(
        """
        SELECT * FROM control_rules
        WHERE room_id = ? AND metric_type = ? AND is_enabled = 1
        """,
        (sensor["room_id"], sensor["sensor_type"]),
    ).fetchall()

    triggered_rules = 0
    generated_commands = 0
    generated_alerts = 0

    for rule in rules:
        if not rule_matches(reading_value, rule["operator"], rule["threshold_value"]):
            continue

        triggered_rules += 1
        message = (
            f"Rule '{rule['name']}' triggered: {sensor['sensor_type']} "
            f"{reading_value} {rule['operator']} {rule['threshold_value']}"
        )
        connection.execute(
            """
            INSERT INTO alerts (room_id, sensor_id, rule_id, severity, message)
            VALUES (?, ?, ?, ?, ?)
            """,
            (sensor["room_id"], sensor["id"], rule["id"], "warning", message),
        )
        generated_alerts += 1

        devices = connection.execute(
            """
            SELECT id FROM devices
            WHERE room_id = ? AND device_type = ? AND status != 'offline'
            """,
            (sensor["room_id"], rule["target_device_type"]),
        ).fetchall()

        for device in devices:
            connection.execute(
                """
                INSERT INTO control_commands
                    (device_id, rule_id, command_type, payload, requested_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    device["id"],
                    rule["id"],
                    rule["command_type"],
                    rule["command_payload"],
                    "system",
                ),
            )
            connection.execute(
                "UPDATE devices SET last_command_at = CURRENT_TIMESTAMP WHERE id = ?",
                (device["id"],),
            )
            generated_commands += 1

    return {
        "triggered_rules": triggered_rules,
        "generated_alerts": generated_alerts,
        "generated_commands": generated_commands,
    }
