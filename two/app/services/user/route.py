import logging
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    authenticate_user,
    create_access_token,
    get_current_user,
    get_password_hash,
    user_shares_organisation,
)
from app.core.database import async_get_db
from app.services.organisation.model import Organisation, OrganisationUser
from app.services.user.model import User
from app.services.user.schema import (
    AuthResponse,
    LoginSchema,
    UserCreate,
    UserRead,
    UserResponse,
    UserToken,
)
from app.services.user.crud import user_handler

router = APIRouter(tags=["user"])



logger = logging.getLogger(__name__)

@router.post("/auth/register", response_model=AuthResponse, status_code=201)
async def register(
    user: UserCreate, db: Annotated[AsyncSession, Depends(async_get_db)]
):

    user_in_db = await user_handler.exists(db, email=user.email)
    if user_in_db:
        return JSONResponse(
            {
                "status": "Bad request",
                "message": "Registration unsuccessful",
                "statusCode": 400,
            },
            400,
        )

    hashed_password = get_password_hash(user.password)
    new_user = User(
        firstName=user.firstName,
        lastName=user.lastName,
        email=user.email,
        password=hashed_password,
        phone=user.phone,
    )
    db.add(new_user)

    org_name = f"{user.firstName}'s Organisation"
    new_org = Organisation(name=org_name)
    db.add(new_org)

    await db.commit()
    await db.refresh(new_user)
    await db.refresh(new_org)

    user_org = OrganisationUser(
        userId=new_user.userId, orgId=new_org.orgId, role="admin"
    )
    db.add(user_org)
    await db.commit()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"sub": new_user.userId, "email": new_user.email},
        expires_delta=access_token_expires,
    )

    return {
        "message": "Registration successful",
        "status": "success",
        "data": {"accessToken": access_token, "user": new_user},
    }


@router.post("/auth/login", response_model=AuthResponse, status_code=200)
async def login(
    form_data: LoginSchema,
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    user = await authenticate_user(form_data.email, form_data.password, db)
    if not user:
        return JSONResponse(
            {
                "status": "Bad request",
                "message": "Authentication failed",
                "statusCode": 401,
            },
            401,
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"email": user.email, "sub": user.userId},
        expires_delta=access_token_expires,
    )
    return {
        "message": "Login successful",
        "status": "success",
        "data": {"accessToken": access_token, "user": user},
    }


@router.post("/api/token", status_code=200)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(async_get_db)],
):
    user = await authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = await create_access_token(
        data={"email": user.email, "sub": user.userId},
        expires_delta=access_token_expires,
    )
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/api/user", response_model=UserResponse, status_code=200)
async def get_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    return {
        "message": "User details fetched successfully",
        "status": "success",
        "data": current_user
    }


@router.get("/api/users/{userId}", response_model=UserResponse, status_code=200)
async def get_user_by_id(
    userId: str,
    db: Annotated[AsyncSession, Depends(async_get_db)],
    can_view: Annotated[bool, Depends(user_shares_organisation)],
):
    # only fetch the user details to user who share organisation with the current user
    user = await user_handler.get(db, userId=userId)
    if can_view:
        return {
            "message": "User details fetched successfully",
            "status": "success",
            "data": user}
    return JSONResponse(
        {
            "status": "forbidden",
            "message": "You are not authorized to view this user",
            "statusCode": 403,
        },
        403,
    )


