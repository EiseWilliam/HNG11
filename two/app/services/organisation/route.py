from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_user, user_belongs_in_organisation
from app.core.database import async_get_db
from app.services.organisation.model import Organisation, OrganisationUser
from app.services.organisation.schema import OrganisationCreate, OrganisationListResponse, OrganisationResponse, OrganisationUserCreate
from app.services.user.model import User
from app.services.organisation.crud import org_handler


router = APIRouter(tags=["organisation"])

@router.post("/api/organisations", response_model=OrganisationResponse, status_code=201)
async def create_organisation(
    organisation: OrganisationCreate,
    user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Create a new organisation
    """
    
    new_organisation = await org_handler.create(db, organisation)
    new_user_in_org = OrganisationUser(userId=user.userId, orgId=new_organisation.orgId)
    db.add(new_user_in_org)
    await db.commit()
    return {"status": "success", "message": "Organisation created successfully", "data": new_organisation}

@router.get("/api/organisation/{orgId}", response_model=OrganisationResponse, status_code=200)
async def read_organisation(
    orgId: str,
    user: Annotated[User, Depends(get_current_user)],   
    db: Annotated[AsyncSession, Depends(async_get_db)],
    can_view: Annotated[bool, Depends(user_belongs_in_organisation)]
):
    """
    Get organisation by ID
    """
    if not can_view:
        return JSONResponse({"status": "error", "message": "User does not belong to organisation", "statusCode": 401}, status_code=401)
    organisation = await org_handler.get(db, orgId=orgId)
    return {"status": "success", "message": "Organisation data retrieved successfully", "data": organisation}

@router.get("/api/organisations", status_code=200, response_model=OrganisationListResponse)
async def get_user_organisations(
    db: Annotated[AsyncSession, Depends(async_get_db)],
    user: Annotated[User, Depends(get_current_user)]
):
    """
    Get all organisations
    """
    user_orgs = (await db.execute(select(OrganisationUser).filter(OrganisationUser.userId == user.userId))).scalars().all()
    org_ids = [org.orgId for org in user_orgs]
    organisations = (await db.execute(select(Organisation).filter(Organisation.orgId.in_(org_ids)))).scalars().all()
    return {"status": "success", "message": "Organisations data retrieved successfully", "data": {"organisations": organisations}}

@router.post("/api/organisation/{orgId}/users", status_code=200)
async def add_user_to_organisation(
    orgId: str,
    user: OrganisationUserCreate,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[AsyncSession, Depends(async_get_db)]
):
    """
    Add a user to an organisation
    """
    try:
        new_user_in_org = OrganisationUser(userId=user.userId, orgId=orgId)
        db.add(new_user_in_org)
        await db.commit()
    except IntegrityError:
        return JSONResponse({"status": "error", "message": "User already exists in organisation", "statusCode": 400}, status_code=400)
    return {"status": "success", "message": "User added to organisation successfully"}