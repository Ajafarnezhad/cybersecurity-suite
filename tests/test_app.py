from __future__ import annotations


def test_index(client):
    response = client.get("/")
    assert response.status_code == 200
    assert response.get_json() == {"message": "Welcome to CyberSecuritySuite"}


def test_404(client):
    response = client.get("/does-not-exist")
    assert response.status_code == 404


def test_login_success(client):
    response = client.post(
        "/auth/login", json={"username": "admin", "password": "change-me-please"}
    )
    assert response.status_code == 200
    assert "access_token" in response.get_json()


def test_login_wrong_password(client):
    response = client.post("/auth/login", json={"username": "admin", "password": "wrong"})
    assert response.status_code == 401


def test_login_missing_fields(client):
    response = client.post("/auth/login", json={})
    assert response.status_code == 400


def test_scan_requires_auth(client):
    response = client.post("/scan/port", json={"target": "127.0.0.1", "ports": "1-10"})
    assert response.status_code == 401


def test_scan_rejects_invalid_target(client, auth_token):
    response = client.post(
        "/scan/port",
        json={"target": "not-an-ip", "ports": "1-10"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 400


def test_scan_rejects_oversized_port_range(client, auth_token):
    response = client.post(
        "/scan/port",
        json={"target": "127.0.0.1", "ports": "1-70000"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 400


def test_scan_port_happy_path(client, auth_token):
    response = client.post(
        "/scan/port",
        json={"target": "127.0.0.1", "ports": "65530-65532"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 200
    body = response.get_json()
    assert "results" in body
    assert "report" in body


def test_static_analysis_rejects_path_traversal(app, client, auth_token, tmp_path):
    app.config["SCAN_ALLOWED_ROOT"] = str(tmp_path)

    response = client.post(
        "/scan/static",
        json={"path": "../../etc/passwd"},
        headers={"Authorization": f"Bearer {auth_token}"},
    )
    assert response.status_code == 400


def test_chat_status(client):
    response = client.get("/chat/status")
    assert response.status_code == 200
    assert response.get_json() == {"enabled": False}
