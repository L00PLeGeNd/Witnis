"""Auth gateway for the public_svc sample."""


class TokenGateway:
    def issue(self, user: str) -> str:
        return f"tok-{user}"

    def verify(self, token: str) -> bool:
        return token.startswith("tok-")
