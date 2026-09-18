from __future__ import annotations

import pytest

from cybersecurity_suite import create_app
from cybersecurity_suite.config import TestConfig


@pytest.fixture()
def app():
    return create_app(TestConfig)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def auth_token(client) -> str:
    response = client.post(
        "/auth/login", json={"username": "admin", "password": "change-me-please"}
    )
    assert response.status_code == 200
    return response.get_json()["access_token"]
