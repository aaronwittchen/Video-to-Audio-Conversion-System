import os
import importlib
import types
import pytest


def create_test_client():
    os.environ.setdefault("JWT_SECRET", "test-secret")
    module = importlib.import_module("src.auth.server")
    app = module.server
    app.config["TESTING"] = True
    return app.test_client(), module


def test_health_endpoint_returns_200():
    client, _ = create_test_client()
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "healthy"


def test_validate_missing_auth_header_returns_401():
    client, _ = create_test_client()
    resp = client.post("/validate")
    assert resp.status_code == 401
    body = resp.get_json()
    assert "Authorization" in body["message"] or body["message"].lower().startswith("authorization")

