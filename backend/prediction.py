"""
Short-term forecasting of water table depth at a single station.

Uses a linear trend + annual-cycle (Fourier) regression, which is a
reasonable, dependency-light baseline for 6-hourly telemetry. For
longer histories or where seasonality is more complex, this is a
natural place to swap in statsmodels SARIMAX or Prophet -- keep the
same (df -> forecast_df) interface so the FastAPI route doesn't change.
"""

import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression


def forecast_depth(df: pd.DataFrame, horizon_days: int = 7, freq_hours: int = 6) -> pd.DataFrame:
    """
    df: DataFrame with columns ['timestamp', 'depth_m'], any order.
    Returns a DataFrame with ['timestamp', 'predicted_depth_m', 'lower_95', 'upper_95']
    for `horizon_days` ahead, sampled every `freq_hours`.
    """
    df = df.sort_values("timestamp").copy()
    if len(df) < 10:
        raise ValueError("Not enough history to forecast (need at least 10 readings).")

    t0 = df["timestamp"].min()
    df["t_hours"] = (df["timestamp"] - t0).dt.total_seconds() / 3600.0

    doy = df["timestamp"].dt.dayofyear
    df["sin_annual"] = np.sin(2 * np.pi * doy / 365.25)
    df["cos_annual"] = np.cos(2 * np.pi * doy / 365.25)

    X = df[["t_hours", "sin_annual", "cos_annual"]].values
    y = df["depth_m"].values

    model = LinearRegression()
    model.fit(X, y)

    last_t = df["t_hours"].max()
    n_steps = int((horizon_days * 24) / freq_hours)
    future_hours = last_t + np.arange(1, n_steps + 1) * freq_hours
    future_timestamps = t0 + pd.to_timedelta(future_hours, unit="h")
    future_doy = future_timestamps.dayofyear

    future_X = np.column_stack([
        future_hours,
        np.sin(2 * np.pi * future_doy / 365.25),
        np.cos(2 * np.pi * future_doy / 365.25),
    ])
    preds = model.predict(future_X)

    residuals = y - model.predict(X)
    resid_std = residuals.std()

    return pd.DataFrame({
        "timestamp": future_timestamps,
        "predicted_depth_m": preds,
        "lower_95": preds - 1.96 * resid_std,
        "upper_95": preds + 1.96 * resid_std,
    })
