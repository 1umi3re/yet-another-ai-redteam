from __future__ import annotations
from datetime import UTC, datetime, timedelta
from jose import jwt, JWTError

ALG = "HS256"


def issue_token(*, secret: str, admin_id: str, ttl_minutes: int) -> str:
    payload = {"sub": admin_id, "exp": datetime.now(UTC) + timedelta(minutes=ttl_minutes)}
    return jwt.encode(payload, secret, algorithm=ALG)


def verify_token(token: str, *, secret: str) -> str:
    try:
        data = jwt.decode(token, secret, algorithms=[ALG])
    except JWTError as e:
        raise PermissionError("invalid token") from e
    return data["sub"]
