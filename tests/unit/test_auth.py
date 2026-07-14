import pytest

from airedteam.api.auth import AuthIdentity, issue_token, verify_identity, verify_token


def test_token_roundtrip():
    tok = issue_token(secret="s", admin_id="admin", ttl_minutes=60)
    sub = verify_token(tok, secret="s")
    assert sub == "admin"


def test_token_rejects_bad_secret():
    tok = issue_token(secret="s", admin_id="admin", ttl_minutes=60)
    with pytest.raises(PermissionError):
        verify_token(tok, secret="other")


def test_token_roundtrip_preserves_oidc_account():
    account = AuthIdentity(
        subject="oidc:abc",
        display_name="Ada Lovelace",
        email="ada@example.com",
        picture="https://example.com/ada.png",
        auth_method="oidc",
    )
    token = issue_token(secret="s", admin_id=account.subject, ttl_minutes=60, identity=account)
    assert verify_identity(token, secret="s") == account
