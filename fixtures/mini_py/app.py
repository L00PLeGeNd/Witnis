from auth import AuthService
from gate import guarded_entry


def main() -> None:
    service = AuthService()
    service.login("alice", "secret")
    guarded_entry("alice", "secret")


if __name__ == "__main__":
    main()
