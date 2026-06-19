import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.config import settings
from app.database.connection import db
from app.api.routes import router
from app.bot import start_bot, stop_bot

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await db.create_pool()
        logger.info("Database pool created")
    except Exception as e:
        logger.warning("Database not available: %s", e)
    await start_bot()
    yield
    await stop_bot()
    await db.close_pool()


app = FastAPI(title=settings.app_name, debug=settings.debug, lifespan=lifespan)
app.include_router(router)
