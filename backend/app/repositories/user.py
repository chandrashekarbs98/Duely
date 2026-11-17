from datetime import date
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import User


class UserRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def get(self, user_id: int) -> User | None:
        return self.db.get(User, user_id)

    def get_by_email(self, email: str) -> User | None:
        return self.db.scalar(select(User).where(User.email == email))

    def create(self, *, email: str, password_hash: str, name: str) -> User:
        user = User(email=email, password_hash=password_hash, name=name)
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: User, changes: dict[str, Any]) -> User:
        for field, value in changes.items():
            setattr(user, field, value)
        self.db.commit()
        self.db.refresh(user)
        return user

    def delete(self, user: User) -> None:
        # ON DELETE CASCADE on the foreign keys removes the user's todos and finances too.
        self.db.delete(user)
        self.db.commit()

    def reminder_recipients(self, today: date) -> list[User]:
        """Users who opted in and have not had a digest today."""
        stmt = (
            select(User)
            .where(User.email_reminders.is_(True))
            .where(or_(User.last_reminder_sent_on.is_(None), User.last_reminder_sent_on < today))
            .order_by(User.id)
        )
        return list(self.db.scalars(stmt))
