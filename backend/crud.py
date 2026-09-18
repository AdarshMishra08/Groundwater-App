from sqlalchemy import desc
from sqlalchemy.orm import Session

import models
import schemas


def get_stations(db: Session):
    return db.query(models.Station).all()


def get_station(db: Session, station_id: int):
    return db.query(models.Station).filter(models.Station.id == station_id).first()


def create_station(db: Session, station: schemas.StationCreate):
    db_station = models.Station(**station.model_dump())
    db.add(db_station)
    db.commit()
    db.refresh(db_station)
    return db_station


def create_reading(db: Session, reading: schemas.ReadingCreate):
    db_reading = models.TelemetryReading(**reading.model_dump())
    db.add(db_reading)
    db.commit()
    db.refresh(db_reading)
    return db_reading


def get_latest_readings(db: Session):
    """Returns one (station, most_recent_reading) pair per station that has data."""
    stations = db.query(models.Station).all()
    result = []
    for s in stations:
        latest = (
            db.query(models.TelemetryReading)
            .filter(models.TelemetryReading.station_id == s.id)
            .order_by(desc(models.TelemetryReading.timestamp))
            .first()
        )
        if latest:
            result.append((s, latest))
    return result


def get_readings_for_station(db: Session, station_id: int, limit: int = 500):
    return (
        db.query(models.TelemetryReading)
        .filter(models.TelemetryReading.station_id == station_id)
        .order_by(models.TelemetryReading.timestamp)
        .limit(limit)
        .all()
    )
