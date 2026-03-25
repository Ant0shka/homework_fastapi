from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token, verify_password
from app.crud import user as user_crud
from app.database import get_db
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(data: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]) -> UserRead:
    if await user_crud.get_by_username(db, data.username):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Имя пользователя занято")
    user = await user_crud.create(db, data)
    await db.commit()
    return UserRead.model_validate(user)


@router.post("/login", response_model=Token)
async def login(
    db: Annotated[AsyncSession, Depends(get_db)],
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = await user_crud.get_by_username(db, form.username)
    if user is None or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = create_access_token(str(user.id))
    return Token(access_token=token)
