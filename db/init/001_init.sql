-- Real-Time GIS Fleet Tracking Platform - initial schema
-- Auto-executed once by the postgis/postgis image on first container start.

CREATE EXTENSION IF NOT EXISTS postgis;

-- Current-state cache: one row per vehicle, upserted on every simulator tick.
-- Kept separate from the time-series `positions` table below so "where is
-- everything right now" reads never have to scan history.
CREATE TABLE vehicles (
    id               SERIAL PRIMARY KEY,
    name             VARCHAR(50) NOT NULL,
    vehicle_type     VARCHAR(20) NOT NULL DEFAULT 'car',
    color            VARCHAR(7)  NOT NULL DEFAULT '#3388ff',
    current_geom     GEOMETRY(POINT, 4326),
    heading_degrees  REAL NOT NULL DEFAULT 0,
    speed_kmh        REAL NOT NULL DEFAULT 0,
    status           VARCHAR(20) NOT NULL DEFAULT 'active',
    last_seen        TIMESTAMPTZ NOT NULL DEFAULT now(),
    created_at       TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_vehicles_current_geom ON vehicles USING GIST (current_geom);

-- Append-only time-series trail. Rows are throttled on insert and purged
-- after POSITION_RETENTION_HOURS by a background task.
CREATE TABLE positions (
    id               BIGSERIAL PRIMARY KEY,
    vehicle_id       INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    geom             GEOMETRY(POINT, 4326) NOT NULL,
    speed_kmh        REAL,
    heading_degrees  REAL,
    recorded_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_positions_geom ON positions USING GIST (geom);
CREATE INDEX idx_positions_vehicle_time ON positions (vehicle_id, recorded_at DESC);

-- User-drawn geofences.
CREATE TABLE geofences (
    id          SERIAL PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    color       VARCHAR(7) NOT NULL DEFAULT '#ff3333',
    geom        GEOMETRY(POLYGON, 4326) NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_geofences_geom ON geofences USING GIST (geom);

-- Enter/exit events, written whenever a vehicle's containment state
-- flips for a given geofence.
CREATE TABLE alert_events (
    id           BIGSERIAL PRIMARY KEY,
    vehicle_id   INTEGER NOT NULL REFERENCES vehicles(id) ON DELETE CASCADE,
    geofence_id  INTEGER NOT NULL REFERENCES geofences(id) ON DELETE CASCADE,
    event_type   VARCHAR(10) NOT NULL CHECK (event_type IN ('enter', 'exit')),
    geom         GEOMETRY(POINT, 4326),
    occurred_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX idx_alerts_time ON alert_events (occurred_at DESC);
