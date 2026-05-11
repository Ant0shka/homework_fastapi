from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.core.security import create_access_token


@pytest.mark.asyncio
async def test_tasks_with_malformed_bearer(client: AsyncClient) -> None:
    r = await client.get("/tasks", headers={"Authorization": "Bearer"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_tasks_with_invalid_token(client: AsyncClient) -> None:
    r = await client.get("/tasks", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_tasks_token_valid_user_missing(client: AsyncClient) -> None:
    token = create_access_token("999999")
    r = await client.get("/tasks", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_tasks_token_subject_not_int(client: AsyncClient, mocker) -> None:
    mocker.patch("app.api.deps.decode_token", return_value="not-an-int")
    r = await client.get("/tasks", headers={"Authorization": "Bearer any.token.here"})
    assert r.status_code == 401
