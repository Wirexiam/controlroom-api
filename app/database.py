from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Iterable

DEFAULT_DB_PATH = "controlroom.sqlite3"


def get_db_path() -> str:
    return os.getenv("CONTROLROOM_DB_PATH", DEFAULT_DB_PATH)


def get_connection() -> sqlite3.Connection:
    db_path = get_db_path()
    if db_path != ":memory:":
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def dict_from_row(row: sqlite3.Row | None) -> dict[str, Any] | None:
    if row is None:
        return None
    return dict(row)


def list_from_rows(rows: Iterable[sqlite3.Row]) -> list[dict[str, Any]]:
    return [dict(row) for row in rows]


def init_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS rooms (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE,
                floor INTEGER NOT NULL,
                purpose TEXT NOT NULL DEFAULT 'study',
                target_temperature REAL NOT NULL DEFAULT 22.0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                device_type TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'online',
                mode TEXT NOT NULL DEFAULT 'auto',
                power_kw REAL NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                last_command_at TEXT,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sensors (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                sensor_type TEXT NOT NULL,
                unit TEXT NOT NULL,
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS sensor_readings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sensor_id INTEGER NOT NULL,
                value REAL NOT NULL,
                measured_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (sensor_id) REFERENCES sensors(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS control_rules (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                name TEXT NOT NULL,
                metric_type TEXT NOT NULL,
                operator TEXT NOT NULL,
                threshold_value REAL NOT NULL,
                target_device_type TEXT NOT NULL,
                command_type TEXT NOT NULL,
                command_payload TEXT NOT NULL DEFAULT '{}',
                is_enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS control_commands (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                rule_id INTEGER,
                command_type TEXT NOT NULL,
                payload TEXT NOT NULL DEFAULT '{}',
                requested_by TEXT NOT NULL DEFAULT 'system',
                status TEXT NOT NULL DEFAULT 'queued',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                executed_at TEXT,
                FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
                FOREIGN KEY (rule_id) REFERENCES control_rules(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                room_id INTEGER NOT NULL,
                sensor_id INTEGER,
                rule_id INTEGER,
                severity TEXT NOT NULL DEFAULT 'warning',
                message TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'open',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                closed_at TEXT,
                FOREIGN KEY (room_id) REFERENCES rooms(id) ON DELETE CASCADE,
                FOREIGN KEY (sensor_id) REFERENCES sensors(id) ON DELETE SET NULL,
                FOREIGN KEY (rule_id) REFERENCES control_rules(id) ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_devices_room ON devices(room_id);
            CREATE INDEX IF NOT EXISTS idx_sensors_room ON sensors(room_id);
            CREATE INDEX IF NOT EXISTS idx_readings_sensor ON sensor_readings(sensor_id);
            CREATE INDEX IF NOT EXISTS idx_rules_room ON control_rules(room_id);
            CREATE INDEX IF NOT EXISTS idx_alerts_status ON alerts(status);
            """
        )
        connection.commit()


def reset_db() -> None:
    with get_connection() as connection:
        connection.executescript(
            """
            DROP TABLE IF EXISTS alerts;
            DROP TABLE IF EXISTS control_commands;
            DROP TABLE IF EXISTS control_rules;
            DROP TABLE IF EXISTS sensor_readings;
            DROP TABLE IF EXISTS sensors;
            DROP TABLE IF EXISTS devices;
            DROP TABLE IF EXISTS rooms;
            """
        )
        connection.commit()
    init_db()
