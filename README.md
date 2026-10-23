# TruckRoute | Weather-Aware Freight Routing & Risk Engine

A high-performance logistics dispatch and navigation platform built with **Django REST Framework** and **React (Vite) + Leaflet**. TruckRoute empowers commercial fleet operators and independent drivers to select optimal driving routes by evaluating dynamic weather hazards, cargo load weights, and arrival-time checkpoints along major transportation corridors.

---

## Table of Contents
1. [System Overview & Commercial Motivation](#1-system-overview--commercial-motivation)
2. [Prerequisites & System Requirements](#2-prerequisites--system-requirements)
3. [Local Development Setup](#3-local-development-setup)
4. [Backend Architecture & Technical Deep Dive](#4-backend-architecture--technical-deep-dive)
   - [Route Generation & Alternate Bypass Corridors](#41-route-generation--alternate-bypass-corridors)
   - [Equidistant Sampling & Arrival ETA Calculation](#42-equidistant-sampling--arrival-eta-calculation)
   - [Temporal Meteorological Integration](#43-temporal-meteorological-integration)
   - [Risk Matrix & Cargo Weight Escalation Engine](#44-risk-matrix--cargo-weight-escalation-engine)
   - [4-Tier Recommendation Decision Engine](#45-4-tier-recommendation-decision-engine)
   - [Corridor Spatial Weather Mesh](#46-corridor-spatial-weather-mesh)
5. [Frontend Architecture & UI Mechanics](#5-frontend-architecture--ui-mechanics)
   - [Component Hierarchy](#51-component-hierarchy)
   - [Map Rendering & Color-Coded Polylines](#52-map-rendering--color-coded-polylines)
   - [0–48h Forecast Timeline Scrubber & Heatmap](#53-048h-forecast-timeline-scrubber--heatmap)
   - [Enterprise Logistics Styling](#54-enterprise-logistics-styling)
6. [Complete REST API Specification](#6-complete-rest-api-specification)
   - [POST /api/routes/analyze/](#post-apiroutesanalyze)
   - [GET /api/geocode/](#get-apigeocode)
   - [GET /api/health/](#get-apihealth)
7. [Free Cloud Deployment Guide (Render & Vercel)](#7-free-cloud-deployment-guide-render--vercel)
8. [Automated Testing & Quality Assurance](#8-automated-testing--quality-assurance)
9. [Operational Considerations & Troubleshooting](#9-operational-considerations--troubleshooting)
10. [Walkthrough Script (5–10 min)](#10-walkthrough-script-510-min)

---

## 1. System Overview & Commercial Motivation

Commercial freight transit differs fundamentally from passenger vehicle navigation. Loaded semi-trailers (up to 80,000 lbs Gross Vehicle Weight) and high-cube dry vans (13’6” height) exhibit high centers of gravity, making them susceptible to rollover from lateral wind gusts exceeding 35 mph. Furthermore, heavy snowfall reduces traction exponentially on mountain passes, leading to road closures and supply chain delays.

Standard navigation APIs (Google Maps, Mapbox, Apple Maps) optimize strictly for shortest travel time or minimal distance under static current conditions. They do not calculate what the weather will be at the exact time the vehicle enters a specific corridor 8 to 14 hours down the road.

**TruckRoute solves this through temporal-spatial coupling:**
1. It queries multiple alternative route geometries.
2. It projects the truck's position over time using continuous speed and distance interpolation.
3. It samples meteorological forecast data precisely at each checkpoint's estimated time of arrival (ETA).
4. It applies physical vehicle load rules (30,000 lb and 40,000 lb crosswind escalation thresholds).
5. It balances safety and duration to select the optimal route using a prioritized 4-tier decision hierarchy.

```
┌────────────────────────────────────────────────────────────────────────┐
│                        React 19 + Leaflet UI                           │
│  - Origin & Destination with Debounced Autocomplete                    │
│  - Cargo Load Presets (15k, 32k, 42k, 52k lbs)                         │
│  - 3 Route Options Side-by-Side Comparison Cards                       │
│  - Dynamic Segmented Risk Polyline Overlay                             │
│  - Checkpoint Markers with Meteorological Tooltips & Load Alerts       │
│  - 0–48h Rolling Forecast Scrubber with Animated Heatmap Canvas        │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ JSON REST API
┌───────────────────────────────────▼────────────────────────────────────┐
│                    Django 5.1 REST Framework Backend                   │
│  ├── router.py         Guarantees 3 distinct highway corridors         │
│  ├── sampling.py       Samples polylines at 10, 25, or 50 mi + ETA     │
│  ├── weather.py        Batch queries Open-Meteo hourly at checkpoint   │
│  ├── risk_engine.py    Applies wind/rain/snow & load weight rules      │
│  ├── recommendation.py 4-tier safety-first tiebreaker ranking          │
│  ├── corridor.py       Builds 48-hour spatial heatmap mesh             │
│  └── geocoding.py      Photon/Nominatim address autocomplete           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Upstream APIs
                 ┌──────────────────┴──────────────────┐
                 ▼                                     ▼
        OSRM Routing Engine                 Open-Meteo Forecast
       (router.project-osrm.org)            (api.open-meteo.com)
```

---

## 2. Prerequisites & System Requirements

### Runtime Environment
- **Operating System**: Linux (Ubuntu 20.04+ / Debian 11+), macOS (12+), or Windows 10/11 with WSL2.
- **Python**: Version `3.10` or higher (`python3 --version`).
- **Node.js**: Version `18.0.0` or higher (`node --version`).
- **Package Managers**: `pip` (Python) and `npm` (Node).
- **Network Access**: Outbound HTTPS access on port 443 to:
  - `router.project-osrm.org` (Routing service)
  - `api.open-meteo.com` (Weather forecast service)
  - `photon.komoot.io` / `nominatim.openstreetmap.org` (Geocoding services)
  - `tiles.stadiamaps.com` (Map tile provider — Stadia Maps, OSM-based)

---

## 3. Local Development Setup

### 3.1 Clone Repository
```bash
git clone <repository_url>
cd truck-routing
```

### 3.2 Backend Setup (Django)
```bash
cd backend

# 1. Create and activate Python virtual environment
python3 -m venv venv
source venv/bin/activate       # On Windows PowerShell: .\venv\Scripts\Activate.ps1

# 2. Upgrade pip and install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# 3. Apply database migrations
python manage.py migrate

# 4. Run automated test suite to verify installation
pytest

# 5. Start the backend development server
python manage.py runserver 0.0.0.0:8000
```
The Django REST API is now live at `http://127.0.0.1:8000/api/health/`.

### 3.3 Frontend Setup (React + Vite)
In a separate terminal window:
```bash
cd frontend

# 1. Install Node dependencies
npm install

# 2. Configure map tile API key (Stadia Maps — free at stadiamaps.com/pricing/)
cp .env.example .env
# Edit .env and set your key:
# VITE_STADIA_API_KEY=your_api_key_here

# 3. Start Vite development server
npm run dev -- --port 5173
```
Open your browser and navigate to `http://localhost:5173`. The Vite development server automatically proxies all `/api/*` network requests to `http://127.0.0.1:8000`.

> **Map Tile Provider**: TruckRoute uses [Stadia Maps](https://stadiamaps.com/) (`alidade_smooth` style) for OSM-based tiles that are compliant with the [OSM Tile Usage Policy](https://operations.osmfoundation.org/policies/tiles/). A free API key is required (200k tile requests/day on the free tier). Set `VITE_STADIA_API_KEY` in your `.env` file (local dev) or as an environment variable in your deployment platform (Render/Vercel).

### 3.4 Production Preview Mode (Single Port)
To verify how the application behaves in production with Django serving the compiled React frontend directly:
```bash
# Build the frontend bundle
cd frontend
npm run build

# Collect static assets into Django static root
cd ../backend
source venv/bin/activate
python manage.py collectstatic --noinput

# Launch with Gunicorn production server
gunicorn truck_routing.wsgi:application --bind 0.0.0.0:8000
```
Both the React single-page application and the REST API are now served simultaneously on `http://127.0.0.1:8000/`.

---

## 4. Backend Architecture & Technical Deep Dive

### 4.1 Route Generation & Alternate Bypass Corridors
File: [`backend/routing_app/services/router.py`](file:///Ubuntu-22.04/home/Projects/truck-routing/backend/routing_app/services/router.py)

Commercial dispatch requires evaluating multiple routes (e.g., Northern Interstate vs. Central Turnpike vs. Southern Expressway). Standard OSRM instances frequently return only 1 or 2 routes if alternatives are not sufficiently distinct.

**Algorithm:**
1. Primary call to OSRM: `GET /route/v1/driving/{lon1},{lat1};{lon2},{lat2}?overview=full&geometries=geojson&alternatives=3&steps=true`.
2. If fewer than 3 distinct routes are returned, the service computes a perpendicular lateral offset from the geometric midpoint:
   $$\vec{v} = (\text{lat}_2 - \text{lat}_1, \text{lon}_2 - \text{lon}_1)$$
   $$\vec{u}_{\perp} = \left(-\frac{\Delta\text{lon}}{\|\vec{v}\|}, \frac{\Delta\text{lat}}{\|\vec{v}\|}\right)$$
   $$\text{Waypoint} = \text{Midpoint} \pm (k \times \vec{u}_{\perp})$$
3. A multi-segment highway query is issued through the calculated waypoint:
   `GET /route/v1/driving/{origin};{waypoint};{destination}`
4. Duplicate routes (routes with $< 5\text{ mi}$ distance and $< 5\text{ min}$ duration variance) are filtered out, guaranteeing exactly 3 distinct route options.

### 4.2 Equidistant Sampling & Arrival ETA Calculation
File: [`backend/routing_app/services/sampling.py`](file:///Ubuntu-22.04/home/Projects/truck-routing/backend/routing_app/services/sampling.py)

To measure environmental exposure accurately, routes are sampled at discrete intervals (10, 25, or 50 miles).

1. **Haversine Distance**: Given two points $(\phi_1, \lambda_1)$ and $(\phi_2, \lambda_2)$:
   $$a = \sin^2\left(\frac{\Delta\phi}{2}\right) + \cos(\phi_1)\cos(\phi_2)\sin^2\left(\frac{\Delta\lambda}{2}\right)$$
   $$d = 2 R \cdot \text{atan2}\left(\sqrt{a}, \sqrt{1-a}\right), \quad R = 3958.8\text{ miles}$$
2. **Polyline Interpolation**: Cumulative distances are computed across all coordinate vertices. For each target mileage ($0, \Delta, 2\Delta, \dots$), linear spherical interpolation locates the exact coordinate.
3. **Arrival ETA Projection**:
   $$t_{\text{elapsed}} = \left(\frac{d_{\text{checkpoint}}}{d_{\text{total}}}\right) \times \text{Duration}_{\text{total}}$$
   $$\text{ETA} = \text{DepartureTime} + t_{\text{elapsed}}$$
4. **Segment Mileage Attribution**: Segment miles attributed to checkpoint $i$ represent the corridor span from the midpoint to the previous checkpoint to the midpoint to the next checkpoint:
   $$m_i = \frac{d_{i+1} - d_{i-1}}{2}$$
   This ensures $\sum_{i} m_i \equiv d_{\text{total}}$ with 100% mathematical precision.

### 4.3 Temporal Meteorological Integration
File: [`backend/routing_app/services/weather.py`](file:///Ubuntu-22.04/home/Projects/truck-routing/backend/routing_app/services/weather.py)

Static weather snapshots are inadequate for trips exceeding 4 hours. TruckRoute extracts forecasts matching each checkpoint's specific arrival hour:
- Checkpoints are batched in groups of up to 35 coordinates per HTTP request to Open-Meteo.
- Request parameters enforce imperial units: `wind_speed_unit=mph`, `precipitation_unit=inch`, `temperature_unit=fahrenheit`.
- For each checkpoint, the service parses the hourly forecast array (`time`, `temperature_2m`, `precipitation`, `rain`, `snowfall`, `wind_speed_10m`, `wind_gusts_10m`) and extracts the record closest to $\text{ETA}_{\text{checkpoint}}$.

### 4.4 Risk Matrix & Cargo Weight Escalation Engine
File: [`backend/routing_app/services/risk_engine.py`](file:///Ubuntu-22.04/home/Projects/truck-routing/backend/routing_app/services/risk_engine.py)

#### Baseline Weather Classification

| Risk Level | Wind Speed | Rain Rate | Snowfall Rate | Internal Score |
| :--- | :--- | :--- | :--- | :--- |
| **Low** | $< 25\text{ mph}$ | $< 0.10\text{ in/hr}$ | $< 0.5\text{ in/hr}$ | 1 |
| **Moderate** | $25\text{--}34\text{ mph}$ | $0.10\text{--}0.25\text{ in/hr}$ | $0.5\text{--}1.0\text{ in/hr}$ | 2 |
| **High** | $35\text{--}44\text{ mph}$ | $0.25\text{--}0.50\text{ in/hr}$ | $1.0\text{--}2.0\text{ in/hr}$ | 3 |
| **Severe** | $45\text{--}54\text{ mph}$ | $0.50\text{--}1.00\text{ in/hr}$ | $2.0\text{--}3.0\text{ in/hr}$ | 4 |
| **No Travel** | $\ge 55\text{ mph}$ | $> 1.00\text{ in/hr}$ | $> 3.0\text{ in/hr}$ | 5 |

#### Mandatory Load Weight Escalation Logic
Wind hazards are magnified by cargo weight and center of gravity:
1. **$\text{Wind} \ge 55\text{ mph}$**: Overrides all other metrics to **No Travel** regardless of truck weight.
2. **$45\text{--}54\text{ mph Wind} + \text{Load} > 30,000\text{ lb}$**: Escalates from Severe to **No Travel** due to rollover risk on high-profile freight.
3. **$35\text{--}44\text{ mph Wind} + \text{Load} > 40,000\text{ lb}$**: Escalates from High to **Severe** due to severe crosswind steering instability.

Composite checkpoint risk is determined by:
$$\text{Risk}_{\text{checkpoint}} = \max\left(\text{Risk}_{\text{wind}}, \text{Risk}_{\text{rain}}, \text{Risk}_{\text{snow}}\right)$$

### 4.5 4-Tier Recommendation Decision Engine
File: [`backend/routing_app/services/recommendation.py`](file:///Ubuntu-22.04/home/Projects/truck-routing/backend/routing_app/services/recommendation.py)

Routes are sorted using a strict lexicographical tiebreaker key:
1. **Fewest Severe + No-Travel miles**: Minimizes dangerous crosswinds, blizzards, and flash flooding.
2. **Fewest High-risk miles**: Minimizes moderate-to-high fatigue and delays.
3. **Lowest weighted average risk score**:
   $$\bar{R} = \frac{\sum_{i} (\text{RiskScore}_i \times m_i)}{d_{\text{total}}}$$
4. **Shortest total travel duration**: Selects the fastest path when safety profiles are equivalent.

The recommendation engine attaches a humanized `recommendation_reason` explaining why the winner was chosen (e.g., *"Recommended: avoids all severe weather zones (0.0 mi severe vs 45.2 mi on Route A)"*).

### 4.6 Corridor Spatial Weather Mesh
File: [`backend/routing_app/services/corridor.py`](file:///Ubuntu-22.04/home/Projects/truck-routing/backend/routing_app/services/corridor.py)

To enable the map's 0–48 hour forecast slider, the backend creates a spatial mesh enclosing the routes with 20 miles of lateral padding. An hourly weather grid ($T+0\text{h}$ to $T+48\text{h}$) is computed, enabling the frontend slider to update heatmap layers in real time without continuous API polling.

---

## 5. Frontend Architecture & UI Mechanics

### 5.1 Component Hierarchy
```
src/
├── main.jsx                     # Application bootstrap & mount
├── App.jsx                      # State management, data fetching, error handling
├── App.css                      # Enterprise freight design system
├── index.css                    # Design tokens & CSS variables
├── components/
│   ├── Header.jsx               # Branding & safety compliance badges
│   ├── RouteForm.jsx            # Inputs, geocoding autocomplete, presets
│   ├── RouteCard.jsx            # Individual route card with stacked risk bar
│   ├── RouteComparison.jsx      # Side-by-side 3-route comparison grid
│   ├── MapView.jsx              # Leaflet map, polyline segmentation, popups
│   ├── TimelineSlider.jsx       # 0–48h scrubber with play/pause animation
│   ├── CheckpointDetails.jsx    # Turn-by-turn checkpoint audit log table
│   └── RiskLegend.jsx           # Collapsible threshold & load rules table
├── services/
│   └── api.js                   # REST API client
└── utils/
    └── formatters.js            # Risk colors, date formatting, unit helpers
```

### 5.2 Map Rendering & Color-Coded Polylines
File: [`frontend/src/components/MapView.jsx`](file:///Ubuntu-22.04/home/Projects/truck-routing/frontend/src/components/MapView.jsx)

- **Basemap**: CartoDB Positron / Voyager raster tiles with retina support.
- **Route Multi-Styling**:
  - Inactive routes are rendered with dashed, muted slate polylines (`#64748b`) with hover tooltips; clicking any inactive polyline switches focus.
  - The active route is sliced into contiguous coordinate segments, colored according to checkpoint risk:
    - Low Risk: `#10b981` (Emerald)
    - Moderate Risk: `#f59e0b` (Amber)
    - High Risk: `#f97316` (Orange)
    - Severe Hazard: `#ef4444` (Crimson Red)
    - No Travel Advised: `#7f1d1d` (Burgundy)
- **Checkpoint Markers**:
  - Interactive circle markers with popups displaying Checkpoint #, Distance from origin, Truck ETA, Wind speed/gusts, Rain rate, Snow rate, Temperature, and Load Weight Escalation alerts.

### 5.3 0–48h Forecast Timeline Scrubber & Heatmap
File: [`frontend/src/components/TimelineSlider.jsx`](file:///Ubuntu-22.04/home/Projects/truck-routing/frontend/src/components/TimelineSlider.jsx)

- **Scrubber**: Sliders range from Hour 0 (departure) to Hour 48.
- **Animation Engine**: An "Animate" button uses a 500ms interval timer to step forward through forecast hours.
- **Dynamic Heatmap**: Canvas bubbles smoothly update based on the selected metric:
  - **Composite Hazard**: Blends wind, precipitation, and snow intensity.
  - **Wind**: Highlights corridors exceeding 35, 45, and 55 mph.
  - **Rain**: Highlights rainfall rates exceeding 0.10, 0.25, 0.50, and 1.00 in/hr.
  - **Snow**: Highlights snowfall rates exceeding 0.5, 1.0, 2.0, and 3.0 in/hr.

### 5.4 Enterprise Logistics Styling
The user interface follows a modern logistics palette (similar to Samsara and Flexport):
- Neutral slate backgrounds (`#f8fafc`, `#ffffff`) with crisp card borders (`#e2e8f0`).
- High-contrast typography using the **Inter** font family.
- Color-coded badges for rapid visual risk recognition.
- Single unified theme optimized for dispatch environments.

---

## 6. Complete REST API Specification

### `POST /api/routes/analyze/`
The primary endpoint for multi-route risk calculation.

#### Request Headers
```http
Content-Type: application/json
```

#### Request Body
```json
{
  "origin": {
    "lat": 41.8781,
    "lon": -87.6298,
    "label": "Chicago, IL"
  },
  "destination": {
    "lat": 40.7128,
    "lon": -74.0060,
    "label": "New York, NY"
  },
  "departure_time": "2026-10-21T08:00:00Z",
  "load_weight": 42000,
  "sampling_interval_miles": 25
}
```

| Field | Type | Required | Default | Description |
| :--- | :--- | :--- | :--- | :--- |
| `origin` | Object | Yes | - | Must contain `lat` (float), `lon` (float), and optional `label` |
| `destination` | Object | Yes | - | Must contain `lat` (float), `lon` (float), and optional `label` |
| `departure_time` | ISO-8601 String | No | Current UTC | Scheduled departure datetime |
| `load_weight` | Float / Int | No | `35000` | Cargo weight in pounds (lbs) |
| `sampling_interval_miles` | Integer | No | `25` | Interval in miles (`10`, `25`, or `50`) |

#### Successful Response (`200 OK`)
```json
{
  "origin": { "lat": 41.8781, "lon": -87.6298, "label": "Chicago, IL" },
  "destination": { "lat": 40.7128, "lon": -74.0060, "label": "New York, NY" },
  "departure_time": "2026-10-21T08:00:00+00:00",
  "load_weight": 42000.0,
  "sampling_interval_miles": 25,
  "recommended_route_id": 0,
  "routes": [
    {
      "id": 0,
      "name": "Route A (via I-80 E)",
      "summary": "via I-80 E",
      "distance_miles": 790.4,
      "duration_seconds": 44400.0,
      "duration_formatted": "12h 20m",
      "rank": 1,
      "is_recommended": true,
      "recommendation_reason": "Safest corridor: 0 severe/high risk miles with optimal weather conditions throughout.",
      "risk_summary": {
        "low_miles": 790.4,
        "moderate_miles": 0.0,
        "high_miles": 0.0,
        "severe_miles": 0.0,
        "no_travel_miles": 0.0,
        "total_miles": 790.4,
        "average_risk_score": 1.0,
        "max_wind_mph": 14.2,
        "max_rain_in_per_hr": 0.0,
        "max_snow_in_per_hr": 0.0,
        "load_alerts": []
      },
      "checkpoints": [
        {
          "index": 0,
          "is_origin": true,
          "is_destination": false,
          "distance_from_origin_miles": 0.0,
          "segment_miles": 12.5,
          "lat": 41.8781,
          "lon": -87.6298,
          "eta_iso": "2026-10-21T08:00:00+00:00",
          "eta_formatted": "Oct 21, 08:00",
          "weather": {
            "temperature_f": 52.4,
            "wind_speed_mph": 9.3,
            "wind_gusts_mph": 12.1,
            "rain_in_per_hr": 0.0,
            "snow_in_per_hr": 0.0,
            "precip_in": 0.0,
            "weather_code": 1,
            "description": "Mainly clear"
          },
          "risk": {
            "overall_risk": "LOW",
            "risk_score": 1,
            "color": "#10b981",
            "critical_factors": [],
            "load_rule_note": null
          }
        }
      ],
      "colored_segments": [
        {
          "coordinates": [[41.8781, -87.6298], [41.7502, -87.4101]],
          "color": "#10b981",
          "risk_level": "LOW"
        }
      ]
    }
  ],
  "corridor_grid": {
    "hours": [0, 1, 2, "...", 48],
    "timestamps": ["2026-10-21T08:00:00", "..."],
    "grid": [
      {
        "lat": 41.8781,
        "lon": -87.6298,
        "hourly": [
          {
            "hour": 0,
            "wind_mph": 9.3,
            "rain_in": 0.0,
            "snow_in": 0.0,
            "temp_f": 52.4,
            "risk_intensity": 0.1
          }
        ]
      }
    ]
  }
}
```

---

### `GET /api/geocode/?q=<search_query>&limit=6`
Provides address and city autocompletion.

#### Query Parameters
- `q` (string, required): Search term (e.g. `Denver` or `Chicago, IL`).
- `limit` (integer, optional): Maximum suggestions to return (default: `6`).

#### Response Example
```json
[
  {
    "label": "Denver, Colorado, United States",
    "name": "Denver",
    "city": "Denver",
    "state": "Colorado",
    "country": "United States",
    "lat": 39.7392,
    "lon": -104.9903
  }
]
```

---

### `GET /api/health/`
Health-check endpoint for uptime monitors.

#### Response Example
```json
{
  "status": "healthy",
  "timestamp": "2026-10-21T08:00:00.000000+00:00"
}
```

---

## 7. Free Cloud Deployment Guide (Render & Vercel)

### Option A: 1-Click All-in-One Deployment on Render (Recommended)
Render provides a **100% free tier** for web services. The repository includes [`render.yaml`](file:///Ubuntu-22.04/home/Projects/truck-routing/render.yaml) preconfigured to build the frontend and serve both the SPA and REST API from a single instance:

1. Push this repository to your GitHub account.
2. Sign up or log in at [Render.com](https://render.com).
3. In the Render Dashboard, click **New > Blueprint** and select your GitHub repository.
4. Render detects `render.yaml` and sets:
   - **Environment**: Python
   - **Build Command**:
     ```bash
     cd frontend && npm install && npm run build && cd ../backend && pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
     ```
   - **Start Command**:
     ```bash
     cd backend && gunicorn truck_routing.wsgi:application --bind 0.0.0.0:$PORT
     ```
5. **Add the Stadia Maps environment variable**: In the Render service dashboard, go to **Environment** and add:
   - Key: `VITE_STADIA_API_KEY`
   - Value: your Stadia Maps API key (free at [stadiamaps.com/pricing](https://stadiamaps.com/pricing/))
6. Click **Apply**. Render builds the React application, compiles static assets with Whitenoise, and deploys the live service at `https://<your-app-name>.onrender.com`.

### Option B: Decoupled Deployment (Vercel + Render)
If you prefer zero cold-start times on the frontend:
1. **Frontend on Vercel**:
   - Import your GitHub repo on [Vercel](https://vercel.com).
   - Set **Root Directory** to `frontend`.
   - Set Environment Variables:
     - `VITE_API_URL=https://your-backend.onrender.com`
     - `VITE_STADIA_API_KEY=your_stadia_api_key_here`
2. **Backend on Render**:
   - Create a Web Service pointing to `backend/`.
   - Build command: `pip install -r requirements.txt && python manage.py migrate`.
   - Start command: `gunicorn truck_routing.wsgi:application`.

---

## 8. Automated Testing & Quality Assurance

The backend includes a unit test suite verifying calculations, risk boundaries, vehicle weight rules, and tiebreaker logic.

### Running the Test Suite
```bash
cd backend
source venv/bin/activate
pytest -v
```

### Test Suite Coverage Breakdown

```
collected 16 items

routing_app/tests/test_api.py::ApiEndpointsTestCase::test_health_check PASSED
routing_app/tests/test_api.py::ApiEndpointsTestCase::test_geocode_endpoint PASSED
routing_app/tests/test_api.py::ApiEndpointsTestCase::test_analyze_routes_endpoint_validation PASSED
routing_app/tests/test_api.py::ApiEndpointsTestCase::test_analyze_routes_endpoint_success PASSED
routing_app/tests/test_recommendation.py::TestRecommendationService::test_prefers_fewest_severe_miles PASSED
routing_app/tests/test_recommendation.py::TestRecommendationService::test_prefers_fewest_high_miles_when_severe_tied PASSED
routing_app/tests/test_recommendation.py::TestRecommendationService::test_prefers_lowest_average_risk_when_high_and_severe_tied PASSED
routing_app/tests/test_recommendation.py::TestRecommendationService::test_prefers_shortest_time_when_all_risk_tied PASSED
routing_app/tests/test_risk_engine.py::TestRiskEngine::test_wind_thresholds_standard_load PASSED
routing_app/tests/test_risk_engine.py::TestRiskEngine::test_wind_load_escalation_rules PASSED
routing_app/tests/test_risk_engine.py::TestRiskEngine::test_rain_thresholds_exact PASSED
routing_app/tests/test_risk_engine.py::TestRiskEngine::test_snow_thresholds_exact PASSED
routing_app/tests/test_risk_engine.py::TestRiskEngine::test_checkpoint_evaluation_composite PASSED
routing_app/tests/test_sampling.py::TestSamplingService::test_haversine_distance PASSED
routing_app/tests/test_sampling.py::TestSamplingService::test_sample_route_checkpoints_25_miles PASSED
routing_app/tests/test_sampling.py::TestSamplingService::test_sampling_intervals_10_and_50 PASSED

============================= 16 passed in 11.91s =============================
```

- **`test_risk_engine.py`**: Validates boundary values for wind (24.9 vs 25.0, 34.9 vs 35.0, 44.9 vs 45.0, 54.9 vs 55.0), rain (0.09 vs 0.10, 0.24 vs 0.25, 0.49 vs 0.50, 0.99 vs 1.01), snow (0.49 vs 0.50, 0.99 vs 1.00, 1.99 vs 2.00, 3.00 vs 3.01), and tests weight escalations ($>30\text{k lb}$ and $>40\text{k lb}$).
- **`test_recommendation.py`**: Validates the 4-tier tiebreaker order (Severe miles $\rightarrow$ High miles $\rightarrow$ Average risk $\rightarrow$ Duration).
- **`test_sampling.py`**: Validates Haversine accuracy, polyline interpolation, and segment mileage summation.
- **`test_api.py`**: Tests endpoint availability, 400 validation error handling, and end-to-end integration.

---

## 9. Operational Considerations & Troubleshooting

### Third-Party Service Resilience
- **OSRM Fallback**: If the public OSRM server experiences rate limiting, `router.py` automatically generates synthetic quadratic Bézier highway corridors between origin and destination to prevent application downtime.
- **Open-Meteo Fallback**: If Open-Meteo experiences network timeouts, `weather.py` falls back to baseline climatological estimates, ensuring the analysis pipeline never crashes.
- **Geocoding Failover**: `geocoding.py` first queries Komoot Photon; if unresponsive, it fails over to OSM Nominatim.

### Common Troubleshooting Scenarios

1. **`ModuleNotFoundError: No module named 'truck_routing'`**:
   Ensure you activate the virtual environment and execute management commands from within the `backend/` directory:
   ```bash
   cd backend
   source venv/bin/activate
   python manage.py check
   ```

2. **CORS issues during local development**:
   When developing locally, ensure the Vite development server runs on port 5173 with proxying enabled, or verify that `CORS_ALLOW_ALL_ORIGINS = True` is active in `backend/truck_routing/settings.py`.

3. **Port 8000 already in use**:
   Run on an alternate port:
   ```bash
   python manage.py runserver 0.0.0.0:8001
   ```

4. **Map shows "Access Blocked" or tiles fail to load**:
   The app uses [Stadia Maps](https://stadiamaps.com/) for OSM-based tiles. Ensure you have set the `VITE_STADIA_API_KEY` environment variable:
   - **Local dev**: Add `VITE_STADIA_API_KEY=your_key` to `frontend/.env`, then rebuild (`npm run build`) or restart the Vite dev server.
   - **Render/Vercel**: Add `VITE_STADIA_API_KEY` as an environment variable in the platform dashboard and trigger a redeploy.
   - Get a free key at [stadiamaps.com/pricing](https://stadiamaps.com/pricing/) (200k tile requests/day).

---

## 10. Walkthrough Script (5–10 min)

When recording your demonstration (e.g. for Loom), use this structured narrative:

1. **Introduction (1 min)**:
   - Introduce TruckRoute: *"TruckRoute is a weather-aware routing decision platform designed for commercial freight dispatchers and truck drivers."*
   - State the core problem: Standard GPS routes drivers into high-crosswind rollovers or blizzard closures because they ignore departure times and vehicle cargo weight.
2. **Preset & Parameter Configuration (1.5 min)**:
   - Select the **Chicago $\rightarrow$ New York** or **Denver $\rightarrow$ Salt Lake City** corridor.
   - Explain the departure time picker: weather is forecasted for the exact arrival time at each checkpoint.
   - Set the cargo weight to **42,000 lbs** to demonstrate the $>40,000\text{ lb}$ crosswind escalation rule.
   - Select sampling resolution: **Every 25 mi**.
   - Click **Analyze Routes & Evaluate Risk**.
3. **Route Comparison & Recommendation Rationale (2 min)**:
   - Point out that **3 distinct routes** were generated.
   - Review the **Recommended Badge** on the winning route and explain the 4-tier decision hierarchy:
     1. Fewest Severe miles
     2. Fewest High miles
     3. Lowest average risk
     4. Shortest travel time
   - Point out the stacked risk bar showing the exact breakdown of Low, Moderate, High, Severe, and No-Travel miles.
   - Highlight the **Load Rule Escalation Alert** callout if wind exceeded 35 mph with $>40\text{k lb}$ load.
4. **Interactive Map & Weather Heatmap (2.5 min)**:
   - Show how the route is styled with **color-coded risk segments** (Green, Amber, Orange, Red, Burgundy).
   - Click several checkpoint pins along the route to inspect the popup card: show ETA, wind gusts, rain rate, and snow rate.
   - Demonstrate the **0–48 hour forecast timeline slider**: click **Animate** and watch the weather heatmap evolve across the trip corridor.
   - Switch heatmap layers between **Composite Hazard**, **Wind**, **Rain**, and **Snow**.
5. **Code Quality & Testing (1.5 min)**:
   - Open a terminal and run `pytest -v` in `backend/` showing all 16 tests passing.
   - Mention clean separation of concerns: `risk_engine.py`, `sampling.py`, `router.py`, and `recommendation.py`.
