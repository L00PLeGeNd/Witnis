from __future__ import annotations

from controller import AuthController
from service import AuthService
from tokens import TokenStore


def test_login_ok() -> None:
    ctl = AuthController()
    pair = ctl.post_login("alice", "secret")
    assert pair is not None
    assert pair.access.startswith("access-alice")


def test_refresh_ok() -> None:
    store = TokenStore()
    svc = AuthService(store)
    pair = svc.login("alice", "secret")
    assert pair is not None
    rotated = svc.refresh_token(pair.refresh)
    assert rotated is not None
    assert rotated.refresh != pair.refresh


def test_refresh_rejects_expired() -> None:
    store = TokenStore()
    svc = AuthService(store)
    pair = svc.login("alice", "secret")
    assert pair is not None
    stored = store.lookup(pair.refresh)
    assert stored is not None
    stored.refresh_expired = True
    assert svc.refresh_token(pair.refresh) is None
