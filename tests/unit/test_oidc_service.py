from datetime import UTC, datetime, timedelta

import pytest
from cryptography.fernet import Fernet
from sqlalchemy import update

from airedteam.api.auth import AuthIdentity
from airedteam.config import Settings
from airedteam.services.oidc import OIDCLoginError, OIDCService, safe_next_path
from airedteam.storage.db import initialize_database, make_engine, make_sessionmaker
from airedteam.storage.models import OIDCLoginTicket


def _settings(tmp_path):
    return Settings(
        _env_file=None,
        master_key=Fernet.generate_key().decode(),
        admin_password="password",
        database_url=f"sqlite+aiosqlite:///{tmp_path}/oidc.db",
        blob_dir=tmp_path / "blobs",
        oidc_endpoint="https://issuer.example.com",
        oidc_client_id="client",
        oidc_client_secret="secret",
        oidc_callback_url="http://api.example.com/api/auth/oidc/callback",
        frontend_url="http://app.example.com",
    )


def test_safe_next_path_rejects_external_or_ambiguous_paths():
    assert safe_next_path("/runs?target=1") == "/runs?target=1"
    assert safe_next_path("https://evil.example") == "/dashboard"
    assert safe_next_path("//evil.example") == "/dashboard"
    assert safe_next_path("/\\evil") == "/dashboard"


@pytest.mark.asyncio
async def test_oidc_ticket_is_single_use_and_expires(tmp_path):
    settings = _settings(tmp_path)
    engine = make_engine(settings.database_url)
    await initialize_database(engine)
    sessions = make_sessionmaker(engine)
    service = OIDCService(sessions, settings)
    identity = AuthIdentity("oidc:abc", "Ada", "ada@example.com", None, "oidc")

    ticket = await service._create_ticket(identity, "/runs")
    account, next_path = await service.consume_ticket(ticket)
    assert account == identity
    assert next_path == "/runs"
    with pytest.raises(OIDCLoginError):
        await service.consume_ticket(ticket)

    expired = await service._create_ticket(identity, "/dashboard")
    async with sessions() as session:
        await session.execute(
            update(OIDCLoginTicket)
            .where(OIDCLoginTicket.consumed_at.is_(None))
            .values(expires_at=datetime.now(UTC).replace(tzinfo=None) - timedelta(seconds=1))
        )
        await session.commit()
    with pytest.raises(OIDCLoginError):
        await service.consume_ticket(expired)
    await engine.dispose()


def test_oidc_identity_is_stable_and_normalized(tmp_path):
    service = OIDCService(object(), _settings(tmp_path))
    claims = {
        "sub": "provider-user-1",
        "name": "Ada Lovelace",
        "email": "ada@example.com",
        "picture": "https://example.com/ada.png",
    }
    first = service._identity(claims, issuer="https://issuer.example.com")
    second = service._identity(claims, issuer="https://issuer.example.com")
    assert first == second
    assert first.subject.startswith("oidc:")
    assert len(first.subject) < 100
    assert first.auth_method == "oidc"
