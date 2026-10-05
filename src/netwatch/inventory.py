"""Reconciles scan results with the stored device inventory and raises alerts."""

import asyncio
import logging
from collections.abc import Sequence
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session, sessionmaker

from netwatch.models import Alert, AlertKind, Device
from netwatch.scanner import DiscoveredDevice, Scanner
from netwatch.schemas import ScanResult

log = logging.getLogger(__name__)


def record_scan(
    session: Session, discovered: Sequence[DiscoveredDevice], now: datetime | None = None
) -> list[Alert]:
    """Upsert discovered devices and return the alerts this scan produced (already added)."""
    now = now or datetime.now(UTC)
    alerts: list[Alert] = []

    for found in discovered:
        device = session.scalar(select(Device).where(Device.mac == found.mac))
        if device is None:
            device = Device(mac=found.mac, ip=found.ip, first_seen=now, last_seen=now)
            session.add(device)
            session.flush()  # assigns device.id
            alerts.append(
                Alert(
                    device_id=device.id,
                    kind=AlertKind.NEW_DEVICE,
                    message=f"New device {found.mac} appeared at {found.ip}",
                    created_at=now,
                )
            )
            continue

        if device.ip != found.ip:
            alerts.append(
                Alert(
                    device_id=device.id,
                    kind=AlertKind.IP_CHANGED,
                    message=f"Device {found.mac} moved from {device.ip} to {found.ip}",
                    created_at=now,
                )
            )
            device.ip = found.ip
        device.last_seen = now

    session.add_all(alerts)
    return alerts


async def run_scan(scanner: Scanner, session_factory: sessionmaker[Session]) -> ScanResult:
    discovered = await scanner.scan()
    with session_factory() as session:
        alerts = record_scan(session, discovered)
        session.commit()
    for alert in alerts:
        log.warning("ALERT %s: %s", alert.kind, alert.message)
    return ScanResult(devices_seen=len(discovered), new_alerts=len(alerts))


async def scan_forever(
    scanner: Scanner, session_factory: sessionmaker[Session], interval_seconds: int
) -> None:
    while True:
        try:
            result = await run_scan(scanner, session_factory)
            log.info("Scan complete: %s", result)
        except Exception:
            log.exception("Scan failed")
        await asyncio.sleep(interval_seconds)
