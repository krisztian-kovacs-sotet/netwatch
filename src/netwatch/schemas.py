from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DeviceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    mac: str
    ip: str
    label: str | None
    trusted: bool
    first_seen: datetime
    last_seen: datetime


class DeviceUpdate(BaseModel):
    label: str | None = None
    trusted: bool | None = None


class AlertOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    device_id: int
    kind: str
    message: str
    created_at: datetime
    acknowledged: bool


class ScanResult(BaseModel):
    devices_seen: int
    new_alerts: int
