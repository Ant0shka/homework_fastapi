from __future__ import annotations

import os
import uuid

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

os.environ.setdefault("DATABASE_URL", "sqlite+aiosqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret-key-32bytes-minimum!!")


def reset_app_caches() -> None:
    from app.core import cache as task_cache

    task_cache.reset_caches_for_tests()


@pytest.fixture(autouse=True)
def _isolate_caches() -> None:
    reset_app_caches()
    yield
    reset_app_caches()


@pytest_asyncio.fixture(autouse=True)
async def _wipe_db(client: AsyncClient):  # noqa: ARG001
    from sqlalchemy import text

    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as s:
        await s.execute(text("DELETE FROM tasks"))
        await s.execute(text("DELETE FROM users"))
        await s.commit()
    yield


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    from app.main import app
    from app.database import Base, engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest_asyncio.fixture
async def db_session(client: AsyncClient):  # noqa: ARG001
    from app.database import AsyncSessionLocal

    async with AsyncSessionLocal() as session:
        yield session


async def register_user(
    client: AsyncClient,
    *,
    username: str | None = None,
    password: str = "password1",
) -> tuple[str, str]:
    name = username or f"u_{uuid.uuid4().hex[:12]}"
    r = await client.post("/auth/register", json={"username": name, "password": password})
    assert r.status_code == 201, r.text
    return name, password


async def login_token(client: AsyncClient, username: str, password: str) -> str:
    r = await client.post(
        "/auth/login",
        data={"username": username, "password": password},
    )
    assert r.status_code == 200, r.text
    return r.json()["access_token"]
