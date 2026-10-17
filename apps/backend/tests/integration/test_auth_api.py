import pytest


@pytest.mark.asyncio
async def test_register_and_login(async_client):
    # Register new workspace and user
    reg_payload = {
        "email": "newadmin@example.com",
        "password": "SecurePassword123!",
        "full_name": "New Admin",
        "workspace_name": "New Workspace",
        "role": "ADMIN",
    }
    reg_resp = await async_client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_resp.status_code == 200
    user_data = reg_resp.json()
    assert user_data["email"] == "newadmin@example.com"

    # Login
    login_payload = {
        "email": "newadmin@example.com",
        "password": "SecurePassword123!",
    }
    login_resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert login_resp.status_code == 200
    token_data = login_resp.json()
    assert "access_token" in token_data

    # Profile check with token
    headers = {"Authorization": f"Bearer {token_data['access_token']}"}
    me_resp = await async_client.get("/api/v1/auth/me", headers=headers)
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "newadmin@example.com"


@pytest.mark.asyncio
async def test_auth_rejection_invalid_credentials(async_client):
    login_payload = {
        "email": "nonexistent@example.com",
        "password": "WrongPassword!",
    }
    resp = await async_client.post("/api/v1/auth/login", json=login_payload)
    assert resp.status_code == 401
