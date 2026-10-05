from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from netwatch.inventory import record_scan
from netwatch.models import AlertKind, Device
from netwatch.scanner import DiscoveredDevice

ROUTER = DiscoveredDevice(mac="a4:2b:b0:12:34:56", ip="192.168.1.1")
T0 = datetime(2026, 1, 1, tzinfo=UTC)


def test_first_sighting_creates_device_and_new_device_alert(session: Session) -> None:
    alerts = record_scan(session, [ROUTER], now=T0)

    device = session.scalars(select(Device)).one()
    assert (device.mac, device.ip, device.trusted) == (ROUTER.mac, ROUTER.ip, False)
    assert [a.kind for a in alerts] == [AlertKind.NEW_DEVICE]
    assert alerts[0].device_id == device.id


def test_known_device_only_updates_last_seen(session: Session) -> None:
    record_scan(session, [ROUTER], now=T0)
    later = T0 + timedelta(minutes=5)

    alerts = record_scan(session, [ROUTER], now=later)

    device = session.scalars(select(Device)).one()
    assert alerts == []
    assert device.first_seen.replace(tzinfo=UTC) == T0
    assert device.last_seen.replace(tzinfo=UTC) == later


def test_ip_change_raises_alert_and_updates_ip(session: Session) -> None:
    record_scan(session, [ROUTER], now=T0)
    moved = DiscoveredDevice(mac=ROUTER.mac, ip="192.168.1.2")

    alerts = record_scan(session, [moved], now=T0 + timedelta(minutes=5))

    assert [a.kind for a in alerts] == [AlertKind.IP_CHANGED]
    assert session.scalars(select(Device)).one().ip == "192.168.1.2"
