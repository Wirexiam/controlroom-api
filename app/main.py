from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.responses import ok
from app.routers import alerts, devices, overview, rooms, rules, sensors


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="ControlRoom API",
    description="Headless REST API для управления помещениями, датчиками и исполнительными устройствами.",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(rooms.router, prefix="/api/v1", tags=["rooms"])
app.include_router(devices.router, prefix="/api/v1", tags=["devices"])
app.include_router(sensors.router, prefix="/api/v1", tags=["sensors"])
app.include_router(rules.router, prefix="/api/v1", tags=["control-rules"])
app.include_router(alerts.router, prefix="/api/v1", tags=["alerts"])
app.include_router(overview.router, prefix="/api/v1", tags=["overview"])


@app.get("/health")
def healthcheck() -> dict:
    return ok({"status": "ok"})
