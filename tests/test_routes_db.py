from __future__ import annotations

import pytest
from fastapi import HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app.api import auth as auth_routes
from app.api import deps as deps_routes
from app.api import tasks as tasks_routes
from app.core.security import create_access_token
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.schemas.user import UserCreate


@pytest.mark.asyncio
async def test_auth_register_success_and_duplicate(db_session) -> None:
    data = UserCreate(username="direct_reg_ok", password="password1")
    out = await auth_routes.register(data, db_session)
    assert out.username == "direct_reg_ok"

    with pytest.raises(HTTPException) as ei:
        await auth_routes.register(data, db_session)
    assert ei.value.status_code == 400


@pytest.mark.asyncio
async def test_auth_login_unknown_user(db_session) -> None:
    form = OAuth2PasswordRequestForm(username="nope_user", password="password1")
    with pytest.raises(HTTPException) as ei:
        await auth_routes.login(db_session, form)
    assert ei.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_login_wrong_password(db_session) -> None:
    await auth_routes.register(UserCreate(username="direct_login_u", password="password1"), db_session)
    await db_session.commit()

    form = OAuth2PasswordRequestForm(username="direct_login_u", password="badpassword")
    with pytest.raises(HTTPException) as ei:
        await auth_routes.login(db_session, form)
    assert ei.value.status_code == 401


@pytest.mark.asyncio
async def test_auth_login_success(db_session) -> None:
    await auth_routes.register(UserCreate(username="direct_login_ok", password="password1"), db_session)
    await db_session.commit()

    form = OAuth2PasswordRequestForm(username="direct_login_ok", password="password1")
    tok = await auth_routes.login(db_session, form)
    assert tok.access_token


@pytest.mark.asyncio
async def test_deps_user_not_found(db_session) -> None:
    token = create_access_token("999001")
    with pytest.raises(HTTPException) as ei:
        await deps_routes.get_current_user(token, db_session)
    assert ei.value.status_code == 401


@pytest.mark.asyncio
async def test_deps_get_current_user_success(db_session) -> None:
    await auth_routes.register(UserCreate(username="deps_ok_user", password="password1"), db_session)
    await db_session.commit()

    from app.crud import user as user_crud

    row = await user_crud.get_by_username(db_session, "deps_ok_user")
    assert row is not None
    token = create_access_token(str(row.id))
    u = await deps_routes.get_current_user(token, db_session)
    assert u.username == "deps_ok_user"


@pytest.mark.asyncio
async def test_tasks_handlers_flow(db_session) -> None:
    user = await auth_routes.register(UserCreate(username="direct_tasks_u", password="password1"), db_session)
    await db_session.commit()
    u = await db_session.get(User, user.id)
    assert u is not None

    created = await tasks_routes.create_task(
        TaskCreate(title="t1", description="d1", status="pending", priority=5),
        db_session,
        u,
    )
    await db_session.commit()
    tid = created.id

    rows = await tasks_routes.search_tasks(db_session, u, q="t1")
    assert len(rows) >= 1

    top1 = await tasks_routes.top_tasks(db_session, u, n=5)
    top2 = await tasks_routes.top_tasks(db_session, u, n=5)
    assert len(top1) >= 1 and len(top2) >= 1

    lst1 = await tasks_routes.list_tasks(db_session, u, sort_by="title", order="asc")
    lst2 = await tasks_routes.list_tasks(db_session, u, sort_by="title", order="asc")
    assert len(lst1) >= 1 and len(lst2) >= 1

    one = await tasks_routes.get_task(tid, db_session, u)
    assert one.id == tid

    with pytest.raises(HTTPException):
        await tasks_routes.get_task(999_888, db_session, u)

    put = await tasks_routes.update_task_put(
        tid,
        TaskCreate(title="t2", description="d2", status="in_progress", priority=9),
        db_session,
        u,
    )
    assert put.title == "t2"
    await db_session.commit()

    pat = await tasks_routes.update_task_patch(tid, TaskUpdate(priority=1), db_session, u)
    assert pat.priority == 1
    await db_session.commit()

    with pytest.raises(HTTPException):
        await tasks_routes.update_task_put(
            999_888,
            TaskCreate(title="x", description="", status="pending", priority=0),
            db_session,
            u,
        )

    with pytest.raises(HTTPException):
        await tasks_routes.update_task_patch(999_888, TaskUpdate(title="nope"), db_session, u)

    await tasks_routes.delete_task(tid, db_session, u)
    await db_session.commit()

    with pytest.raises(HTTPException):
        await tasks_routes.delete_task(999_888, db_session, u)
