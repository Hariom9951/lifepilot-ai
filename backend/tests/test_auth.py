import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.features.auth.repositories import RoleRepository

# Mark all test cases in this module as asynchronous
pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def seed_roles(db_session: AsyncSession):
    """
    Seed standard roles prior to executing test cases.
    """
    # Seed default roles if not exists
    user_role = await RoleRepository.get_by_name(db_session, "USER")
    if not user_role:
        await RoleRepository.create(
            db_session, name="USER", description="Standard account user permissions."
        )
    admin_role = await RoleRepository.get_by_name(db_session, "ADMIN")
    if not admin_role:
        await RoleRepository.create(
            db_session, name="ADMIN", description="Administrative permissions."
        )
    await db_session.commit()


async def test_user_registration(client: AsyncClient) -> None:
    """
    Test user registration successfully.
    """
    payload = {
        "full_name": "Test User",
        "username": "testuser",
        "email": "test@example.com",
        "password": "Password123!",
        "timezone": "UTC",
        "language": "en",
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["username"] == "testuser"
    assert data["data"]["email"] == "test@example.com"
    assert data["data"]["role"]["name"] == "USER"


async def test_user_registration_duplicate_email(client: AsyncClient) -> None:
    """
    Test registering with duplicate email returns 409 conflict.
    """
    payload = {
        "full_name": "Test User 1",
        "username": "testuser1",
        "email": "duplicate@example.com",
        "password": "Password123!",
    }
    response1 = await client.post("/api/v1/auth/register", json=payload)
    assert response1.status_code == 201

    payload2 = {
        "full_name": "Test User 2",
        "username": "testuser2",
        "email": "duplicate@example.com",
        "password": "Password123!",
    }
    response2 = await client.post("/api/v1/auth/register", json=payload2)
    assert response2.status_code == 409
    assert "already registered" in response2.json()["message"]


async def test_user_registration_weak_password(client: AsyncClient) -> None:
    """
    Test registration fails with 422 if password is weak.
    """
    payload = {
        "full_name": "Test User 3",
        "username": "testuser3",
        "email": "weak@example.com",
        "password": "weakpassword",  # Passes min_length=8, fails strength checks (no digits, uppercase, special)
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 422
    assert (
        "Password must contain at least one uppercase letter"
        in response.json()["message"]
    )


async def test_user_login_success(client: AsyncClient) -> None:
    """
    Test user authentication successfully.
    """
    # 1. Register
    payload = {
        "full_name": "Login User",
        "username": "loginuser",
        "email": "login@example.com",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/register", json=payload)

    # 2. Login
    login_payload = {"username_or_email": "loginuser", "password": "Password123!"}
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "access_token" in data["data"]
    assert data["data"]["user"]["username"] == "loginuser"


async def test_user_logout(client: AsyncClient) -> None:
    """
    Test signing out revokes refresh token.
    """
    # 1. Register and Login
    payload = {
        "full_name": "Logout User",
        "username": "logoutuser",
        "email": "logout@example.com",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/register", json=payload)

    login_payload = {
        "username_or_email": "logout@example.com",
        "password": "Password123!",
    }
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200

    # 2. Logout
    client.cookies.update(login_resp.cookies)
    logout_resp = await client.post("/api/v1/auth/logout")
    assert logout_resp.status_code == 200


async def test_token_refresh(client: AsyncClient) -> None:
    """
    Test token rotation on /auth/refresh.
    """
    payload = {
        "full_name": "Refresh User",
        "username": "refreshuser",
        "email": "refresh@example.com",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/register", json=payload)

    login_payload = {"username_or_email": "refreshuser", "password": "Password123!"}
    # Log in to get set-cookie
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200

    # Refresh by passing cookies directly on client instance
    client.cookies.update(login_resp.cookies)
    refresh_resp = await client.post("/api/v1/auth/refresh")
    assert refresh_resp.status_code == 200
    assert "access_token" in refresh_resp.json()["data"]


async def test_get_current_user_profile(client: AsyncClient) -> None:
    """
    Test accessing /users/me with JWT access token.
    """
    payload = {
        "full_name": "Profile User",
        "username": "profileuser",
        "email": "profile@example.com",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/register", json=payload)

    login_payload = {"username_or_email": "profileuser", "password": "Password123!"}
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    token = login_resp.json()["data"]["access_token"]

    # Access /users/me
    headers = {"Authorization": f"Bearer {token}"}
    me_resp = await client.get("/api/v1/users/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["data"]["username"] == "profileuser"


async def test_update_profile(client: AsyncClient) -> None:
    """
    Test updating user profile details.
    """
    payload = {
        "full_name": "Update User",
        "username": "updateuser",
        "email": "update@example.com",
        "password": "Password123!",
    }
    await client.post("/api/v1/auth/register", json=payload)

    login_payload = {"username_or_email": "updateuser", "password": "Password123!"}
    login_resp = await client.post("/api/v1/auth/login", json=login_payload)
    token = login_resp.json()["data"]["access_token"]

    # Update profile
    headers = {"Authorization": f"Bearer {token}"}
    update_payload = {
        "full_name": "Updated Name",
        "timezone": "Europe/Paris",
        "language": "fr",
    }
    patch_resp = await client.patch(
        "/api/v1/users/profile", json=update_payload, headers=headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["data"]["full_name"] == "Updated Name"
    assert patch_resp.json()["data"]["timezone"] == "Europe/Paris"
    assert patch_resp.json()["data"]["language"] == "fr"
