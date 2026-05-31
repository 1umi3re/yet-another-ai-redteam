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


def test_settings_requires_master_key(monkeypatch):
    monkeypatch.delenv("AIREDTEAM_MASTER_KEY", raising=False)
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "secret")
    with pytest.raises(ValidationError):
        Settings(_env_file=None)
