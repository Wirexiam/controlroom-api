from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field

DeviceStatus = Literal["online", "offline", "maintenance"]
CommandStatus = Literal["queued", "sent", "executed", "failed", "cancelled"]
AlertStatus = Literal["open", "acknowledged", "closed"]
RuleOperator = Literal[">", ">=", "<", "<=", "==", "!="]


class Pagination(BaseModel):
    limit: int = Field(default=50, ge=1, le=200)
    offset: int = Field(default=0, ge=0)


class RoomCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    floor: int = Field(ge=-5, le=100)
    purpose: str = Field(default="study", max_length=80)
    target_temperature: float = Field(default=22.0, ge=10, le=35)


class RoomUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    floor: int | None = Field(default=None, ge=-5, le=100)
    purpose: str | None = Field(default=None, max_length=80)
    target_temperature: float | None = Field(default=None, ge=10, le=35)


class RoomSearch(Pagination):
    name_contains: str | None = None
    floor: int | None = None
    purpose: str | None = None


class DeviceCreate(BaseModel):
    room_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=120)
    device_type: str = Field(min_length=2, max_length=80, examples=["climate", "ventilation", "lighting"])
    status: DeviceStatus = "online"
    mode: str = Field(default="auto", max_length=80)
    power_kw: float = Field(default=0, ge=0)


class DeviceUpdate(BaseModel):
    room_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    device_type: str | None = Field(default=None, min_length=2, max_length=80)
    status: DeviceStatus | None = None
    mode: str | None = Field(default=None, max_length=80)
    power_kw: float | None = Field(default=None, ge=0)


class DeviceSearch(Pagination):
    room_id: int | None = Field(default=None, gt=0)
    device_type: str | None = None
    status: DeviceStatus | None = None


class SensorCreate(BaseModel):
    room_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=120)
    sensor_type: str = Field(min_length=2, max_length=80, examples=["temperature", "humidity", "co2"])
    unit: str = Field(min_length=1, max_length=20, examples=["°C", "%", "ppm"])
    is_active: bool = True


class SensorUpdate(BaseModel):
    room_id: int | None = Field(default=None, gt=0)
    name: str | None = Field(default=None, min_length=2, max_length=120)
    sensor_type: str | None = Field(default=None, min_length=2, max_length=80)
    unit: str | None = Field(default=None, min_length=1, max_length=20)
    is_active: bool | None = None


class SensorSearch(Pagination):
    room_id: int | None = Field(default=None, gt=0)
    sensor_type: str | None = None
    is_active: bool | None = None


class ReadingCreate(BaseModel):
    value: float
    measured_at: datetime | None = None


class RuleCreate(BaseModel):
    room_id: int = Field(gt=0)
    name: str = Field(min_length=2, max_length=120)
    metric_type: str = Field(min_length=2, max_length=80, examples=["temperature", "humidity", "co2"])
    operator: RuleOperator
    threshold_value: float
    target_device_type: str = Field(min_length=2, max_length=80)
    command_type: str = Field(min_length=2, max_length=80, examples=["set_mode", "turn_on", "turn_off"])
    command_payload: dict = Field(default_factory=dict)
    is_enabled: bool = True


class RuleUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=120)
    metric_type: str | None = Field(default=None, min_length=2, max_length=80)
    operator: RuleOperator | None = None
    threshold_value: float | None = None
    target_device_type: str | None = Field(default=None, min_length=2, max_length=80)
    command_type: str | None = Field(default=None, min_length=2, max_length=80)
    command_payload: dict | None = None
    is_enabled: bool | None = None


class RuleSearch(Pagination):
    room_id: int | None = Field(default=None, gt=0)
    metric_type: str | None = None
    is_enabled: bool | None = None


class ManualCommandCreate(BaseModel):
    command_type: str = Field(min_length=2, max_length=80)
    payload: dict = Field(default_factory=dict)
    requested_by: str = Field(default="operator", min_length=2, max_length=80)


class TicketCreate(BaseModel):
    device_id: int = Field(gt=0)
    title: str = Field(min_length=3, max_length=160)
    description: str = Field(default="", max_length=1000)
    priority: Literal["low", "normal", "high", "critical"] = "normal"


class AlertSearch(Pagination):
    room_id: int | None = Field(default=None, gt=0)
    status: AlertStatus | None = None
    severity: str | None = None
