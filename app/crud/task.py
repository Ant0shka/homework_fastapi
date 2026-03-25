from sqlalchemy import Select, asc, delete as sql_delete, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.schemas.task import TaskCreate, TaskUpdate

SORTABLE = frozenset({"title", "status", "created_at", "priority"})


def _task_base(user_id: int) -> Select:
    return select(Task).where(Task.user_id == user_id)


async def create(db: AsyncSession, user_id: int, data: TaskCreate) -> Task:
    task = Task(
        user_id=user_id,
        title=data.title,
        description=data.description,
        status=data.status,
        priority=data.priority,
    )
    db.add(task)
    await db.flush()
    await db.refresh(task)
    return task


async def get_by_id(db: AsyncSession, user_id: int, task_id: int) -> Task | None:
    r = await db.execute(_task_base(user_id).where(Task.id == task_id))
    return r.scalar_one_or_none()


async def list_tasks(
    db: AsyncSession,
    user_id: int,
    *,
    sort_by: str = "created_at",
    order: str = "desc",
) -> list[Task]:
    field = sort_by if sort_by in SORTABLE else "created_at"
    col = getattr(Task, field)
    order_expr = desc(col) if order.lower() == "desc" else asc(col)
    r = await db.execute(_task_base(user_id).order_by(order_expr))
    return list(r.scalars().all())


async def top_by_priority(db: AsyncSession, user_id: int, n: int) -> list[Task]:
    r = await db.execute(
        _task_base(user_id).order_by(desc(Task.priority)).limit(max(1, min(n, 500)))
    )
    return list(r.scalars().all())


async def search_scan(db: AsyncSession, user_id: int, q: str) -> list[Task]:
    """Full scan in Python (substring in title or description)."""
    needle = q.strip().lower()
    if not needle:
        return []
    r = await db.execute(_task_base(user_id))
    rows = list(r.scalars().all())
    return [t for t in rows if needle in t.title.lower() or needle in t.description.lower()]


async def update(db: AsyncSession, user_id: int, task_id: int, data: TaskUpdate) -> Task | None:
    task = await get_by_id(db, user_id, task_id)
    if task is None:
        return None
    if data.title is not None:
        task.title = data.title
    if data.description is not None:
        task.description = data.description
    if data.status is not None:
        task.status = data.status
    if data.priority is not None:
        task.priority = data.priority
    await db.flush()
    await db.refresh(task)
    return task


async def delete(db: AsyncSession, user_id: int, task_id: int) -> bool:
    r = await db.execute(
        sql_delete(Task).where(Task.id == task_id, Task.user_id == user_id)
    )
    await db.flush()
    return r.rowcount > 0
