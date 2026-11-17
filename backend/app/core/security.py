"""Password hashing and JWT helpers. No database or HTTP code here."""

from datetime import timedelta

import bcrypt
import jwt

from app.core import clock
from app.core.config import get_settings

_ALGORITHM = "HS256"

# Used when an email is not registered, so a failed login takes the same time either way.
# Otherwise an attacker could time responses to learn which emails have accounts.
_DUMMY_HASH = bcrypt.hashpw(b"timing-equaliser", bcrypt.gensalt()).decode()


def hash_password(password: str) -> str:
    # bcrypt generates a random salt and embeds it (and the cost factor) in the hash string.
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str | None) -> bool:
    candidate = password_hash or _DUMMY_HASH
    matches = bcrypt.checkpw(password.encode(), candidate.encode())
    return matches and password_hash is not None


def create_access_token(user_id: int) -> str:
    settings = get_settings()
    issued = clock.now()
    payload = {
        "sub": str(user_id),
        "iat": issued,
        "exp": issued + timedelta(hours=settings.jwt_expire_hours),
    }
    return jwt.encode(payload, settings.jwt_secret, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> int | None:
    """Return the user id inside a valid token, or None if it is missing, forged or expired."""
    try:
        payload = jwt.decode(
            token,
            get_settings().jwt_secret,
            algorithms=[_ALGORITHM],  # never let the token choose its own algorithm
            options={"require": ["exp", "sub"]},
        )
        return int(payload["sub"])
    except (jwt.PyJWTError, ValueError):
        return None
