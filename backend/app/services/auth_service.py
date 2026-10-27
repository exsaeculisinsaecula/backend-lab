from __future__ import annotations

import uuid

from sqlalchemy.orm import Session

from app.models import User
from app.security import hash_password


class AuthService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get_by_email(self, email: str) -> User | None:
        return self.db.query(User).filter(User.email == email.lower()).first()

    def get(self, user_id: str) -> User | None:
        return self.db.get(User, user_id)

    def create_user(self, *, email: str, username: str, password: str) -> User:
        user = User(
            id=f"u-{uuid.uuid4().hex[:12]}",
            email=email.lower(),
            username=username,
            password_hash=hash_password(password),
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def verify(self, user: User, password: str) -> bool:
        return verify_password_local(password, user.password_hash)


def verify_password_local(password: str, password_hash: str) -> bool:
    from app.security import verify_password

    return verify_password(password, password_hash)
