import enum
from uuid import uuid4
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Organisation(Base):
    __tablename__ = "organisations"

    name: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(String, nullable=True, default=None)
    orgId: Mapped[str] = mapped_column(
        String, primary_key=True, unique=True, default=str(uuid4())
    )

    def __repr__(self):
        return f"<Organisation {self.name}>"

class OrganisationUser(Base):
    __tablename__ = "organisation_users"
    userId: Mapped[str] = mapped_column(String, nullable=False)
    orgId: Mapped[str] = mapped_column(String, nullable=False)
    orgUserId: Mapped[str] = mapped_column(
        String, primary_key=True, unique=True, default=str(uuid4())
    )
    role: Mapped[str] = mapped_column(String, nullable=False, default="member")

    def __repr__(self):
        return f"<OrganisationUser {self.userId} in {self.orgId}>"