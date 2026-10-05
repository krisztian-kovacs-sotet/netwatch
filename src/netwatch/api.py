from collections.abc import Iterator
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.orm import Session

from netwatch.inventory import run_scan
from netwatch.models import Alert, Device
from netwatch.schemas import AlertOut, DeviceOut, DeviceUpdate, ScanResult

router = APIRouter()


def get_session(request: Request) -> Iterator[Session]:
    with request.app.state.session_factory() as session:
        yield session


SessionDep = Annotated[Session, Depends(get_session)]


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/devices", response_model=list[DeviceOut])
def list_devices(session: SessionDep, trusted: bool | None = None) -> list[Device]:
    query = select(Device).order_by(Device.last_seen.desc())
    if trusted is not None:
        query = query.where(Device.trusted == trusted)
    return list(session.scalars(query))


@router.get("/devices/{device_id}", response_model=DeviceOut)
def get_device(device_id: int, session: SessionDep) -> Device:
    device = session.get(Device, device_id)
    if device is None:
        raise HTTPException(status_code=404, detail="Device not found")
    return device


@router.patch("/devices/{device_id}", response_model=DeviceOut)
def update_device(device_id: int, update: DeviceUpdate, session: SessionDep) -> Device:
    device = get_device(device_id, session)
    for field, value in update.model_dump(exclude_unset=True).items():
        setattr(device, field, value)
    session.commit()
    return device


@router.get("/alerts", response_model=list[AlertOut])
def list_alerts(session: SessionDep, unacknowledged_only: bool = False) -> list[Alert]:
    query = select(Alert).order_by(Alert.created_at.desc(), Alert.id.desc())
    if unacknowledged_only:
        query = query.where(Alert.acknowledged.is_(False))
    return list(session.scalars(query))


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertOut)
def acknowledge_alert(alert_id: int, session: SessionDep) -> Alert:
    alert = session.get(Alert, alert_id)
    if alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    alert.acknowledged = True
    session.commit()
    return alert


@router.post("/scans", response_model=ScanResult)
async def trigger_scan(request: Request) -> ScanResult:
    return await run_scan(request.app.state.scanner, request.app.state.session_factory)
