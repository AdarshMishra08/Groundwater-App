from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class StationBase(BaseModel):
    station_code: str
    name: str
    state: Optional[str] = None
    district: Optional[str] = None
    latitude: float
    longitude: float
    aquifer_type: Optional[str] = None


class StationCreate(StationBase):
    pass


class StationOut(StationBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class ReadingBase(BaseModel):
    station_id: int
    timestamp: datetime
    depth_m: float
    battery_voltage: Optional[float] = None
    quality_flag: Optional[str] = "OK"


class ReadingCreate(ReadingBase):
    pass


class ReadingOut(ReadingBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


class InterpolationRequest(BaseModel):
    timestamp: datetime
    grid_resolution: float = 0.05  # degrees
    method: str = "idw"


class PredictionRequest(BaseModel):
    station_id: int
    horizon_days: int = 7
