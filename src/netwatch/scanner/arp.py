"""Passive discovery from the operating system's ARP cache.

Reading the ARP table sends no packets, so it is safe to run on any network you are on.
Active scanning (ping sweeps, port scans) should only ever target networks you own.
"""

import asyncio
import re
import subprocess
from pathlib import Path

from netwatch.scanner.base import DiscoveredDevice

_IP = re.compile(r"\b(\d{1,3}(?:\.\d{1,3}){3})\b")
_MAC = re.compile(r"\b([0-9a-fA-F]{1,2}(?:[:-][0-9a-fA-F]{1,2}){5})\b")
_PROC_ARP = Path("/proc/net/arp")


def normalise_mac(raw: str) -> str:
    return ":".join(part.zfill(2) for part in re.split(r"[:-]", raw.lower()))


def _is_unicast(mac: str) -> bool:
    if mac in ("00:00:00:00:00:00", "ff:ff:ff:ff:ff:ff"):
        return False
    # The least significant bit of the first octet marks multicast addresses.
    return int(mac[:2], 16) & 1 == 0


def parse_arp_output(text: str) -> list[DiscoveredDevice]:
    """Parse `arp -a` (Windows, macOS, Linux) or /proc/net/arp output.

    Every format puts an IPv4 address and a MAC address on the same line, so we look for
    both rather than depending on column positions.
    """
    devices: dict[str, DiscoveredDevice] = {}
    for line in text.splitlines():
        ip_match, mac_match = _IP.search(line), _MAC.search(line)
        if not ip_match or not mac_match:
            continue
        mac = normalise_mac(mac_match.group(1))
        if _is_unicast(mac):
            devices.setdefault(mac, DiscoveredDevice(mac=mac, ip=ip_match.group(1)))
    return list(devices.values())


class ArpTableScanner:
    async def scan(self) -> list[DiscoveredDevice]:
        return parse_arp_output(await asyncio.to_thread(self._read_table))

    @staticmethod
    def _read_table() -> str:
        if _PROC_ARP.exists():
            return _PROC_ARP.read_text()
        result = subprocess.run(["arp", "-a"], capture_output=True, text=True, check=True)
        return result.stdout
