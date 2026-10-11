import pytest
from fastapi.testclient import TestClient
from main import app
from app.config import settings

client = TestClient(app)

def test_register_and_login():
    email = "filmmaker@example.com"
    pwd = "SecurePassword123!"
    
    resp = client.post("/api/auth/register", json={
        "email": email,
        "password": pwd,
        "invite_code": settings.REGISTRATION_INVITE_CODE
    })
    assert resp.status_code == 200

    resp_login = client.post("/api/auth/login", json={
        "email": email,
        "password": pwd
    })
    assert resp_login.status_code == 200
    token = resp_login.json()["access_token"]
    assert token is not None

    resp_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp_me.status_code == 200
    assert resp_me.json()["email"] == email
