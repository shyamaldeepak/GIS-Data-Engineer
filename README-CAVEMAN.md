# UGG. MAP GO BRRR. (Caveman Guide)

*If big words in [README.md](README.md) hurt brain, read this one instead. Same app. Silly words.*

---

## WHAT THIS THING DO

This thing make magic map. Map show little car-shapes moving around CITY, live, right now, not yesterday. You draw INVISIBLE FENCE on map (like fence for dog, but for truck). When car-shape cross fence, map SCREAM (nicely, in little box) "car went in fence!" or "car left fence!"

No real cars. Cars are pretend. Computer make them move like little ants on string. But everything ELSE — the database, the map-brain, the fence-magic — that is REAL grown-up engineer stuff. Pretend cars, real skills.

## CAVEMAN DICTIONARY

| Big Word | What It Mean, Caveman Way |
|---|---|
| **PostGIS** | Smart map-brain database. Regular database only know "this word go with that word." PostGIS also know "this DOT is INSIDE that SHAPE." Very smart rock. |
| **Geofence** | Invisible fence. Like fence for dog, except dog is truck and fence is drawn on map with finger (mouse finger). |
| **GIST index** | Caveman way to organize rocks so you find ONE rock fast, not look at ALL rocks every time. Database do same thing with map-shapes. |
| **WebSocket** | Magic string between map and brain-server that carry message FAST-FAST. No need ask-ask-ask like normal internet (that called REST, see below). String stay open, whisper new car-spot every second. |
| **REST API** | Normal internet way. You ASK "where car?" Server ANSWER "car HERE." Ask again in one minute, ask again. WebSocket better for FAST stuff, REST fine for "give me list one time." |
| **SRID 4326** | Fancy number meaning "this dot use SAME map-language as GPS satellite." Without this number, dot might mean different spot on different map. Bad. Confusing. Cavemen hate confusing. |
| **Docker** | Magic box. Put WHOLE APP in box — database, brain-server, map-screen — box work same on YOUR cave computer as on MY cave computer. No "it work on my machine" excuse. |
| **Simulator** | Pretend-car machine. Make cars walk on invisible grid-road, turn random corners, so map not boring empty blue square. |
| **Shapely** | Caveman shape-checker tool. "Is dot inside shape? Yes/no?" Very fast, very smart, lives INSIDE brain-server memory so no need ask database EVERY time (database ask is slower, like asking elder instead of just knowing). |

## HOW MAKE WORK GO (Install)

### Way 1: Docker Way (EASY WAY, DO THIS)

You need: **Docker** on your cave-computer. Get from docker.com, big blue whale logo, easy to find.

```bash
git clone https://github.com/shyamaldeepak/GIS-Data-Engineer.git
cd GIS-Data-Engineer
cp .env.example .env
docker compose up --build
```

Wait. Watch words scroll on screen (that normal, that computer thinking). When words stop scrolling fast, go to:

**http://localhost:3000**

Car-shapes should be moving. If moving = GOOD. UGG SUCCESS.

To make everything stop and rest:

```bash
docker compose down
```

### Way 2: Hard Way (No Docker, More Work, For Brave Cavemen)

You need THREE things installed by hand: Python (snake language), Node (green leaf language), and PostgreSQL-with-PostGIS (smart rock database).

```bash
# Step 1: wake up just the database (still need docker for this bit, or install Postgres+PostGIS yourself)
docker compose up db

# Step 2: wake up brain-server
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://gis_user:change_me_locally@localhost:5432/fleet_tracking
uvicorn app.main:app --reload

# Step 3 (NEW cave-window/terminal): wake up map-screen
cd frontend
npm install
npm run dev
```

Go to **http://localhost:5173**. Same map, more manual work. You brave caveman.

## HOW USE MAP (After It Work)

1. **Look** — car-shapes already moving. This normal. This good.
2. **Click "+ Draw geofence"** button (top-left of map)
3. **Click map** few times to make invisible fence shape (dots connect like connect-the-dots game)
4. **Click "Finish"** — computer ask fence name, you type name, press enter
5. **WATCH** — when car-shape walk INTO your fence, little "IN" message pop in side box. When car LEAVE fence, "OUT" message pop. THIS THE MAGIC PART.
6. Click car-name in left list, map fly-zoom to that car. Wheee.

## UGG-OH TROUBLESHOOTING

| Problem | Caveman Fix |
|---|---|
| Map screen blank white/black, no cars | Wait longer. Database slow to wake up first time (like caveman after long winter sleep). Check `docker compose logs backend` for red angry words. |
| "port already in use" angry message | Something ELSE already using that door (port). Close other app, or change `FRONTEND_PORT`/`BACKEND_PORT` in `.env` file. |
| Cars frozen, not moving | Backend brain-server maybe crash. Run `docker compose logs backend`, look for scary red text, show smart friend. |
| "docker: command not found" | Docker not installed. Go get from docker.com. Whale logo. Cannot miss it. |
| Geofence draw button do nothing | Make sure you clicked directly ON map (not sidebar), and clicked AT LEAST 3 times before hitting Finish. Two dots not make shape. Need three, minimum, for baby triangle. |

## WHY CAVEMAN MADE THIS

Caveman want show can build REAL data-engineer thing: real database with map-brain (PostGIS), real live-update magic (WebSocket), real fence-crossing detection (geofencing), all wrapped in one-button install (Docker). Built in spirit of BIG fancy map company apps (you know, the ones on your phone that talk and say "turn left") — same ideas, cave-scale, but SAME BRAIN PARTS work same way.

Grown-up version of this document at [README.md](README.md), if you want ALL the smart words and tables and diagrams.

UGG. THE END. GO PLAY WITH MAP NOW.
