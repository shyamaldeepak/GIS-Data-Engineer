# Live Fleet Tracker

**A real-time GIS data engineering platform: simulated fleet tracking, geofencing, and live alerts — built on PostGIS, FastAPI, WebSockets, and MapLibre GL.**

This project is designed in the spirit of production-grade mapping and logistics platforms like Apple Maps, Uber, and Flightradar24 — applying the same core GIS data engineering patterns (spatial indexing, geofencing, real-time streaming pipelines) at portfolio scale, entirely self-contained with no external API keys required.

---

## Overview

A backend simulator streams the live positions of a fleet of vehicles moving through a city grid. Every position update flows through PostGIS, is checked against user-drawn geofences for enter/exit events, and is pushed to the browser over a WebSocket. The frontend renders everything live on a MapLibre map: moving vehicles with heading-rotated icons, a fleet list, a geofence drawing tool, and a real-time alert feed.

No API keys, no external map provider accounts, no paid services — `docker compose up` and it runs.

## Features

- **Live vehicle tracking** — a fleet of simulated vehicles moves along a synthetic road grid, broadcasting position, speed, and heading every second over WebSockets.
- **Geofencing** — draw a polygon directly on the map; the backend tracks per-vehicle containment state and fires enter/exit events the instant a vehicle crosses the boundary.
- **Live alert feed** — geofence crossings appear in the UI in real time, no polling or refresh required.
- **Historical trails** — every vehicle's recent path is persisted as a time-series and queryable via the REST API.
- **Fully self-contained** — the simulator generates its own synthetic road network and vehicle movement, so the whole stack runs offline with zero external dependencies beyond the Docker images and one free, no-key basemap tile source.
- **One-command install** — `docker compose up --build` brings up the database, backend, and frontend together.

## Architecture

```mermaid
flowchart LR
    subgraph Backend [FastAPI Backend Container]
        SIM[Simulator<br/>grid-graph vehicle movement]
        GEO[Geofence Engine<br/>in-memory Shapely cache]
        WS[WebSocket Manager]
        REST[REST Routers]
    end

    DB[(PostGIS<br/>vehicles / positions /<br/>geofences / alert_events)]

    subgraph Frontend [Nginx + React Container]
        PROXY[Nginx reverse proxy]
        UI[React + MapLibre GL UI]
    end

    SIM -->|UPDATE / INSERT| DB
    SIM --> GEO
    GEO -->|INSERT alert_events| DB
    GEO -->|broadcast| WS
    SIM -->|broadcast tick| WS
    REST <--> DB
    WS -->|/ws/live| PROXY
    REST -->|/api/*| PROXY
    PROXY --> UI
    UI -->|draw geofence| REST
```

## GIS Concepts Explained

This project was built to demonstrate — not just use — core GIS data engineering patterns:

- **Spatial indexing (GIST)** — every geometry column (`vehicles.current_geom`, `positions.geom`, `geofences.geom`) has a PostGIS GIST index, so spatial queries (containment, nearest-neighbor, bounding-box filters) stay fast as the dataset grows, instead of degrading to full table scans.
- **SRID / coordinate systems** — all geometry is stored as `SRID 4326` (WGS84 lat/lon, the standard for GPS data), with explicit `ST_SetSRID` calls on every write so there's never ambiguity about which coordinate reference system a geometry is in.
- **Geofencing via point-in-polygon** — geofence containment is a classic point-in-polygon problem. Rather than running `ST_Contains` against Postgres on every vehicle on every tick (which would not scale), geofences are cached in-process as Shapely polygons and checked in memory; Postgres remains the source of truth and is only re-queried when a geofence is created or deleted.
- **Current-state vs. time-series schema design** — `vehicles.current_geom` is a hot, frequently-upserted "where is everything right now" cache, while `positions` is an append-only time-series trail. Splitting these is a deliberate real-world data engineering pattern: it keeps "give me current fleet state" queries cheap while still preserving full history for trail/analytics queries, with a retention sweep to bound table growth.
- **Real-time streaming pipeline design** — the simulator → PostGIS → WebSocket broadcast path mirrors how production GPS ingestion pipelines work: normalize incoming positions, persist them, evaluate business rules (geofences) against the new state, then fan the result out to connected clients — all without polling.

## Tech Stack

| Layer | Technology | Why |
|---|---|---|
| Database | PostgreSQL + PostGIS 16 | Industry-standard spatial database; native geometry types, spatial indexes, and functions |
| Backend | FastAPI + asyncpg | Async Python web framework with native WebSocket support; asyncpg for fast, direct SQL access |
| Spatial logic | Shapely | In-memory geometry operations for real-time geofence containment checks |
| Frontend | React + TypeScript + Vite | Modern, fast, type-safe UI development |
| Map rendering | MapLibre GL JS | Open-source, no API key required, WebGL-accelerated vector maps |
| Basemap | CARTO (free, no signup) | No-key basemap tiles suitable for demos and production alike |
| State management | Zustand | Minimal, fast client-side store for live data |
| Geometry math | Turf.js | Client-side polygon validation (self-intersection checks) for the geofence drawing tool |
| Deployment | Docker Compose | Single-command install: database + backend + frontend together |

## Project Structure

```
gis-data-engineer-project/
├── docker-compose.yml
├── .env.example
├── db/init/001_init.sql        # PostGIS schema, auto-run on first container start
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   └── app/
│       ├── main.py             # FastAPI app, lifespan startup, retention sweep
│       ├── config.py           # Environment-driven settings
│       ├── database.py         # asyncpg pool with startup retry
│       ├── simulator.py        # Grid-graph vehicle movement engine
│       ├── geofence_engine.py  # In-memory geofence containment + alerting
│       ├── ws_manager.py       # WebSocket connection manager
│       ├── schemas.py          # Pydantic request/response models
│       └── routers/            # health, vehicles, geofences, alerts, ws
└── frontend/
    ├── Dockerfile               # Multi-stage: Node build -> Nginx serve
    ├── nginx.conf                # Reverse-proxies /api and /ws to the backend
    └── src/
        ├── App.tsx, main.tsx, store.ts
        ├── api/                  # REST client + WebSocket client
        └── components/           # MapView, Sidebar, GeofenceDrawTool, AlertFeed, StatsBar
```

## Requirements

- **Docker & Docker Compose** (recommended path) — [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- **Or, for a manual install:** Python 3.12+, Node.js 20+, PostgreSQL 16 with the PostGIS extension

## Installation

### Option A — Docker Compose (recommended)

```bash
git clone https://github.com/shyamaldeepak/GIS-Data-Engineer.git
cd GIS-Data-Engineer
cp .env.example .env
docker compose up --build
```

Then open **http://localhost:3000**. That's it — the database schema, backend, simulator, and frontend all start together.

To stop:

```bash
docker compose down        # stop containers, keep data
docker compose down -v     # stop containers and wipe the database volume
```

### Option B — Manual local install (no Docker)

```bash
# 1. Start just the database
docker compose up db
# (or install PostgreSQL 16 + PostGIS locally and run db/init/001_init.sql yourself)

# 2. Backend
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://gis_user:change_me_locally@localhost:5432/fleet_tracking
uvicorn app.main:app --reload

# 3. Frontend (in a second terminal)
cd frontend
npm install
npm run dev
```

Then open **http://localhost:5173** (Vite's dev server proxies `/api` and `/ws` to `localhost:8000`).

## Environment Variables

| Variable | Default | Description |
|---|---|---|
| `POSTGRES_USER` / `POSTGRES_PASSWORD` / `POSTGRES_DB` | see `.env.example` | Database credentials |
| `DATABASE_URL` | built from the above | Full asyncpg connection string used by the backend |
| `SIM_VEHICLE_COUNT` | `12` | Number of simulated vehicles |
| `SIM_TICK_SECONDS` | `1` | Simulator update interval |
| `SIM_CITY_BBOX` | downtown San Francisco | `min_lon,min_lat,max_lon,max_lat` bounding box for the simulated road grid |
| `POSITION_RETENTION_HOURS` | `24` | How long time-series position history is kept before the hourly retention sweep purges it |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Allowed frontend origins |
| `VITE_MAP_STYLE_URL` | CARTO dark-matter style | MapLibre basemap style URL (no key required) |

## API Reference

### REST

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service + database + simulator status |
| `GET` | `/api/vehicles` | Current position/speed/heading of every vehicle |
| `GET` | `/api/vehicles/{id}/trail?minutes=10` | Recent position history for one vehicle |
| `GET` | `/api/geofences` | List all geofences |
| `POST` | `/api/geofences` | Create a geofence: `{ name, color, coordinates: [[lon, lat], ...] }` |
| `DELETE` | `/api/geofences/{id}` | Delete a geofence |
| `GET` | `/api/alerts?limit=50&vehicle_id=&geofence_id=` | Recent geofence enter/exit events |

### WebSocket — `/ws/live`

On connect, the server immediately sends a `snapshot` message with full current state, then streams:

| `type` | Payload |
|---|---|
| `snapshot` | `{ vehicles, geofences, alerts }` — sent once on connect |
| `tick` | `{ vehicles: [...] }` — batched position update, sent every simulator tick |
| `alert` | A single enter/exit event, sent the instant it happens |
| `geofence_created` | `{ geofence }` |
| `geofence_deleted` | `{ geofence_id }` |

## Usage Walkthrough

1. Open the app — vehicles appear immediately and start moving along the simulated road grid.
2. Click **"+ Draw geofence"**, click points on the map to place a polygon, then **Finish** and give it a name.
3. Watch the **Live Alerts** panel — as soon as a vehicle enters or exits your geofence, an alert appears instantly.
4. Click a vehicle in the sidebar to fly the map to it and see its current speed.
5. Query `GET /api/vehicles/{id}/trail?minutes=5` to pull that vehicle's recent path as raw GeoJSON-friendly points.

## Roadmap

- Real road-network routing (OSM/OSRM) instead of the synthetic grid graph
- Alembic migrations for schema versioning
- Authentication and per-user fleets
- Kafka / Redis Streams for horizontally-scalable ingestion
- Historical trail playback UI (scrub through a vehicle's past route)

## License

MIT — see [LICENSE](LICENSE).
