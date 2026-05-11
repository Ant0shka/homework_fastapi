from __future__ import annotations

import pytest

from app.crud import task as task_crud
from app.crud import user as user_crud
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_search_scan_whitespace_only_returns_empty(db_session) -> None:
    u = await user_crud.create(db_session, UserCreate(username="crud_u1", password="password1"))
    await db_session.commit()
    await task_crud.create(
        db_session,
        u.id,
        TaskCreate(title="t", description="d", status="pending", priority=0),
    )
    await db_session.commit()

    rows = await task_crud.search_scan(db_session, u.id, "   ")
    assert rows == []


@pytest.mark.asyncio
async def test_list_tasks_invalid_sort_falls_back(db_session) -> None:
    u = await user_crud.create(db_session, UserCreate(username="crud_u2", password="password1"))
    await db_session.commit()
    await task_crud.create(
        db_session,
        u.id,
        TaskCreate(title="z", description="", status="pending", priority=0),
    )
    await db_session.commit()

    rows = await task_crud.list_tasks(db_session, u.id, sort_by="not_a_column", order="asc")
    assert len(rows) == 1


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_false(db_session) -> None:
    u = await user_crud.create(db_session, UserCreate(username="crud_u3", password="password1"))
    await db_session.commit()
    ok = await task_crud.delete(db_session, u.id, 999_999)
    await db_session.flush()
    assert ok is False


@pytest.mark.asyncio
async def test_update_partial_fields(db_session) -> None:
    u = await user_crud.create(db_session, UserCreate(username="crud_u4", password="password1"))
    await db_session.commit()
    t = await task_crud.create(
        db_session,
        u.id,
        TaskCreate(title="old", description="desc", status="pending", priority=1),
    )
    await db_session.commit()

    out = await task_crud.update(db_session, u.id, t.id, TaskUpdate(title="new"))
    await db_session.commit()
    assert out is not None
    assert out.title == "new"
    assert out.description == "desc"
