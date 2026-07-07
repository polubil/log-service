from fastapi import FastAPI
from src.data.db import DB
from src.routers.api import router
from contextlib import asynccontextmanager

from src.config import get_settings

settings = get_settings()

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.db = DB(url=settings.database_url)
    await app.state.db.connect()
    await app.state.db.create_tables()
    yield
    await app.state.db.disconnect()

app = FastAPI(lifespan=lifespan)
app.include_router(router)