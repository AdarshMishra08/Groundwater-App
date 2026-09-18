import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import requests
import streamlit as st

try:
    API_BASE = st.secrets.get("API_BASE", "http://localhost:8000")
except Exception:
    API_BASE = "http://localhost:8000"

st.set_page_config(page_title="Groundwater Level Monitor", layout="wide")
st.title("Groundwater Level Monitoring Dashboard")
st.caption("6-hourly telemetry · spatial interpolation · short-term forecasting")


@st.cache_data(ttl=300)
def get_stations():
    r = requests.get(f"{API_BASE}/stations/")
    r.raise_for_status()
    return pd.DataFrame(r.json())


@st.cache_data(ttl=300)
def get_readings(station_id, limit=1000):
    r = requests.get(f"{API_BASE}/readings/{station_id}", params={"limit": limit})
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    if not df.empty:
        df["timestamp"] = pd.to_datetime(df["timestamp"])
    return df


try:
    stations_df = get_stations()
except requests.exceptions.ConnectionError:
    st.error(f"Can't reach the API at {API_BASE}. Start the backend with `uvicorn main:app --reload`.")
    st.stop()

tab_overview, tab_station, tab_map, tab_forecast = st.tabs(
    ["Overview", "Station Trend", "Spatial Interpolation", "Forecast"]
)

with tab_overview:
    st.subheader("Monitoring Stations")
    if stations_df.empty:
        st.warning("No stations found. Run `python seed_demo_data.py` in the backend folder, "
                    "or add stations via POST /stations/.")
    else:
        st.dataframe(stations_df, use_container_width=True)
        st.map(stations_df.rename(columns={"latitude": "lat", "longitude": "lon"})[["lat", "lon"]])

with tab_station:
    st.subheader("Station-level Time Series")
    if stations_df.empty:
        st.info("No stations available yet.")
    else:
        label_map = {row["name"]: row["id"] for _, row in stations_df.iterrows()}
        chosen = st.selectbox("Select station", list(label_map.keys()))
        station_id = label_map[chosen]
        readings_df = get_readings(station_id)

        if readings_df.empty:
            st.info("No readings for this station yet.")
        else:
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.plot(readings_df["timestamp"], readings_df["depth_m"], color="steelblue", linewidth=1.2)
            ax.invert_yaxis()  # deeper water level reads as "lower" on the chart, matching intuition
            ax.set_xlabel("Time")
            ax.set_ylabel("Depth to water level (m)")
            ax.set_title(f"{chosen} — Depth to Water Level")
            ax.grid(alpha=0.3)
            st.pyplot(fig)

            col1, col2, col3 = st.columns(3)
            col1.metric("Latest depth (m)", f"{readings_df['depth_m'].iloc[-1]:.2f}")
            col2.metric("Period mean (m)", f"{readings_df['depth_m'].mean():.2f}")
            col3.metric("Readings", len(readings_df))

with tab_map:
    st.subheader("Spatial Interpolation (IDW)")
    resolution = st.slider("Grid resolution (degrees)", 0.02, 0.2, 0.05, step=0.01)
    if st.button("Run interpolation"):
        payload = {"timestamp": pd.Timestamp.utcnow().isoformat(), "grid_resolution": resolution}
        r = requests.post(f"{API_BASE}/interpolate/", json=payload)
        if r.status_code != 200:
            st.error(r.json().get("detail", "Interpolation failed"))
        else:
            data = r.json()
            grid_lon = np.array(data["grid_lon"])
            grid_lat = np.array(data["grid_lat"])
            grid_depth = np.array(data["grid_depth_m"])
            points = data["station_points"]

            fig, ax = plt.subplots(figsize=(8, 7))
            c = ax.contourf(grid_lon, grid_lat, grid_depth, levels=20, cmap="viridis_r")
            plt.colorbar(c, ax=ax, label="Depth to water level (m)")
            px = [p["lon"] for p in points]
            py = [p["lat"] for p in points]
            ax.scatter(px, py, c="red", edgecolor="white", s=60, zorder=5, label="Stations")
            for p in points:
                ax.annotate(p["station_code"], (p["lon"], p["lat"]), fontsize=7,
                             xytext=(3, 3), textcoords="offset points")
            ax.set_xlabel("Longitude")
            ax.set_ylabel("Latitude")
            ax.legend()
            st.pyplot(fig)

with tab_forecast:
    st.subheader("Short-term Forecast")
    if stations_df.empty:
        st.info("No stations available yet.")
    else:
        label_map = {row["name"]: row["id"] for _, row in stations_df.iterrows()}
        chosen = st.selectbox("Select station for forecast", list(label_map.keys()), key="forecast_station")
        station_id = label_map[chosen]
        horizon = st.slider("Forecast horizon (days)", 1, 30, 7)

        if st.button("Generate forecast"):
            r = requests.post(f"{API_BASE}/predict/", json={"station_id": station_id, "horizon_days": horizon})
            if r.status_code != 200:
                st.error(r.json().get("detail", "Forecast failed"))
            else:
                forecast_df = pd.DataFrame(r.json())
                forecast_df["timestamp"] = pd.to_datetime(forecast_df["timestamp"])
                history_df = get_readings(station_id)

                fig, ax = plt.subplots(figsize=(10, 4))
                if not history_df.empty:
                    ax.plot(history_df["timestamp"], history_df["depth_m"], label="Observed", color="steelblue")
                ax.plot(forecast_df["timestamp"], forecast_df["predicted_depth_m"],
                         label="Forecast", color="darkorange")
                ax.fill_between(forecast_df["timestamp"], forecast_df["lower_95"], forecast_df["upper_95"],
                                 color="darkorange", alpha=0.2, label="95% interval")
                ax.invert_yaxis()
                ax.legend()
                ax.set_ylabel("Depth to water level (m)")
                ax.grid(alpha=0.3)
                st.pyplot(fig)
                st.dataframe(forecast_df, use_container_width=True)
