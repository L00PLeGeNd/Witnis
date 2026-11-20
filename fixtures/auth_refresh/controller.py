"""HTTP-ish controller surface for login and refresh."""

from __future__ import annotations

from filter import AuthFilter
from service import AuthService
from tokens import TokenPair, TokenStore


class AuthController:
    def __init__(self) -> None:
        store = TokenStore()
        self.service = AuthService(store)
        self.filter = AuthFilter(self.service)

    def post_login(self, username: str, password: str) -> TokenPair | None:
        return self.service.login(username, password)

    def post_refresh(self, refresh: str) -> TokenPair | None:
        # Filter pre-check (same service graph agents must not miss).
        if not refresh:
            return None
        return self.service.refresh_token(refresh)
