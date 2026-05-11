from __future__ import annotations

import pytest

from app.crud import task as task_crud
from app.crud import user as user_crud
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_user_crud_get_by_username_and_id(db_session) -> None:
    u = await user_crud.create(db_session, UserCreate(username="lookup_u", password="password1"))
    await db_session.commit()

    assert (await user_crud.get_by_username(db_session, "lookup_u")) is not None
    assert (await user_crud.get_by_username(db_session, "missing_x")) is None
    assert (await user_crud.get_by_id(db_session, u.id)) is not None
    assert (await user_crud.get_by_id(db_session, 999_888)) is None


@pytest.mark.asyncio
async def test_task_top_by_priority_limit_and_search_matches(db_session) -> None:
    u = await user_crud.create(db_session, UserCreate(username="extra_u", password="password1"))
    await db_session.commit()

    tops = await task_crud.top_by_priority(db_session, u.id, n=9999)
    assert isinstance(tops, list)

    await task_crud.create(
        db_session,
        u.id,
        TaskCreate(title="Hello", description="World", status="pending", priority=1),
    )
    await db_session.commit()

    found = await task_crud.search_scan(db_session, u.id, "hello")
    assert len(found) >= 1

    updated = await task_crud.update(
        db_session,
        u.id,
        found[0].id,
        TaskUpdate(description="x", status="completed", priority=3),
    )
    assert updated is not None
    assert updated.status.value == "completed"
    await db_session.commit()
