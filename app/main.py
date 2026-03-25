from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api import auth, tasks
from app.database import Base, engine
from app.models import Task, User  # noqa: F401


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


app = FastAPI(title="Task Manager", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(tasks.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
