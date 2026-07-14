from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt

ALG = "HS256"


@dataclass(frozen=True)
class AuthIdentity:
    subject: str
    display_name: str
    email: str | None = None
    picture: str | None = None
    auth_method: str = "password"

    def public(self) -> dict[str, str | None]:
        return asdict(self)


def issue_token(
    *,
    secret: str,
    admin_id: str,
    ttl_minutes: int,
    identity: AuthIdentity | None = None,
) -> str:
    account = identity or AuthIdentity(subject=admin_id, display_name="Administrator")
    payload: dict[str, Any] = {
        "sub": account.subject,
        "name": account.display_name,
        "email": account.email,
        "picture": account.picture,
        "auth_method": account.auth_method,
        "iat": datetime.now(UTC),
        "exp": datetime.now(UTC) + timedelta(minutes=ttl_minutes),
    }
    return jwt.encode(payload, secret, algorithm=ALG)


def verify_identity(token: str, *, secret: str) -> AuthIdentity:
    try:
        data = jwt.decode(token, secret, algorithms=[ALG])
        subject = data["sub"]
        if not isinstance(subject, str) or not subject:
            raise JWTError("invalid subject")
    except (JWTError, KeyError, TypeError) as e:
        raise PermissionError("invalid token") from e
    return AuthIdentity(
        subject=subject,
        display_name=str(data.get("name") or subject),
        email=str(data["email"]) if data.get("email") else None,
        picture=str(data["picture"]) if data.get("picture") else None,
        auth_method=str(data.get("auth_method") or "password"),
    )


def verify_token(token: str, *, secret: str) -> str:
    return verify_identity(token, secret=secret).subject
