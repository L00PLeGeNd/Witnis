"""Auth filter / middleware — gates requests on access tokens."""

from __future__ import annotations

from service import AuthService
from tokens import TokenStore


class AuthFilter:
    def __init__(self, service: AuthService | None = None) -> None:
        self.service = service or AuthService(TokenStore())

    def allow(self, access: str | None) -> bool:
        return bool(access) and str(access).startswith("access-")

    def refresh_via_filter(self, refresh: str) -> bool:
        pair = self.service.refresh_token(refresh)
        return pair is not None
