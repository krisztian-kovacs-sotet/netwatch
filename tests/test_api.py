from fastapi.testclient import TestClient

from netwatch.scanner import DiscoveredDevice
from tests.conftest import FakeScanner

LAPTOP = DiscoveredDevice(mac="3c:22:fb:aa:bb:cc", ip="192.168.1.23")
PHONE = DiscoveredDevice(mac="f0:99:b6:11:22:33", ip="192.168.1.40")


def test_health(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_scan_records_devices_and_alerts(client: TestClient, scanner: FakeScanner) -> None:
    scanner.devices = [LAPTOP, PHONE]

    assert client.post("/scans").json() == {"devices_seen": 2, "new_alerts": 2}
    assert {d["mac"] for d in client.get("/devices").json()} == {LAPTOP.mac, PHONE.mac}
    assert {a["kind"] for a in client.get("/alerts").json()} == {"new_device"}

    # A repeat scan with nothing new produces no alerts.
    assert client.post("/scans").json() == {"devices_seen": 2, "new_alerts": 0}


def test_mark_device_trusted_and_filter(client: TestClient, scanner: FakeScanner) -> None:
    scanner.devices = [LAPTOP, PHONE]
    client.post("/scans")
    laptop_id = next(d["id"] for d in client.get("/devices").json() if d["mac"] == LAPTOP.mac)

    response = client.patch(f"/devices/{laptop_id}", json={"trusted": True, "label": "My laptop"})

    assert response.status_code == 200
    assert response.json()["label"] == "My laptop"
    assert [d["mac"] for d in client.get("/devices", params={"trusted": True}).json()] == [
        LAPTOP.mac
    ]
    assert [d["mac"] for d in client.get("/devices", params={"trusted": False}).json()] == [
        PHONE.mac
    ]


def test_acknowledge_alert(client: TestClient, scanner: FakeScanner) -> None:
    scanner.devices = [LAPTOP]
    client.post("/scans")
    alert_id = client.get("/alerts").json()[0]["id"]

    assert client.post(f"/alerts/{alert_id}/acknowledge").json()["acknowledged"] is True
    assert client.get("/alerts", params={"unacknowledged_only": True}).json() == []


def test_stats_summarises_devices_and_alerts(client: TestClient, scanner: FakeScanner) -> None:
    assert client.get("/stats").json() == {
        "devices": 0,
        "trusted_devices": 0,
        "untrusted_devices": 0,
        "unacknowledged_alerts": 0,
    }

    scanner.devices = [LAPTOP, PHONE]
    client.post("/scans")
    devices = client.get("/devices").json()
    client.patch(f"/devices/{devices[0]['id']}", json={"trusted": True})
    client.post(f"/alerts/{client.get('/alerts').json()[0]['id']}/acknowledge")

    assert client.get("/stats").json() == {
        "devices": 2,
        "trusted_devices": 1,
        "untrusted_devices": 1,
        "unacknowledged_alerts": 1,
    }


def test_missing_resources_return_404(client: TestClient) -> None:
    assert client.get("/devices/999").status_code == 404
    assert client.patch("/devices/999", json={"trusted": True}).status_code == 404
    assert client.post("/alerts/999/acknowledge").status_code == 404
