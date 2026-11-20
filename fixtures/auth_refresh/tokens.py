"""Token issuance and refresh storage."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TokenPair:
    access: str
    refresh: str
    refresh_expired: bool = False


class TokenStore:
    def __init__(self) -> None:
        self._by_refresh: dict[str, TokenPair] = {}
        self._seq = 0

    def issue(self, subject: str) -> TokenPair:
        self._seq += 1
        pair = TokenPair(
            access=f"access-{subject}-{self._seq}",
            refresh=f"refresh-{subject}-{self._seq}",
        )
        self._by_refresh[pair.refresh] = pair
        return pair

    def lookup(self, refresh: str) -> TokenPair | None:
        return self._by_refresh.get(refresh)

    def rotate(self, refresh: str) -> TokenPair | None:
        current = self.lookup(refresh)
        if current is None:
            return None
        if current.refresh_expired:
            return None
        # subject = access-{subject}-{n}
        parts = current.access.split("-")
        subject = parts[1] if len(parts) >= 2 else "user"
        new_pair = self.issue(subject)
        del self._by_refresh[refresh]
        return new_pair
