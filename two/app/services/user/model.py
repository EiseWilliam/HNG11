from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column
from uuid import uuid4
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    firstName: Mapped[str] = mapped_column(String, nullable=False)
    lastName: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String)
    userId: Mapped[str] = mapped_column(
        String, primary_key=True, unique=True, default=str(uuid4())
    )

    def __repr__(self):
        return f"<User {self.email}>"
