from datetime import datetime

from pydantic import BaseModel, Field


class VehicleOut(BaseModel):
    id: int
    name: str
    vehicle_type: str
    color: str
    status: str
    lat: float | None
    lon: float | None
    heading_degrees: float
    speed_kmh: float
    last_seen: datetime


class TrailPoint(BaseModel):
    lat: float
    lon: float
    speed_kmh: float | None
    heading_degrees: float | None
    recorded_at: datetime


class TrailOut(BaseModel):
    vehicle_id: int
    points: list[TrailPoint]


class GeofenceCreate(BaseModel):
    name: str
    color: str = "#ff3333"
    # Closed linear ring: [[lon, lat], [lon, lat], ..., first point repeated last]
    coordinates: list[list[float]] = Field(min_length=4)


class GeofenceOut(BaseModel):
    id: int
    name: str
    color: str
    coordinates: list[list[float]]
    created_at: datetime


class AlertOut(BaseModel):
    id: int
    vehicle_id: int
    vehicle_name: str
    geofence_id: int
    geofence_name: str
    event_type: str
    lat: float | None
    lon: float | None
    occurred_at: datetime


class HealthOut(BaseModel):
    status: str
    db: str
    simulator: str
    timestamp: datetime
