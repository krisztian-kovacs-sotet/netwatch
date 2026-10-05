from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker

from netwatch import models  # noqa: F401  (registers tables on Base)
from netwatch.config import Settings
from netwatch.db import Base, make_engine
from netwatch.main import create_app
from netwatch.scanner import DiscoveredDevice


class FakeScanner:
    """Returns whatever devices the test puts in `.devices`."""

    def __init__(self) -> None:
        self.devices: list[DiscoveredDevice] = []

    async def scan(self) -> list[DiscoveredDevice]:
        return list(self.devices)


@pytest.fixture
def scanner() -> FakeScanner:
    return FakeScanner()


@pytest.fixture
def client(scanner: FakeScanner) -> Iterator[TestClient]:
    settings = Settings(database_url="sqlite:///:memory:", scan_interval_seconds=0)
    with TestClient(create_app(settings, scanner=scanner)) as test_client:
        yield test_client


@pytest.fixture
def session() -> Iterator[Session]:
    engine = make_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with sessionmaker(engine)() as db_session:
        yield db_session
    engine.dispose()
