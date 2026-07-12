# HOS Trip Planner — Backend

Django + DRF API that turns a trip (current location, pickup, dropoff, and
hours already used in the current cycle) into an **HOS-compliant schedule**, a
**route with stops**, and **daily ELD-style log sheets** for FMCSA
property-carrying interstate drivers on the 70-hour / 8-day cycle.

The heart of it is a pure-Python **scheduling engine** (`hos/engine/`) that is
guaranteed never to emit a plan violating the 11h drive / 14h window / 30-min
break / 70h cycle rules.

---

## Stack

- **Django 5 + Django REST Framework** — API + persistence
- **PostgreSQL** in prod / Docker; **SQLite** fallback for zero-config local runs
- **OpenRouteService** (`driving-hgv`) for routing + geocoding, with a built-in
  **offline estimator** so the app runs with no API key
- **Pure-Python engine** (`hos/engine/`) — no Django imports, stdlib only

---

## Quick start

### Option A — Docker (recommended; no local Python setup)

```bash
cd backend
docker compose up --build      # or: make run
# API on http://localhost:8000/api  (Postgres + web, migrations run on start)
```

Common tasks are wrapped in the `Makefile`: `make run`, `make migrate`,
`make shell`, `make test`, `make test-engine`, `make down`.

### Option B — local Python

Requires pip/venv (`sudo apt install python3.12-venv` on Debian/Ubuntu):

```bash
cd backend
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Connect the frontend

Point the client at this API and turn off the in-browser mocks:

```bash
# frontend/.env
VITE_APP_API_URL=http://localhost:8000/api
VITE_APP_ENABLE_API_MOCKING=false
```

---

## Testing

The **engine** tests are pure stdlib — no dependencies, no Django:

```bash
cd backend
python3 -m unittest hos.tests.test_engine -v
```

The **API** tests use pytest + pytest-django + factory_boy (deps required —
use Docker if pip is unavailable). This runs both suites:

```bash
# Docker (lean prod image → install dev deps for the test run):
docker compose run --rm web sh -c "pip install -q -r requirements-dev.txt && pytest -q"

# or locally:
pip install -r requirements-dev.txt && pytest
```

---

## API

| Method | Path                  | Description                              |
|--------|-----------------------|------------------------------------------|
| `POST` | `/api/trips/`         | Plan a trip, persist it, return the plan |
| `GET`  | `/api/trips/{id}/`    | Fetch a stored trip (shareable link)     |
| `GET`  | `/api/healthcheck`    | Liveness probe                           |

`POST` body:

```json
{
  "current_location": "Los Angeles, CA",
  "pickup_location": "Denver, CO",
  "dropoff_location": "New York, NY",
  "current_cycle_used_hours": 10,
  "start_datetime": "2026-07-10T08:00:00"   // optional
}
```

The response matches `frontend/src/types/api.ts` exactly (snake_case):
`summary`, `route` (`geometry`, `legs`, `stops`), `segments`, `daily_logs`.

---

## How the engine works

`plan_trip` orchestrates `drive_leg(current→pickup)` → 1h on-duty pickup →
`drive_leg(pickup→dropoff)` → 1h on-duty dropoff. `drive_leg` consumes driving
time in chunks; on each iteration it first resolves any blocking limit in
**strict priority order**:

1. **70h cycle exhausted** → insert a **34-hour restart** (only a restart fixes it)
2. **11h driving or 14h window exhausted** → insert a **10-hour reset** (sleeper)
3. **1,000-mile fuel mark reached** → insert a **30-min fuel stop** (also
   satisfies a pending break)
4. **8h cumulative driving** → insert a **30-minute break**

…then drives the largest chunk that cannot cross *any* remaining limit
(driving/window/break/cycle/fuel), emits a `DRIVING` segment, and advances
every clock. `dailylog.py` splits the resulting segments at local midnight and
groups them into per-day log sheets whose totals reconcile with the segments.

The rolling 70h is computed over on-duty *intervals* (today + prior 7 calendar
days), raised by the most recent 34h restart, so restarts and the sliding
window compose correctly.

---

## Supported HOS features vs. simplifications

| Rule / feature                              | Status |
|---------------------------------------------|--------|
| 11-hour driving limit                       | ✅ enforced |
| 14-hour on-duty window                      | ✅ enforced |
| 30-minute break after 8h driving            | ✅ enforced (any ≥30-min non-driving satisfies it) |
| 10-hour reset                               | ✅ enforced |
| 70-hour / 8-day rolling cycle               | ✅ enforced |
| 34-hour restart                             | ✅ enforced |
| Fuel stop every 1,000 miles                 | ✅ modelled as 30-min on-duty |
| 1h on-duty at pickup and dropoff            | ✅ modelled |
| Real truck routing + geometry (ORS `driving-hgv`) | ✅ when `ORS_API_KEY` set |
| Offline routing/geocoding (known US cities) | ✅ fallback when no key |
| **Split-sleeper berth (7/3, 8/2)**          | ⚠️ **deferred** — always uses a full 10h reset |
| **Seed cycle attribution**                  | ⚠️ **simplified** — `current_cycle_used_hours` is attributed entirely to the start instant (conservative: it frees up soonest, never later than reality) |
| Adverse-driving-conditions exception        | ❌ out of scope |

---

## Deployment (Render)

`render.yaml` defines a Docker web service + free Postgres. Set `ORS_API_KEY`
(optional) and `CORS_ALLOWED_ORIGINS` (your Vercel URL) in the dashboard;
`DATABASE_URL` and `DJANGO_SECRET_KEY` are wired automatically. Migrations run
on container start.

## Environment variables

See `.env.example`. Key ones: `DATABASE_URL` (Postgres; SQLite if unset),
`ORS_API_KEY` (optional), `CORS_ALLOWED_ORIGINS`, `DJANGO_SECRET_KEY`,
`DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`.
