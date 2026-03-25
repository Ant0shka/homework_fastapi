from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import get_password_hash
from app.models.user import User
from app.schemas.user import UserCreate


async def get_by_username(db: AsyncSession, username: str) -> User | None:
    r = await db.execute(select(User).where(User.username == username))
    return r.scalar_one_or_none()


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    r = await db.execute(select(User).where(User.id == user_id))
    return r.scalar_one_or_none()


async def create(db: AsyncSession, data: UserCreate) -> User:
    user = User(username=data.username, hashed_password=get_password_hash(data.password))
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user
