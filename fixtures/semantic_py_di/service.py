from __future__ import annotations

from models import User
from repository import UserRepository


class UserService:
    def __init__(self, repository: UserRepository) -> None:
        self.repository = repository

    def find_user(self, user_id: int) -> User | None:
        return self.repository.find_by_id(user_id)
