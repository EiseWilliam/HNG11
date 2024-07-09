from datetime import UTC, datetime, timedelta
from typing import Annotated, Any, Literal

import bcrypt
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import async_get_db
from app.services.organisation.model import OrganisationUser

from app.core.config import settings
from app.services.user.model import User

SECRET_KEY = settings.SECRET_KEY
ALGORITHM = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES
# REFRESH_TOKEN_EXPIRE_DAYS = settings.REFRESH_TOKEN_EXPIRE_DAYS

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


async def verify_password(plain_password: str, hashed_password: str) -> bool:
    correct_password: bool = bcrypt.checkpw(
        plain_password.encode(), hashed_password.encode()
    )
    return correct_password


def get_password_hash(password: str) -> str:
    hashed_password: str = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    return hashed_password


async def authenticate_user(
    email: str, password: str, db: AsyncSession
) -> User | Literal[False]:
    user = (
        (await db.execute(select(User).filter(User.email == email))).scalars().first()
    )
    if not user or not await verify_password(password, user.password):
        return False
    return user


async def create_access_token(
    data: dict[str, Any], expires_delta: timedelta | None = None
) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC).replace(tzinfo=None) + expires_delta
    else:
        expire = datetime.now(UTC).replace(tzinfo=None) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )
    to_encode.update({"exp": expire})
    encoded_jwt: str = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def verify_token(token: str, db: AsyncSession) -> str | None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username_or_email = payload.get("sub")
        if username_or_email is None:
            return None
        return username_or_email

    except JWTError:
        return None


async def get_current_user(
    token: str = Depends(oauth2_scheme), db: AsyncSession = Depends(async_get_db)
):
    credentials_exception = HTTPException(
        status_code=401,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("email")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    user = (
        (await db.execute(select(User).filter(User.email == email))).scalars().first()
    )
    if user is None:
        raise credentials_exception
    return user

async def user_shares_organisation(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user: Annotated[User, Depends(get_current_user)],
    userId: str,
) -> bool:
    if user.userId == userId:
        return True
    user_orgs = (
        await db.execute(
            select(OrganisationUser).filter(OrganisationUser.userId == user.userId)
        )
    ).scalars().all()
    org_ids = [org.orgId for org in user_orgs]
    user_orgs = (
        await db.execute(
            select(OrganisationUser)
            .filter(OrganisationUser.userId == userId)
            .filter(OrganisationUser.orgId.in_(org_ids))
        )
    ).scalars().all()
    return bool(user_orgs)

async def user_belongs_in_organisation(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user: Annotated[User, Depends(get_current_user)],
    orgId: str,
) -> bool:
    user_orgs = (
        await db.execute(
            select(OrganisationUser).filter(OrganisationUser.userId == user.userId).filter(OrganisationUser.orgId == orgId)
        )
    ).scalars().all()
    return bool(user_orgs)