"""API tests for Reqres (https://reqres.in) using pytest + requests.

Reqres now requires a free API key. Get one at https://reqres.in and set:
    export REQRES_API_KEY=your_key        (Windows: set REQRES_API_KEY=your_key)
"""
import os

import pytest
import requests

BASE_URL = "https://reqres.in/api"
TIMEOUT = 10  # seconds; never let a test hang forever


@pytest.fixture(scope="module")
def session():
    """SETUP: one shared HTTP session with the API key header.
    TEARDOWN: session is closed after all tests in this file finish."""
    key = os.getenv("REQRES_API_KEY")
    if not key:
        pytest.skip("Set REQRES_API_KEY environment variable first")
    s = requests.Session()
    s.headers.update({"x-api-key": key})
    yield s
    s.close()


def test_list_users_success(session):
    """Positive: status 200 + response structure is correct."""
    r = session.get(f"{BASE_URL}/users", params={"page": 2}, timeout=TIMEOUT)
    assert r.status_code == 200
    body = r.json()
    assert body["page"] == 2            # value is correct
    assert isinstance(body["data"], list) and len(body["data"]) > 0
    assert {"id", "email", "first_name"} <= body["data"][0].keys()  # keys exist


def test_single_user_content(session):
    """Positive: validate actual content of one user."""
    r = session.get(f"{BASE_URL}/users/2", timeout=TIMEOUT)
    assert r.status_code == 200
    user = r.json()["data"]
    assert user["id"] == 2
    assert "@" in user["email"]         # email looks like an email


def test_login_missing_password(session):
    """Negative: missing parameter -> 400 and an error message."""
    r = session.post(f"{BASE_URL}/login", json={"email": "eve.holt@reqres.in"}, timeout=TIMEOUT)
    assert r.status_code == 400
    assert "error" in r.json()
    assert "password" in r.json()["error"].lower()


def test_user_not_found(session):
    """Negative: invalid resource id -> 404 with an empty body."""
    r = session.get(f"{BASE_URL}/users/23", timeout=TIMEOUT)
    assert r.status_code == 404
    assert r.json() == {}
