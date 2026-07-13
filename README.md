# HOS Truck Trip Planner

Full-stack application for planning FMCSA Hours-of-Service (HOS) compliant truck trips. Enter a route and current cycle hours, and get a schedule that never violates the 11h driving / 14h window / 30-min break / 70h cycle rules, plus an interactive route map and daily ELD-style log sheets.

**Live demo:** [spotter-ai-assessment-nu.vercel.app](https://spotter-ai-assessment-nu.vercel.app/)  
**API:** [hos-trip-planner-api-bgmv.onrender.com](https://hos-trip-planner-api-bgmv.onrender.com/api/healthcheck)

---

## Tech stack

| Layer | Technology |
|-------|-----------|
| **Frontend** | React 18, TypeScript, Vite, Tailwind CSS, react-leaflet, TanStack Query, React Hook Form + Zod |
| **Backend** | Django 5, Django REST Framework, Python 3.12 |
| **Engine** | Pure Python (stdlib only), no Django imports — independently testable |
| **Routing** | OpenRouteService `driving-hgv` profile (with offline fallback: city gazetteer + haversine) |
| **Database** | SQLite (dev/prod) — zero config |
| **Infra** | Docker, Vercel (frontend), Render (backend) |

---

## Architecture

```
frontend/                          backend/
  src/                               config/          # Django settings, URLs, WSGI
    app/          # router, provider  hos/
    components/   # UI primitives        engine/        # Pure Python HOS engine
    features/     # TripForm, map,       constants.py   # All numeric limits
                  # log sheets, summary  models.py      # SimState, Segment, etc.
    lib/          # api-client, query    cycle.py       # Rolling 70h/8-day
    types/        # Shared TS types      planner.py     # plan_trip, drive_leg
    testing/      # MSW mocks            dailylog.py    # midnight split, grouping
                                       services/
                                         routing.py     # ORS client + offline fallback
                                         trip_service.py # geocode → route → plan
                                         trip_store.py  # Django persistence
                                       models.py        # Trip ORM model (UUID PK)
                                       serializers.py   # DRF input/output
                                       views.py         # POST/GET /api/trips/
                                       tests/           # engine unit tests + API tests
```

The **engine** (`hos/engine/`) is pure Python with no Django imports. Every limit is defined in `constants.py`, the planner consumes routed legs in chunks resolving blocking rules in priority order, and `dailylog.py` splits segments at midnight into per-day log sheets.

---

## Quick start

### Backend

```bash
cd backend
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

Or with Docker: `docker compose up --build`

### Frontend

```bash
cd frontend
pnpm install
pnpm dev
```

Set `frontend/.env`:
```
VITE_APP_API_URL=http://localhost:8000/api
VITE_APP_ENABLE_API_MOCKING=false
```

Open http://localhost:3000

---

## API

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/trips/` | Plan a trip |
| `GET` | `/api/trips/{id}/` | Fetch stored trip (shareable link) |
| `GET` | `/api/healthcheck` | Liveness probe |

**POST body:**
```json
{
  "current_location": "Los Angeles",
  "pickup_location": "Phoenix",
  "dropoff_location": "Dallas",
  "current_cycle_used_hours": 0,
  "start_datetime": ""
}
```

---

## HOS rules enforced

| Rule | Status |
|------|--------|
| 11-hour driving limit | ✅ |
| 14-hour on-duty window | ✅ |
| 30-min break after 8h driving | ✅ |
| 10-hour reset | ✅ |
| 70-hour / 8-day rolling cycle | ✅ |
| 34-hour restart | ✅ |
| Fuel stop every 1,000 miles | ✅ |
| Split-sleeper berth | ⚠️ Deferred (always uses full 10h) |

---

## Testing

```bash
# Engine tests (stdlib only, no Django):
cd backend && python3 -m unittest hos.tests.test_engine -v

# Full suite (pytest required):
cd backend && pip install -r requirements-dev.txt && pytest
```

---

## Deployment

- **Frontend:** `cd frontend && pnpm build` → deploy `dist/` to Vercel
- **Backend:** Docker image deployed to Render via `backend/render.yaml`
