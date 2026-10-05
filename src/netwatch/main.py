"""Application factory. Run with: uvicorn --factory netwatch.main:create_app"""

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator

from fastapi import FastAPI
from sqlalchemy.orm import sessionmaker

from netwatch import __version__, models  # noqa: F401  (registers tables on Base)
from netwatch.api import router
from netwatch.config import Settings
from netwatch.db import Base, make_engine
from netwatch.inventory import scan_forever
from netwatch.scanner import ArpTableScanner, Scanner


def create_app(settings: Settings | None = None, scanner: Scanner | None = None) -> FastAPI:
    settings = settings or Settings()
    scanner = scanner or ArpTableScanner()
    engine = make_engine(settings.database_url)
    session_factory = sessionmaker(engine, expire_on_commit=False)

    @contextlib.asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        logging.basicConfig(level=logging.INFO)
        Base.metadata.create_all(engine)
        task = None
        if settings.scan_interval_seconds > 0:
            task = asyncio.create_task(
                scan_forever(scanner, session_factory, settings.scan_interval_seconds)
            )
        yield
        if task is not None:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
        engine.dispose()

    app = FastAPI(title="NetWatch", version=__version__, lifespan=lifespan)
    app.state.session_factory = session_factory
    app.state.scanner = scanner
    app.include_router(router)
    return app
