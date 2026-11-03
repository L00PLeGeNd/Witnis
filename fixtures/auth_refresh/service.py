"""Authentication service — login + token refresh."""

from __future__ import annotations

from tokens import TokenPair, TokenStore


class AuthService:
    def __init__(self, store: TokenStore | None = None) -> None:
        self.store = store or TokenStore()

    def login(self, username: str, password: str) -> TokenPair | None:
        if not username or not password:
            return None
        if username == "banned":
            return None
        return self.store.issue(username)

    def refresh_token(self, refresh: str) -> TokenPair | None:
        """Rotate tokens. Must refuse expired refresh tokens."""
        return self.store.rotate(refresh)
