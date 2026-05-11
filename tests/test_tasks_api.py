from __future__ import annotations

import pytest
from httpx import AsyncClient

from tests.conftest import login_token, register_user


@pytest.mark.asyncio
async def test_tasks_require_auth(client: AsyncClient) -> None:
    r = await client.get("/tasks")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_task_crud_flow(client: AsyncClient) -> None:
    u, p = await register_user(client)
    token = await login_token(client, u, p)
    h = {"Authorization": f"Bearer {token}"}

    create = {
        "title": "Задача A",
        "description": "Описание с текстом",
        "status": "pending",
        "priority": 10,
    }
    r = await client.post("/tasks", json=create, headers=h)
    assert r.status_code == 201
    task = r.json()
    tid = task["id"]
    assert task["title"] == create["title"]
    assert task["status_label"] == "в ожидании"

    r = await client.get(f"/tasks/{tid}", headers=h)
    assert r.status_code == 200
    assert r.json()["id"] == tid

    r = await client.put(
        f"/tasks/{tid}",
        json={
            "title": "Новый заголовок",
            "description": "новое",
            "status": "in_progress",
            "priority": 5,
        },
        headers=h,
    )
    assert r.status_code == 200
    assert r.json()["status_label"] == "в работе"

    r = await client.patch(f"/tasks/{tid}", json={"priority": 99}, headers=h)
    assert r.status_code == 200
    assert r.json()["priority"] == 99

    r = await client.delete(f"/tasks/{tid}", headers=h)
    assert r.status_code == 204

    r = await client.get(f"/tasks/{tid}", headers=h)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_task_not_found(client: AsyncClient) -> None:
    u, p = await register_user(client)
    token = await login_token(client, u, p)
    h = {"Authorization": f"Bearer {token}"}

    for method, path, body in [
        ("GET", "/tasks/99999", None),
        ("PUT", "/tasks/99999", {"title": "x", "description": "", "status": "pending", "priority": 0}),
        ("PATCH", "/tasks/99999", {"title": "y"}),
        ("DELETE", "/tasks/99999", None),
    ]:
        if method == "GET":
            r = await client.get(path, headers=h)
        elif method == "PUT":
            r = await client.put(path, json=body, headers=h)
        elif method == "PATCH":
            r = await client.patch(path, json=body, headers=h)
        else:
            r = await client.delete(path, headers=h)
        assert r.status_code == 404


@pytest.mark.asyncio
async def test_tasks_user_isolation(client: AsyncClient) -> None:
    u1, p1 = await register_user(client)
    u2, p2 = await register_user(client)
    t1 = await login_token(client, u1, p1)
    t2 = await login_token(client, u2, p2)
    h1 = {"Authorization": f"Bearer {t1}"}
    h2 = {"Authorization": f"Bearer {t2}"}

    r = await client.post(
        "/tasks",
        json={"title": "только user1", "description": "", "status": "pending", "priority": 1},
        headers=h1,
    )
    tid = r.json()["id"]
    r = await client.get(f"/tasks/{tid}", headers=h2)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_tasks_search(client: AsyncClient) -> None:
    u, p = await register_user(client)
    token = await login_token(client, u, p)
    h = {"Authorization": f"Bearer {token}"}
    await client.post(
        "/tasks",
        json={"title": "Alpha", "description": "beta gamma", "status": "pending", "priority": 1},
        headers=h,
    )

    r = await client.get("/tasks/search", params={"q": "ALPHA"}, headers=h)
    assert r.status_code == 200
    assert len(r.json()) >= 1

    r = await client.get("/tasks/search", params={"q": "gamma"}, headers=h)
    assert r.status_code == 200
    assert any("gamma" in (t.get("description") or "").lower() for t in r.json())


@pytest.mark.asyncio
async def test_tasks_search_query_validation(client: AsyncClient) -> None:
    u, p = await register_user(client)
    token = await login_token(client, u, p)
    h = {"Authorization": f"Bearer {token}"}

    r = await client.get("/tasks/search", headers=h)
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_tasks_top(client: AsyncClient) -> None:
    u, p = await register_user(client)
    token = await login_token(client, u, p)
    h = {"Authorization": f"Bearer {token}"}
    for pr, title in [(1, "low"), (50, "high"), (10, "mid")]:
        await client.post(
            "/tasks",
            json={"title": title, "description": "", "status": "pending", "priority": pr},
            headers=h,
        )

    r = await client.get("/tasks/top", params={"n": 2}, headers=h)
    assert r.status_code == 200
    tops = r.json()
    assert len(tops) <= 2
    priorities = [t["priority"] for t in tops]
    assert priorities == sorted(priorities, reverse=True)


@pytest.mark.asyncio
async def test_tasks_top_n_validation(client: AsyncClient) -> None:
    u, p = await register_user(client)
    token = await login_token(client, u, p)
    h = {"Authorization": f"Bearer {token}"}

    assert (await client.get("/tasks/top", params={"n": 0}, headers=h)).status_code == 422
    assert (await client.get("/tasks/top", params={"n": 501}, headers=h)).status_code == 422


@pytest.mark.asyncio
async def test_tasks_list_sort(client: AsyncClient) -> None:
    u, p = await register_user(client)
    token = await login_token(client, u, p)
    h = {"Authorization": f"Bearer {token}"}
    await client.post(
        "/tasks",
        json={"title": "b", "description": "", "status": "completed", "priority": 2},
        headers=h,
    )
    await client.post(
        "/tasks",
        json={"title": "a", "description": "", "status": "pending", "priority": 1},
        headers=h,
    )

    r = await client.get("/tasks", params={"sort_by": "title", "order": "asc"}, headers=h)
    assert r.status_code == 200
    titles = [t["title"] for t in r.json()]
    assert titles == sorted(titles)


@pytest.mark.asyncio
async def test_create_task_validation(client: AsyncClient) -> None:
    u, p = await register_user(client)
    token = await login_token(client, u, p)
    h = {"Authorization": f"Bearer {token}"}

    r = await client.post(
        "/tasks",
        json={"title": "", "description": "", "status": "pending", "priority": 0},
        headers=h,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_list_cache_reduces_db_reads(client: AsyncClient, mocker) -> None:
    from app.crud import task as task_mod

    u, p = await register_user(client)
    token = await login_token(client, u, p)
    h = {"Authorization": f"Bearer {token}"}

    real = task_mod.list_tasks
    calls = {"n": 0}

    async def wrapped(db, user_id, **kw):
        calls["n"] += 1
        return await real(db, user_id, **kw)

    mocker.patch("app.api.tasks.task_crud.list_tasks", side_effect=wrapped)

    await client.get("/tasks", headers=h)
    await client.get("/tasks", headers=h)
    assert calls["n"] == 1

    await client.post(
        "/tasks",
        json={"title": "new", "description": "", "status": "pending", "priority": 0},
        headers=h,
    )
    await client.get("/tasks", headers=h)
    assert calls["n"] == 2


@pytest.mark.asyncio
async def test_top_cache_reduces_db_reads(client: AsyncClient, mocker) -> None:
    from app.crud import task as task_mod

    u, p = await register_user(client)
    token = await login_token(client, u, p)
    h = {"Authorization": f"Bearer {token}"}
    await client.post(
        "/tasks",
        json={"title": "x", "description": "", "status": "pending", "priority": 3},
        headers=h,
    )

    real = task_mod.top_by_priority
    calls = {"n": 0}

    async def wrapped(db, user_id, n):
        calls["n"] += 1
        return await real(db, user_id, n)

    mocker.patch("app.api.tasks.task_crud.top_by_priority", side_effect=wrapped)

    await client.get("/tasks/top", params={"n": 5}, headers=h)
    await client.get("/tasks/top", params={"n": 5}, headers=h)
    assert calls["n"] == 1
