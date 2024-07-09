from datetime import datetime
from os import access
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field


from app.core.schema import BaseRespone
from app.services.user.model import User


class UserBase(BaseModel):
    email: Annotated[EmailStr, Field(max_length=100)]


class UserCreate(UserBase):
    firstName: str
    lastName: str
    password: str
    phone: str

class LoginSchema(BaseModel):
    email: str
    password: str

class UserRead(UserBase):
    userId: str
    firstName: str
    lastName: str
    phone: str


class UserToken(BaseModel):
    accessToken: str
    user: UserRead


class AuthResponse(BaseRespone):
    data: UserToken


class UserResponse(BaseRespone):
    status: str = "success"
    message: str = "User data retrieved successfully"
    data: UserRead