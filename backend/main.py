from typing import List

import numpy as np
import pandas as pd
from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy.orm import Session

import crud
import models
import schemas
from database import Base, engine, get_db
from interpolation import build_grid, idw_interpolate
from prediction import forecast_depth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="Groundwater Telemetry API", version="1.0.0")


@app.get("/")
def root():
    return {"status": "ok", "service": "groundwater-telemetry-api"}


@app.post("/stations/", response_model=schemas.StationOut)
def create_station(station: schemas.StationCreate, db: Session = Depends(get_db)):
    existing = db.query(models.Station).filter(models.Station.station_code == station.station_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Station code already exists")
    return crud.create_station(db, station)


@app.get("/stations/", response_model=List[schemas.StationOut])
def list_stations(db: Session = Depends(get_db)):
    return crud.get_stations(db)


@app.post("/readings/", response_model=schemas.ReadingOut)
def add_reading(reading: schemas.ReadingCreate, db: Session = Depends(get_db)):
    if not crud.get_station(db, reading.station_id):
        raise HTTPException(status_code=404, detail="Station not found")
    return crud.create_reading(db, reading)


@app.get("/readings/{station_id}", response_model=List[schemas.ReadingOut])
def get_station_readings(station_id: int, limit: int = 500, db: Session = Depends(get_db)):
    return crud.get_readings_for_station(db, station_id, limit)


@app.post("/interpolate/")
def interpolate(req: schemas.InterpolationRequest, db: Session = Depends(get_db)):
    latest = crud.get_latest_readings(db)
    if len(latest) < 3:
        raise HTTPException(status_code=400, detail="Need at least 3 stations with readings to interpolate")

    points = np.array([[s.longitude, s.latitude] for s, r in latest])
    values = np.array([r.depth_m for s, r in latest])

    grid_x, grid_y = build_grid(points, resolution=req.grid_resolution)
    grid_z = idw_interpolate(points, values, grid_x, grid_y)

    return {
        "grid_lon": grid_x.tolist(),
        "grid_lat": grid_y.tolist(),
        "grid_depth_m": grid_z.tolist(),
        "station_points": [
            {"station_code": s.station_code, "lon": s.longitude, "lat": s.latitude, "depth_m": r.depth_m}
            for s, r in latest
        ],
    }


@app.post("/predict/")
def predict(req: schemas.PredictionRequest, db: Session = Depends(get_db)):
    readings = crud.get_readings_for_station(db, req.station_id, limit=2000)
    if len(readings) < 10:
        raise HTTPException(status_code=400, detail="Not enough history for this station to forecast")

    df = pd.DataFrame([{"timestamp": r.timestamp, "depth_m": r.depth_m} for r in readings])
    try:
        forecast_df = forecast_depth(df, horizon_days=req.horizon_days)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return forecast_df.to_dict(orient="records")
