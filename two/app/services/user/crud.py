from fastcrud import FastCRUD

from app.services.user.model import User

CRUDUser = FastCRUD
user_handler = CRUDUser(User)

