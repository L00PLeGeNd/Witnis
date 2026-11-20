"""Session helper for public_svc."""

from .gateway import TokenGateway


class Session:
    def __init__(self, gateway: TokenGateway | None = None) -> None:
        self.gateway = gateway or TokenGateway()

    def login(self, user: str) -> str:
        return self.gateway.issue(user)

    def ok(self, token: str) -> bool:
        return self.gateway.verify(token)
