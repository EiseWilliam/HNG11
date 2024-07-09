from datetime import datetime
from pydoc import describe
from typing import Annotated

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.core.schema import BaseRespone
from app.services.organisation.model import Organisation


class OrganisationBase(BaseModel):
    name: str


class OrganisationCreate(OrganisationBase):
    description: str | None = None


class OrganisationUserCreate(BaseModel):
    userId: str

 

class OrganisationRead(OrganisationBase):
    orgId: str
    description: str | None = None


class OrganisationResponse(BaseRespone):
    status: str = "success"
    message: str = "Organisation data retrieved successfully"
    data: OrganisationRead


class OrganisationList(BaseRespone):
    organisations: list[OrganisationRead]


class OrganisationListResponse(BaseRespone):
    status: str = "success"
    message: str = "Organisations data retrieved successfully"
    data: OrganisationList
