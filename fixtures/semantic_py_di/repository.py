from __future__ import annotations

from models import User


class UserRepository:
    def find_by_id(self, user_id: int) -> User | None:
        if user_id <= 0:
            return None
        return User(user_id, f"user-{user_id}")
