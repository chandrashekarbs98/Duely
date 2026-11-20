from typing import Any

from app.core.errors import AuthError, ConflictError, TooManyRequestsError
from app.core.rate_limit import (
    login_failures_by_email,
    login_failures_by_ip,
    registrations_by_ip,
)
from app.core.security import create_access_token, hash_password, verify_password
from app.models import User
from app.repositories.user import UserRepository
from app.schemas.auth import LoginRequest, RegisterRequest, UserUpdate


class AuthService:
    def __init__(self, users: UserRepository) -> None:
        self.users = users

    def register(self, data: RegisterRequest, client_ip: str) -> tuple[User, str]:
        # Every attempt counts, even ones that fail: each costs a slow bcrypt hash, and
        # "email already exists" answers would otherwise let a bot test addresses in bulk.
        if not registrations_by_ip.try_acquire(client_ip):
            raise TooManyRequestsError("Too many sign-ups from your network. Try again later.")
        if self.users.get_by_email(data.email):
            raise ConflictError("An account with this email already exists.")
        user = self.users.create(
            email=data.email, password_hash=hash_password(data.password), name=data.name
        )
        return user, create_access_token(user.id)

    def login(self, data: LoginRequest, client_ip: str) -> tuple[User, str]:
        if login_failures_by_email.is_blocked(data.email) or login_failures_by_ip.is_blocked(
            client_ip
        ):
            raise TooManyRequestsError("Too many failed attempts. Try again in 15 minutes.")

        user = self.users.get_by_email(data.email)
        # verify_password runs even when the user is missing (constant-ish timing).
        if not verify_password(data.password, user.password_hash if user else None) or not user:
            login_failures_by_email.record(data.email)
            login_failures_by_ip.record(client_ip)
            # Same message for "no such email" and "wrong password": don't reveal which.
            raise AuthError("Invalid email or password.")

        # Success clears the per-email count only. Clearing the per-IP count would let an
        # attacker reset it by logging in to their own account between guesses.
        login_failures_by_email.reset(data.email)
        return user, create_access_token(user.id)

    def update_profile(self, user: User, data: UserUpdate) -> User:
        # exclude_unset: a PATCH only touches fields the client actually sent.
        changes: dict[str, Any] = data.model_dump(exclude_unset=True)
        if changes.get("name") is None:
            changes.pop("name", None)  # name cannot be cleared
        if changes.get("email_reminders") is None:
            changes.pop("email_reminders", None)
        return self.users.update(user, changes)

    def delete_account(self, user: User) -> None:
        self.users.delete(user)
