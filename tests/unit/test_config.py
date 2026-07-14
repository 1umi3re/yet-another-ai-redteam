import pytest
from pydantic import ValidationError

from airedteam.config import Settings


def test_settings_defaults(monkeypatch, tmp_path):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", "0" * 44)
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path))
    s = Settings(_env_file=None)
    assert s.database_url.startswith("sqlite")
    assert s.max_concurrency >= 1
    assert s.jwt_ttl_minutes == 60 * 24 * 7
    assert s.blob_dir == tmp_path
    assert s.monitor_enabled is True
    assert s.dingtalk_webhook_url is None
    assert s.monitor_failure_rate_threshold == 0.5
    assert s.monitor_rate_window_seconds == 300


def test_settings_requires_master_key(monkeypatch):
    monkeypatch.delenv("AIREDTEAM_MASTER_KEY", raising=False)
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "secret")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)


def test_oidc_settings_require_complete_configuration(monkeypatch):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", "0" * 44)
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("AIREDTEAM_OIDC_ENDPOINT", "https://issuer.example.com")
    with pytest.raises(ValidationError, match="partial OIDC configuration"):
        Settings(_env_file=None)


def test_oidc_settings_enable_complete_configuration(monkeypatch):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", "0" * 44)
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("AIREDTEAM_OIDC_ENDPOINT", "https://issuer.example.com")
    monkeypatch.setenv("AIREDTEAM_OIDC_CLIENT_ID", "client")
    monkeypatch.setenv("AIREDTEAM_OIDC_CLIENT_SECRET", "secret")
    monkeypatch.setenv("AIREDTEAM_OIDC_CALLBACK_URL", "https://api.example.com/api/auth/oidc/callback")
    monkeypatch.setenv("AIREDTEAM_FRONTEND_URL", "https://app.example.com")
    monkeypatch.setenv("AIREDTEAM_OIDC_FORCE_AUTH", "true")
    settings = Settings(_env_file=None)
    assert settings.oidc_enabled is True
    assert settings.oidc_force_auth is True


def test_forced_oidc_requires_configuration(monkeypatch):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", "0" * 44)
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "secret")
    monkeypatch.setenv("AIREDTEAM_OIDC_FORCE_AUTH", "true")
    with pytest.raises(ValidationError, match="OIDC_FORCE_AUTH"):
        Settings(_env_file=None)
