from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.core import cache as task_cache
from app.crud import task as task_crud
from app.database import get_db
from app.models.user import User
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/tasks", tags=["tasks"])


def _to_read_list(tasks: list) -> list[TaskRead]:
    return [TaskRead.model_validate(t) for t in tasks]


@router.get("/search", response_model=list[TaskRead])
async def search_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    q: Annotated[str, Query(min_length=1)],
) -> list[TaskRead]:
    """полный перебор строк"""
    rows = await task_crud.search_scan(db, current_user.id, q)
    return _to_read_list(rows)


@router.get("/top", response_model=list[TaskRead])
async def top_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    n: Annotated[int, Query(ge=1, le=500)] = 5,
) -> list[TaskRead]:
    ver = task_cache.user_cache_version(current_user.id)
    key = (current_user.id, ver, "top", n)
    hit = task_cache.top_cache_get(key)
    if hit is not None:
        return hit
    rows = await task_crud.top_by_priority(db, current_user.id, n)
    out = _to_read_list(rows)
    task_cache.top_cache_set(key, out)
    return out


@router.get("", response_model=list[TaskRead])
async def list_tasks(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    sort_by: Literal["title", "status", "created_at", "priority"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
) -> list[TaskRead]:
    ver = task_cache.user_cache_version(current_user.id)
    key = (current_user.id, ver, "list", sort_by, order)
    hit = task_cache.list_cache_get(key)
    if hit is not None:
        return hit
    rows = await task_crud.list_tasks(db, current_user.id, sort_by=sort_by, order=order)
    out = _to_read_list(rows)
    task_cache.list_cache_set(key, out)
    return out


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
async def create_task(
    body: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TaskRead:
    task = await task_crud.create(db, current_user.id, body)
    await db.commit()
    task_cache.bump_user_cache_version(current_user.id)
    return TaskRead.model_validate(task)


@router.get("/{task_id}", response_model=TaskRead)
async def get_task(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TaskRead:
    task = await task_crud.get_by_id(db, current_user.id, task_id)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    return TaskRead.model_validate(task)


@router.put("/{task_id}", response_model=TaskRead)
async def update_task_put(
    task_id: int,
    body: TaskCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TaskRead:
    upd = TaskUpdate(
        title=body.title,
        description=body.description,
        status=body.status,
        priority=body.priority,
    )
    task = await task_crud.update(db, current_user.id, task_id, upd)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    await db.commit()
    task_cache.bump_user_cache_version(current_user.id)
    return TaskRead.model_validate(task)


@router.patch("/{task_id}", response_model=TaskRead)
async def update_task_patch(
    task_id: int,
    body: TaskUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> TaskRead:
    task = await task_crud.update(db, current_user.id, task_id, body)
    if task is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    await db.commit()
    task_cache.bump_user_cache_version(current_user.id)
    return TaskRead.model_validate(task)


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: int,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
) -> None:
    ok = await task_crud.delete(db, current_user.id, task_id)
    if not ok:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Задача не найдена")
    await db.commit()
    task_cache.bump_user_cache_version(current_user.id)
