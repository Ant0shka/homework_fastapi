import pytest
from httpx import AsyncClient

from tests.conftest import register_user


@pytest.mark.asyncio
async def test_register_and_login(client: AsyncClient) -> None:
    u, p = await register_user(client)
    r = await client.post("/auth/login", data={"username": u, "password": p})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data.get("token_type") == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient) -> None:
    u, p = await register_user(client)
    r = await client.post("/auth/register", json={"username": u, "password": p})
    assert r.status_code == 400
    assert "занято" in str(r.json().get("detail", "")).lower()


@pytest.mark.asyncio
async def test_login_invalid_credentials(client: AsyncClient) -> None:
    u, p = await register_user(client)
    r = await client.post("/auth/login", data={"username": u, "password": "wrongpass"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_register_validation_short_username(client: AsyncClient) -> None:
    r = await client.post("/auth/register", json={"username": "ab", "password": "secret1"})
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_register_validation_short_password(client: AsyncClient) -> None:
    r = await client.post("/auth/register", json={"username": "validuser", "password": "short"})
    assert r.status_code == 422
