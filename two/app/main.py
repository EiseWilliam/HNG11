from fastapi import FastAPI, Request
from fastapi.concurrency import asynccontextmanager
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi import status
from app.core.config import settings
from app.core.database import create_tables
from app.services.user.route import router as user_router
from app.services.organisation.route import router as org_router
from sqlalchemy.exc import IntegrityError


@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield


def get_application():
    _app = FastAPI(title=settings.PROJECT_NAME, lifespan=lifespan)
    _app.include_router(user_router)
    _app.include_router(org_router)
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    return _app


app = get_application()


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc):
    errors = []
    for error in exc.errors():
        errors.append({"field": error["loc"][-1], "message": error["msg"]})
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"errors": errors},
    )


@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc):
    return JSONResponse(
        status_code=400,
        content={"message": "Conflict", "detail": str(exc.orig)},
    )
