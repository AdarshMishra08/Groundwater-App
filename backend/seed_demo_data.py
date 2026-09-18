"""Run once to populate the database with demo stations + 90 days of synthetic telemetry.

    python seed_demo_data.py
"""
from datetime import datetime, timedelta

import models
from database import Base, SessionLocal, engine
from ingest import generate_synthetic_readings

Base.metadata.create_all(bind=engine)

DEMO_STATIONS = [
    {"station_code": "AS-KAM-001", "name": "Kamrup Metro-1", "state": "Assam",
     "district": "Kamrup Metropolitan", "latitude": 26.15, "longitude": 91.77, "aquifer_type": "Alluvial"},
    {"station_code": "AS-JOR-002", "name": "Jorhat-2", "state": "Assam",
     "district": "Jorhat", "latitude": 26.75, "longitude": 94.22, "aquifer_type": "Alluvial"},
    {"station_code": "AS-DIB-003", "name": "Dibrugarh-3", "state": "Assam",
     "district": "Dibrugarh", "latitude": 27.48, "longitude": 94.91, "aquifer_type": "Alluvial"},
    {"station_code": "AS-SIL-004", "name": "Silchar-4", "state": "Assam",
     "district": "Cachar", "latitude": 24.83, "longitude": 92.78, "aquifer_type": "Alluvial"},
    {"station_code": "AS-NGN-005", "name": "Nagaon-5", "state": "Assam",
     "district": "Nagaon", "latitude": 26.35, "longitude": 92.68, "aquifer_type": "Alluvial"},
]


def run():
    db = SessionLocal()
    station_objs = []
    for s in DEMO_STATIONS:
        existing = db.query(models.Station).filter_by(station_code=s["station_code"]).first()
        if not existing:
            existing = models.Station(**s)
            db.add(existing)
            db.commit()
            db.refresh(existing)
        station_objs.append(existing)

    end = datetime.utcnow()
    start = end - timedelta(days=90)
    codes = [s.station_code for s in station_objs]
    df = generate_synthetic_readings(codes, start, end, freq_hours=6)

    code_to_id = {s.station_code: s.id for s in station_objs}
    for _, row in df.iterrows():
        db.add(models.TelemetryReading(
            station_id=code_to_id[row["station_code"]],
            timestamp=row["timestamp"],
            depth_m=row["depth_m"],
        ))
    db.commit()
    db.close()
    print(f"Seeded {len(station_objs)} stations and {len(df)} readings.")


if __name__ == "__main__":
    run()
