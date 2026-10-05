from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class DiscoveredDevice:
    mac: str  # normalised: lowercase, colon-separated, zero-padded
    ip: str


class Scanner(Protocol):
    """Anything that can report which devices are currently on the network."""

    async def scan(self) -> list[DiscoveredDevice]: ...
