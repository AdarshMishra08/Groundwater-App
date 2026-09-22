# Groundwater Telemetry Monitoring App

FastAPI backend + SQL database + Streamlit frontend for ingesting 6-hourly
groundwater depth telemetry, interpolating it spatially, and forecasting
short-term trends.

## Structure

```
groundwater_app/
  backend/
    database.py        # SQLAlchemy engine/session (SQLite by default)
    models.py           # ORM models: Station, TelemetryReading
    schemas.py           # Pydantic request/response models
    crud.py               # DB query helpers
    ingest.py              # CSV import + synthetic data generator
    interpolation.py        # IDW spatial interpolation
    prediction.py             # Trend + seasonal forecasting
    main.py                    # FastAPI app and routes
    seed_demo_data.py           # Populates demo stations + synthetic data
  frontend/
    app.py                      # Streamlit dashboard
  requirements.txt
```

## Setup

```bash
python -m venv venv
source venv/bin/activate       # venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Run

**1. Start the backend** (from `backend/`):
OR
Double Click .bat file for backend

```bash
cd backend
uvicorn main:app --reload --port 8000
```

This creates `groundwater.db` (SQLite) on first run. Interactive API docs
are at `http://localhost:8000/docs`.

**2. Seed demo data** (optional, gives the dashboard something to show):

```bash
python seed_demo_data.py
```

**3. Start the frontend** (from `frontend/`, in a separate terminal):

```bash
cd frontend
streamlit run app.py
```

By default the frontend calls the API at `http://localhost:8000`. Override
with a `.streamlit/secrets.toml`:

```toml
API_BASE = "https://your-deployed-api.example.com"
```

## Swapping in real CGWB / NWDP data

Neither the CGWB dashboard (cgwb.gov.in) nor the NWDP portal
(nwdp.nwic.gov.in) expose a stable public REST API for bulk pulls at the
time of writing — both are primarily interactive dashboards with CSV/report
exports. `backend/ingest.py` is written so you can:

- Export a CSV manually (or scrape it yourself) and load it with
  `ingest_from_csv()`, then POST each row to `/readings/`.
- Or write your own `fetch_live_readings()` following the same
  `(station_code, timestamp, depth_m)` shape — everything downstream
  (DB, interpolation, forecasting, dashboard) stays unchanged.

## Swapping SQLite for Postgres/MySQL

Set the `DATABASE_URL` env var before starting the backend, e.g.:

```bash
export DATABASE_URL="postgresql://user:pass@host:5432/groundwater"
```

## Notes on the modeling choices

- **Interpolation**: IDW (Inverse Distance Weighting) — simple, no extra
  dependencies, works well with sparse station networks. For larger
  networks or where spatial correlation structure matters, swap in
  kriging via `pykrige` — same `(points, values, grid) -> grid` interface.
- **Forecasting**: linear trend + annual Fourier terms via
  scikit-learn — a light baseline. For longer histories or more complex
  seasonality, swap in `statsmodels` SARIMAX or Prophet in
  `prediction.py`, keeping the same `(df) -> forecast_df` interface.
