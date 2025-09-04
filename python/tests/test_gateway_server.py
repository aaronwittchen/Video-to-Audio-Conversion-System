import os
import importlib
import json
import pytest


def create_test_client():
    os.environ.setdefault("AUTH_SVC_ADDRESS", "auth:5000")
    module = importlib.import_module("src.gateway.server")
    app = module.server
    app.config["TESTING"] = True
    return app.test_client(), module


def test_login_route_exists():
    client, _ = create_test_client()
    # This route expects Basic Auth proxied call format in code; just ensure it exists and returns something (probably 500 without auth backend)
    resp = client.post("/login")
    assert resp.status_code in (200, 401, 500)


def test_upload_without_token_returns_error():
    client, _ = create_test_client()
    resp = client.post("/upload")
    assert resp.status_code in (400, 401)

