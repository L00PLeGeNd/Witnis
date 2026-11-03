from auth import AuthService


class AccessGate:
    def __init__(self) -> None:
        self.auth = AuthService()

    def allow(self, username: str, password: str) -> bool:
        return self.auth.login(username, password)


def guarded_entry(username: str, password: str) -> bool:
    return AccessGate().allow(username, password)
