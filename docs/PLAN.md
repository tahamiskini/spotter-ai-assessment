# HOS Truck Trip Planner — Implementation Plan

## Context

This is a full-stack coding assessment: build an app where a driver enters a trip
(current location, pickup, dropoff, and hours already used in their current cycle) and
receives an **HOS-compliant schedule**, a **route map with stops**, and **daily ELD-style
log sheets**. The domain is FMCSA Hours-of-Service rules for property-carrying interstate
truckers on the 70-hour/8-day cycle (no adverse-condition exceptions).

The assessment is graded on a live hosted app, a 3–5 min Loom demo, and a GitHub repo.
Graders test the deployed app for **HOS accuracy** and care about **UI/UX quality**.
The hard/risky part is the scheduling engine that must *never* violate the rules; the map
and log rendering are the visible polish.

This is a **greenfield build** — no existing code. Environment has Python 3.12 and Docker;
**Node/npm is not installed yet** and must be added (via nvm) before frontend work.

### Locked decisions
- **Routing/Map:** OpenRouteService (free key — distance, driving duration, geometry; use
  the `driving-hgv` truck profile) + geocoding via ORS/Nominatim. Map rendered with
  **react-leaflet** + free OpenStreetMap tiles.
- **Deploy:** React → **Vercel**; Django → **Render** web service + **Render Postgres**.
- **HOS scope (v1):** core rules (11h drive, 14h window, 30-min break, 10h reset,
  70h/8-day cycle) **+ fuel stops (every 1,000 mi) + 34-hour restart**.
  **Split-sleeper is deferred** (documented as a known simplification).
- **Persistence:** **PostgreSQL** — Docker locally, Render Postgres in prod. Each trip and
  its computed plan is stored and retrievable by ID (shareable link + history for the demo).

---

## Architecture

```
hos-trip-planner/
  backend/                 # Django + DRF
    config/                # settings, urls, wsgi
    hos/
      engine/              # PURE python, no Django import (unit-testable)
        constants.py       # all HOS numeric limits
        models.py          # Status enum, Segment, Leg, TripInput, SimState (dataclasses)
        cycle.py           # cycle_used_at, cycle_available_at, add_onduty, reset_cycle
        planner.py         # plan_trip, drive_leg, emit_driving, insert_rest, do_activity
        dailylog.py        # split_at_midnight, group_by_day, day_totals
      services/
        routing.py         # OpenRouteService client -> builds two Leg objects
        trip_service.py    # geocode -> route -> plan_trip -> persist
      models.py            # Trip (Django ORM), stored inputs + serialized plan
      serializers.py       # DRF
      views.py             # API endpoints
      tests/               # engine unit tests + API tests
    requirements.txt
    Dockerfile / render.yaml
    docker-compose.yml     # local Postgres
  frontend/                # React (Vite + TypeScript)
    src/
      api/                 # fetch client
      components/          # TripForm, RouteMap, LogSheet, TripSummary, StopsList
      pages/               # PlanTrip, TripResult
    package.json
  README.md                # setup, stack, assumptions, HOS features vs simplifications
```

---

## Backend

### 1. HOS scheduling engine (`hos/engine/`) — the core, build & test first

Pure functions, no Django. Full algorithm design validated separately; key points:

- **State (`SimState`)** tracks five independent clocks: shift driving hrs (11h),
  14h window start, cumulative driving since last ≥30-min break, rolling 70h/8-day
  on-duty (dict `onduty_by_day: date -> hours` + seed), and miles-since-fuel.
- **`plan_trip(trip)`** orchestrates: `drive_leg(current→pickup)` → 1h ODND pickup →
  `drive_leg(pickup→dropoff)` → 1h ODND dropoff. Assumes the driver came on duty at
  `start_dt` following a qualifying 10h off period (shift counters start at 0).
- **`drive_leg`** consumes the leg's driving *time* in chunks. Each iteration:
  - **STEP A — resolve blocking limits in strict priority order:**
    1. **70h cycle exhausted → insert 34h restart** (only a restart can fix it; test first).
    2. **11h driving hit OR 14h window exhausted → insert 10h reset** (SLEEPER).
    3. **8h cumulative driving → insert 30-min break.**
  - **STEP B** — drive `chunk = min(leg remainder, 11h left, 14h window left,
    8h-to-break, 70h available, hours-to-next-fuel-mark)`; never overshoots a limit.
  - **STEP C** — emit DRIVING segment, advance clock, update all counters.
  - **STEP D** — if 1,000 mi reached, insert 30-min ODND fuel stop, reset fuel miles.
- **Reset semantics** (`insert_rest`): any ≥30-min non-driving resets the break counter
  (so a fuel stop or pickup naturally satisfies a pending break); ≥10h resets shift +
  window; ≥34h additionally clears the cycle (`reset_cycle`).
- **Rolling 70h** (`cycle_used_at`): sum on-duty over today + prior 7 local-calendar days,
  plus the seed while it's still in-window. **Seed simplification:** attribute
  `current_cycle_used_hours` entirely to the start date (conservative / safe direction —
  document this).
- **Miles-driven** derived from per-leg constant speed (`distance/duration`), used only for
  fuel accounting — never re-derive time from miles.
- **`dailylog.py`** splits segments at local midnight and groups by day for log rendering;
  per-day on-duty totals must equal `onduty_by_day` (invariant test).

**Engine unit tests (correctness anchors):** no-limit short trip; forced 10h reset;
30-min break at 8h; fuel stop combining with a break; ≥2× 34h restarts; cycle near 70 →
restart before driving/pickup; midnight split totals match; 14h window closing before 11h.

### 2. Routing service (`services/routing.py`)
- ORS client: geocode the three location strings → lat/lng; request two directions calls
  (`driving-hgv`) → `duration_s`, `distance_m`, geometry per leg → build `Leg` objects.
- API key from env (`ORS_API_KEY`). Handle geocode failures with clear 400 errors.

### 3. Django model + API
- `Trip` model: input fields (locations, cycle_used, start_dt) + JSON fields for the
  computed `segments`, `daily_logs`, `route` (geometry + stops), and `summary`.
- Endpoints (DRF):
  - `POST /api/trips/` — accept inputs, run `trip_service.plan()`, persist, return full result + id.
  - `GET /api/trips/{id}/` — fetch a stored trip (shareable link / history).
- `summary`: total distance, total driving hrs, #days, #breaks, #rests, on-duty added to
  cycle, and whether a 34h restart was used.

### 4. Data / config
- `docker-compose.yml` for local Postgres; `DATABASE_URL` via `dj-database-url`.
- `django-cors-headers` (allow the Vercel origin), `python-dotenv`/env settings,
  `gunicorn` for prod, `whitenoise` if serving anything static.

---

## Frontend (React + Vite + TS)

- **TripForm** — inputs for current/pickup/dropoff locations, current cycle used (hrs),
  optional start date/time. Location fields use ORS/Nominatim autocomplete (nice-to-have;
  plain text acceptable). Client-side validation, loading state on submit.
- **RouteMap** — react-leaflet + OSM tiles; draw the route polyline from returned geometry;
  markers for pickup, dropoff, fuel stops, breaks, and overnight rests (distinct icons).
- **LogSheet** — for each day, an ELD-style 24-hour grid (4 rows: Off Duty / Sleeper /
  Driving / On Duty ND) with the duty-status line drawn from that day's segments, plus
  per-status totals and a remarks column. This is the signature visual — invest in it.
- **TripSummary** — distance, driving hours, #days, #breaks/rests, on-duty added, restart used.
- **StopsList** — chronological list of segments/stops with times, locations, and remarks.
- Clean, professional, responsive styling (Tailwind or CSS modules). Result page reachable
  by `/trips/{id}` for shareable links.

---

## Deployment
- **Backend → Render:** web service (gunicorn), `render.yaml`, attached Render Postgres,
  env vars (`ORS_API_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `CORS` origin). Run migrations.
- **Frontend → Vercel:** Vite build, `VITE_API_BASE_URL` env pointing at the Render backend.
- **README:** setup steps, stack, assumptions, and a clear "Supported HOS features vs.
  simplifications" table (note deferred split-sleeper and the seed-attribution assumption).

---

## Suggested build order
1. Scaffold repo + backend Django project + Docker Postgres; install Node via nvm.
2. **Engine + unit tests first** (`hos/engine/*`) — get HOS correctness locked before UI.
3. Routing service against ORS (real key); `trip_service` wiring; Trip model + migrations.
4. DRF endpoints; verify end-to-end with a real request.
5. React scaffold; TripForm → API → TripResult (map, log sheets, summary).
6. Styling/polish; deploy backend (Render) then frontend (Vercel); record Loom.

## Verification
- **Engine:** `pytest` on the engine test suite — the anchor cases above must pass; assert
  no plan ever exceeds 11h drive / 14h window / 70h cycle and that daily on-duty totals
  reconcile with `onduty_by_day`.
- **API:** `POST /api/trips/` with (a) a short intra-day trip, (b) a long multi-day trip
  (e.g. LA→NYC) that forces resets/fuel/restart, (c) `current_cycle_used=68` to force an
  early restart. Confirm returned segments are ordered, gapless, and rule-compliant.
- **Frontend:** run the dev server, submit each scenario, confirm the map draws the route +
  correctly-typed stop markers and the log sheets render one grid per day with totals
  summing to 24h. Cross-check a hand-computed small trip against the rendered schedule.
- **Live:** repeat scenario (b) against the deployed Vercel URL end-to-end before recording.
```
