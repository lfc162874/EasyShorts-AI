from fastapi.testclient import TestClient

from app.main import app


def test_healthcheck():
    with TestClient(app) as client:
        response = client.get("/easy-shorts/health")
        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 0
        assert payload["data"]["api_prefix"] == "/easy-shorts"


def test_default_admin_login():
    with TestClient(app) as client:
        response = client.post(
            "/easy-shorts/auth/login",
            json={"username": "admin", "password": "Admin@123456"},
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["code"] == 0
        assert payload["data"]["user"]["username"] == "admin"
        assert payload["data"]["access_token"]
