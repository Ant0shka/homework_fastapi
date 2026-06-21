import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.api import auth, tasks
from app.database import Base, engine
from app.models import Task, User  # noqa: F401

STATIC_DIR = Path(__file__).resolve().parent / "static"


async def _init_database() -> None:
    for i in range(15):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            return
        except Exception:
            if i == 14:
                raise
            await asyncio.sleep(2)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await _init_database()
    yield
    await engine.dispose()


app = FastAPI(title="Task Manager", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(tasks.router)

if STATIC_DIR.is_dir():
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
async def root():
    index = STATIC_DIR / "index.html"
    if index.is_file():
        return FileResponse(index)
    return {"message": "Task Manager API", "docs": "/docs"}


@app.get("/health")
async def health():
    return {"status": "ok"}
