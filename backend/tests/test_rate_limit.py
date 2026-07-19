"""Unit tests for the in-memory rate limiter — verifies the sliding window logic
without spinning up the full app or a real DB.
"""
from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.shared.rate_limit import RateLimitMiddleware


def make_test_app(limit: int) -> TestClient:
    app = FastAPI()
    app.add_middleware(RateLimitMiddleware, requests_per_minute=limit)

    @app.get("/ping")
    def ping():
        return {"ok": True}

    return TestClient(app)


def test_requests_under_limit_succeed():
    client = make_test_app(limit=5)
    for _ in range(5):
        resp = client.get("/ping")
        assert resp.status_code == 200


def test_requests_over_limit_get_429():
    client = make_test_app(limit=3)
    for _ in range(3):
        assert client.get("/ping").status_code == 200
    resp = client.get("/ping")
    assert resp.status_code == 429
