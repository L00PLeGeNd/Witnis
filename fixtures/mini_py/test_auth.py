from auth import AuthService


def test_login_ok() -> None:
    assert AuthService().login("alice", "secret") is True
