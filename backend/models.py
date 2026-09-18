from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from database import Base


class Station(Base):
    __tablename__ = "stations"

    id = Column(Integer, primary_key=True, index=True)
    station_code = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    state = Column(String)
    district = Column(String)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    aquifer_type = Column(String, nullable=True)

    readings = relationship("TelemetryReading", back_populates="station", cascade="all, delete-orphan")


class TelemetryReading(Base):
    __tablename__ = "telemetry_readings"

    id = Column(Integer, primary_key=True, index=True)
    station_id = Column(Integer, ForeignKey("stations.id"), nullable=False, index=True)
    timestamp = Column(DateTime, nullable=False, index=True)
    depth_m = Column(Float, nullable=False)  # depth to water level below ground surface, in meters
    battery_voltage = Column(Float, nullable=True)
    quality_flag = Column(String, default="OK")

    station = relationship("Station", back_populates="readings")
