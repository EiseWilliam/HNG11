from fastcrud import FastCRUD

from app.services.user.model import User
from app.services.user.schema import UserCreate, UserDelete, UserRead, UserUpdate, UserUpdateInternal

CRUDUser = FastCRUD[User, UserCreate, UserUpdate, UserUpdateInternal, UserDelete]
user_handler = CRUDUser(User)

