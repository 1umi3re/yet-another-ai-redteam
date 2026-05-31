from __future__ import annotations

import json

from cryptography.fernet import Fernet


class SecretBox:
    def __init__(self, key: str) -> None:
        self._f = Fernet(key.encode() if isinstance(key, str) else key)

    def encrypt(self, payload: dict) -> bytes:
        return self._f.encrypt(json.dumps(payload, separators=(",", ":")).encode())

    def decrypt(self, ct: bytes) -> dict:
        return json.loads(self._f.decrypt(ct).decode())
