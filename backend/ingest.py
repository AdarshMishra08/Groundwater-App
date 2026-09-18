"""
Ingestion module.

The CGWB / National Water Informatics Centre portals (cgwb.gov.in,
nwdp.nwic.gov.in) are primarily interactive dashboards with CSV/report
exports rather than a documented public REST API for bulk programmatic
pulls. Two integration paths are supported here:

1. `ingest_from_csv()` -- for CSVs exported manually (or via your own
   scraper) from the NWDP portal or CGWB dashboard.
2. `generate_synthetic_readings()` -- for local development/testing
   without network access, so the rest of the pipeline (DB, API,
   interpolation, forecasting, Streamlit UI) can be built and demoed
   end-to-end before a live feed is wired up.

If you get access to an actual ingestion endpoint or build a scraper,
add a `fetch_live_readings()` here that returns a DataFrame with the
same three columns (station_code, timestamp, depth_m) and everything
downstream keeps working unchanged.
"""

from datetime import datetime

import numpy as np
import pandas as pd


def ingest_from_csv(
    filepath: str,
    station_code_col: str = "station_code",
    timestamp_col: str = "timestamp",
    depth_col: str = "depth_m",
) -> pd.DataFrame:
    df = pd.read_csv(filepath, parse_dates=[timestamp_col])
    df = df.rename(columns={
        station_code_col: "station_code",
        timestamp_col: "timestamp",
        depth_col: "depth_m",
    })
    return df[["station_code", "timestamp", "depth_m"]].dropna()


def generate_synthetic_readings(
    station_codes,
    start: datetime,
    end: datetime,
    freq_hours: int = 6,
    base_depth: float = 8.0,
    seed: int = 42,
) -> pd.DataFrame:
    """Generates plausible 6-hourly depth-to-water-level series for testing."""
    rng = np.random.default_rng(seed)
    timestamps = pd.date_range(start, end, freq=f"{freq_hours}h")

    rows = []
    for code in station_codes:
        station_base = base_depth + rng.uniform(-3, 3)
        trend = np.linspace(0, rng.uniform(-1, 1), len(timestamps))
        seasonal = 0.8 * np.sin(2 * np.pi * timestamps.dayofyear.values / 365.25)
        noise = rng.normal(0, 0.15, len(timestamps))
        depth = station_base + trend + seasonal + noise
        for ts, d in zip(timestamps, depth):
            rows.append({"station_code": code, "timestamp": ts, "depth_m": round(float(d), 3)})

    return pd.DataFrame(rows)
