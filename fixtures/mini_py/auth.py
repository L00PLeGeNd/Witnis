"""Tiny fixture module for Witnis v0.1 indexing demos."""


def audit(fn):  # type: ignore[no-untyped-def]
    return fn


class AuthService:
    """Handles login for the sample app."""

    @audit
    def login(self, username: str, password: str) -> bool:
        return bool(username and password)


def public_helper() -> str:
    return "ok"


class SecureAuth(AuthService):
    """Subclass used to exercise inheritance edges."""

    def login(self, username: str, password: str) -> bool:
        return super().login(username, password) and username != "banned"
