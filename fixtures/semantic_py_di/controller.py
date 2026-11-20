from __future__ import annotations

from models import User
from service import UserService


class UserController:
    def __init__(self, user_service: UserService) -> None:
        self.user_service = user_service

    def get(self, user_id: int) -> User | None:
        return self.user_service.find_user(user_id)
