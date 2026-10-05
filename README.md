# NetWatch

![CI](https://github.com/krisztian-kovacs-sotet/netwatch/actions/workflows/ci.yml/badge.svg)

A home network security monitor. NetWatch keeps an inventory of every device on your
network, notices when something new joins or a known device changes address, and raises
alerts you can review and acknowledge through a REST API.

> **Scope:** NetWatch is for monitoring networks you own or administer. Discovery is
> passive by default (it reads the OS ARP cache and sends no packets).

## Features

- **Device inventory**: MAC, IP, first/last seen, user label, trusted flag
- **Change detection**: alerts for new devices and IP changes
- **Background scanning** on a configurable interval, or on demand via `POST /scans`
- **REST API** with interactive docs at `/docs`
- Runs on SQLite for development and PostgreSQL in Docker

## Architecture

```
 â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   DiscoveredDevice[]   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”   Device / Alert   â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
 â”‚   Scanner    â”‚ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¶ â”‚  Inventory   â”‚ â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â–¶ â”‚  Database  â”‚
 â”‚ (ARP table)  â”‚                        â”‚ record_scan  â”‚                    â”‚ SQLite/PG  â”‚
 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                        â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜                    â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
        â–²                                                                          â”‚
        â”‚ periodic task / POST /scans                                              â–¼
 â”Œâ”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”
 â”‚                                FastAPI  (api.py)                                     â”‚
 â””â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”˜
```

| Module | Responsibility |
|---|---|
| `scanner/` | `Scanner` protocol + `ArpTableScanner` (parses Windows, macOS and Linux formats) |
| `inventory.py` | Reconciles scan results with stored devices and creates alerts |
| `api.py` | HTTP endpoints |
| `main.py` | App factory, lifespan, background scan loop |

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
uvicorn --factory netwatch.main:create_app --reload
```

Open http://localhost:8000/docs.

With Docker (Linux host):

```bash
docker compose up --build
```

## API

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Liveness check |
| GET | `/devices?trusted=` | List devices, optionally filtered |
| GET | `/devices/{id}` | Device detail |
| PATCH | `/devices/{id}` | Set `label` / `trusted` |
| GET | `/alerts?unacknowledged_only=` | List alerts, newest first |
| POST | `/alerts/{id}/acknowledge` | Acknowledge an alert |
| POST | `/scans` | Run a scan now |

## Development

```bash
pytest          # tests + coverage
ruff check .    # lint
ruff format .   # format
mypy            # strict type checking
```

CI runs all of these on every push and pull request, plus a Docker build.

## Design decisions

- **Passive discovery first.** Reading the ARP cache is safe, needs no privileges and
  works cross-platform. Active scanning can be added behind the same `Scanner` protocol.
- **Parse by pattern, not by column.** Every `arp` output format puts an IPv4 and a MAC on
  one line, so a single regex-based parser handles Windows, macOS and `/proc/net/arp`.
- **App factory with injected dependencies.** Tests swap in an in-memory database and a
  fake scanner, so the whole HTTP flow is tested without touching the real network.

## Roadmap

- [ ] Web dashboard (device timeline, alert feed)
- [ ] Discord / email notifications
- [ ] MAC vendor lookup (OUI database)
- [ ] Optional active discovery and port checks (own networks only)
- [ ] API authentication
- [ ] Alembic migrations

## License

MIT
