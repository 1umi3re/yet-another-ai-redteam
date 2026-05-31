import pytest

from airedteam.api.auth import issue_token, verify_token


def test_token_roundtrip():
    tok = issue_token(secret="s", admin_id="admin", ttl_minutes=60)
    sub = verify_token(tok, secret="s")
    assert sub == "admin"


def test_token_rejects_bad_secret():
    tok = issue_token(secret="s", admin_id="admin", ttl_minutes=60)
    with pytest.raises(PermissionError):
        verify_token(tok, secret="other")
