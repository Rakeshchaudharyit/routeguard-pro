# RouteGuard Pro

**Weather-aware route comparison | Django REST Framework · React · TypeScript**

RouteGuard Pro is a full-stack route-planning prototype that compares driving alternatives and provides checkpoint-level weather context. It combines route geometry, estimated travel times, cargo weight and forecast conditions in one dashboard, so a reviewer can inspect both the route recommendation and the underlying conditions.

> **Scope:** Technical assessment prototype. RouteGuard is **not** a commercial truck-navigation or safety-certified dispatch product. Its public routing provider does not account for truck-specific restrictions such as bridge clearances, axle loads or hazardous-material routes. Weather assessments are advisory and may be incomplete.

## Features

- Compare alternative road routes with distance and estimated duration.
- Analyze forecast conditions at configurable 10-, 25- or 50-mile checkpoints.
- Inspect cargo-weight-aware risk indicators and route recommendations when forecast coverage permits.
- Explore a 48-hour weather corridor and detailed checkpoint forecasts.
- Switch route alternatives on an interactive map, locate checkpoints and reset the map view.
- Retain the last successful analysis and retry after API failures.
- Use the responsive dashboard on desktop and mobile devices.

## Technology

| Layer | Stack |
| --- | --- |
| Frontend | React 19, TypeScript, Vite 6 |
| Backend | Python, Django 5.2, Django REST Framework |
| Integrations | Public geocoding, OSRM routing and weather forecast services |
| Testing | Django test runner; Node built-in test runner; TypeScript/Vite build |

## Prerequisites

- Python **3.11+** (previously tested on Python 3.13)
- Node.js compatible with Vite 6, and npm
- Internet access for external routing, geocoding and weather services

## Quick start

Clone the repository and open a terminal at its root. Start the backend first.

**Terminal 1 — Django API**

```bash
python3 -m venv .venv
source .venv/bin/activate              # Windows: .venv\Scripts\activate
python -m pip install -r backend/requirements.txt
cd backend
python manage.py check
python manage.py migrate
python manage.py runserver 8010
```

The API is available at `http://127.0.0.1:8010`.

**Terminal 2 — React dashboard**

```bash
cd frontend
npm ci --include=dev
npm run dev
```

Open the address printed by Vite, typically `http://localhost:5173`.

### Environment configuration

The default local setup works with the API on port `8010`. For a different backend URL, create `frontend/.env.local` from `frontend/.env.example` and set:

```dotenv
VITE_API_BASE_URL=http://127.0.0.1:8010
```

Restart Vite after changing environment variables. The backend sample `backend/.env.example` documents `DJANGO_DEBUG`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` and `CORS_ALLOWED_ORIGINS`. **Django does not automatically read `.env` files in this project**: export these variables in the shell or configure them in your deployment environment. Never commit actual secrets.

## How to use RouteGuard

1. Open the dashboard and enter an **origin** and **destination**, such as *Dallas, TX* and *Atlanta, GA*.
2. Select a **future departure date/time**, provide the **cargo load weight** in pounds and choose the **checkpoint interval** (10, 25 or 50 miles).
3. Click **Analyze Routes**. The API retrieves route alternatives and available forecast data; processing depends on public service availability.
4. Review the route cards and select an alternative to compare its map geometry, travel estimate and weather checkpoints.
5. Open **Weather Intelligence** to inspect the 48-hour forecast corridor. The corridor shows fixed forecast hours; arrival-time checkpoint assessments are a separate view.
6. Open checkpoint details to review the wind, rainfall, snowfall and risk indicators. Use **Locate on Map** and **Reset Map View** when exploring locations.
7. If the request fails, use **Retry Analysis**. The last successful result remains visible; do not confuse it with a newly completed analysis.

**Important:** Forecasts can be partial or unavailable. An unavailable forecast does **not** mean low risk. Weather-aware recommendations may be withheld when data coverage or conditions are unsuitable. The backend supports departures within a 72-hour forecast window for weather assessment.

## API reference

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health/` | Service health status |
| `GET` | `/api/geocode/?q=Dallas` | Resolve a location query |
| `POST` | `/api/routes/analyze/` | Compare routes and assess available weather forecasts |

**Example request** (replace `departure_at` with a future ISO 8601 timestamp):

```bash
curl -X POST http://127.0.0.1:8010/api/routes/analyze/ \
  -H 'Content-Type: application/json' \
  -d '{"origin":"Dallas, TX","destination":"Atlanta, GA","departure_at":"2026-11-02T12:00:00Z","load_weight_lb":32000,"checkpoint_interval_miles":25}'
```

The departure timestamp must include a timezone offset. Valid checkpoint intervals are **10, 25, 50** miles; cargo weight must be between **0 and 200,000 lb**. A successful response contains resolved locations, route alternatives, weather coverage, warnings and an optional recommendation. Public provider failures may return an error or incomplete weather coverage.

## Project structure

```text
routeguard/
├── backend/
│   ├── config/               # Django settings and URL configuration
│   ├── routing/              # Geocoding, routes, forecasts and API tests
│   ├── risk/                 # Weather and cargo risk calculations
│   ├── requirements.txt
│   └── manage.py
├── frontend/
│   ├── src/                  # React dashboard, API client and validation
│   ├── tests/                # Frontend response-validation tests
│   ├── package.json
│   └── .env.example
├── docs/
│   ├── VERIFICATION.md
│   └── DEPLOYMENT.md
└── README.md
```

## Tests and quality checks

**Backend** (activate `.venv` first):

```bash
cd backend
python manage.py check
python manage.py test
```

**Frontend:**

```bash
cd frontend
npm ci --include=dev
npm test
npm run build
```

**Last developer-reported checks — October 31, 2026:** Django system checks clean; **25/25 backend tests passed**; **4/4 frontend tests passed**; TypeScript compilation and Vite production build passed; npm audit reported **0 vulnerabilities**. These results were reported from a local Mac environment, not a production deployment. See [Verification](docs/VERIFICATION.md) for manual acceptance steps.

## Design decisions and limitations

- **Explainability over a single score:** Route alternatives, coverage, risk labels and checkpoint observations are exposed together.
- **Graceful degradation:** Route analysis can remain available when weather data is missing; the UI must not claim that missing weather is safe.
- **External data dependency:** Public geocoding, routing and weather services have availability, accuracy and usage limits.
- **Truck restrictions:** Public OSRM routes are not truck-specific. Do not use this prototype for real commercial fleet navigation.
- **Production deployment:** Local `runserver` and the Vite development server are for development only. Production hosting requires a proper application server, TLS, trusted origins and provider/licensing review. See [Deployment notes](docs/DEPLOYMENT.md).

## Assessment walkthrough

A short review can cover Dallas → Atlanta route analysis, route switching and map synchronization, checkpoint details, the 48-hour corridor, and a simulated backend outage followed by Retry Analysis. A second long-distance trip can be used to demonstrate forecast coverage limits.

---

Built as a technical assessment demonstrating end-to-end API integration, route visualization, weather-risk modeling and resilient frontend behavior.
