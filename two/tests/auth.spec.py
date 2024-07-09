import pytest
from httpx import AsyncClient
from sqlalchemy import text
from app.core.config import settings
from app.main import app
from app.core.database import Base, async_get_db
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

# Test database URL
TEST_DATABASE_URL = settings.DATABASE_URI

async_engine = create_async_engine(TEST_DATABASE_URL, echo=False, future=True)
test_session = sessionmaker(
    bind=async_engine, class_=AsyncSession, expire_on_commit=False
)


@pytest.fixture(scope="function")
async def clear_db():
    async with async_engine.begin() as session:
        await session.execute(text("DELETE FROM users"))
        await session.execute(text("DELETE FROM organisations"))
        await session.execute(text("DELETE FROM organisation_users"))
        await session.commit()
        yield


@pytest.fixture(scope="module")
async def test_app():
    # Setup
    engine = create_async_engine(TEST_DATABASE_URL)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async def override_get_db():
        async with test_session() as session:
            yield session

    app.dependency_overrides[async_get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

    # Teardown
    app.dependency_overrides.clear()


@pytest.mark.anyio
async def test_register_user_successfully(test_app, clear_db):
    response = await test_app.post(
        "/auth/register",
        json={
            "firstName": "John",
            "lastName": "Doe",
            "email": "john5@example.com",
            "password": "securepassword",
            "phone": "1234567890",
        },
    )
    print(response.json())
    assert response.status_code == 201
    data = response.json()["data"]
    assert "accessToken" in data
    assert data["user"]["firstName"] == "John"
    assert data["user"]["lastName"] == "Doe"
    assert data["user"]["email"] == "john5@example.com"

    # Verify default organisation
    org_response = await test_app.get(
        "/api/organisations",
        headers={"Authorization": f"Bearer {data['accessToken']}"},
    )
    assert org_response.status_code == 200
    orgs = org_response.json()["data"]["organisations"]
    assert len(orgs) == 1
    assert orgs[0]["name"] == "John's Organisation"


@pytest.mark.anyio
async def test_login_user_successfully(test_app, clear_db):
    await test_app.post(
        "/auth/register",
        json={
            "firstName": "Jane",
            "lastName": "Doe",
            "email": "jane@example.com",
            "password": "securepassword",
            "phone": "1234567890",
        },
    )

    response = await test_app.post(
        "/auth/login",
        json={"email": "jane@example.com", "password": "securepassword"},
    )


    assert response.status_code == 200
    data = response.json()["data"]
    assert "accessToken" in data
    assert data["user"]["email"] == "jane@example.com"


@pytest.mark.anyio
async def test_login_fails_with_invalid_credentials(test_app):
    response = await test_app.post(
        "/auth/login",
        json={"email": "jane@example.com", "password": "wrongpassword"},
    )

    assert response.status_code == 401


@pytest.mark.anyio
@pytest.mark.parametrize(
    "missing_field", ["firstName", "lastName", "email", "password"]
)
async def test_register_fails_with_missing_fields(test_app, missing_field):
    user_data = {
        "firstName": "Test",
        "lastName": "User",
        "email": "test@example.com",
        "password": "testpassword",
    }
    del user_data[missing_field]

    response = await test_app.post("/auth/register", json=user_data)

    assert response.status_code == 422
    errors = response.json()["errors"]
    assert any([error["field"] == missing_field for error in errors])


@pytest.mark.anyio
async def test_register_fails_with_duplicate_email(test_app):
    await test_app.post(
        "/auth/register",
        json={
            "firstName": "First",
            "lastName": "User",
            "email": "duplicate@example.com",
            "password": "password123",
            "phone": "1234567890",
        },
    )

    response = await test_app.post(
        "/auth/register",
        json={
            "firstName": "Second",
            "lastName": "User",
            "email": "duplicate@example.com",
            "password": "anotherpassword",
            "phone": "1234567890",
        },
    )

    assert response.status_code == 400
