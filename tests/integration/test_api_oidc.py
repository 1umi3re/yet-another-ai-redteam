from datetime import UTC, datetime, timedelta
from urllib.parse import parse_qs, urlparse

import httpx
import pytest
import respx
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from httpx import ASGITransport, AsyncClient
from jose import jwt
from jose.utils import base64url_encode

ISSUER = "https://issuer.example.com"


def _configure(monkeypatch, tmp_path, *, forced: bool = False):
    monkeypatch.setenv("AIREDTEAM_MASTER_KEY", Fernet.generate_key().decode())
    monkeypatch.setenv("AIREDTEAM_ADMIN_PASSWORD", "letmein")
    monkeypatch.setenv("AIREDTEAM_DATABASE_URL", f"sqlite+aiosqlite:///{tmp_path}/oidc-api.db")
    monkeypatch.setenv("AIREDTEAM_BLOB_DIR", str(tmp_path / "blobs"))
    monkeypatch.setenv("AIREDTEAM_JWT_SECRET", "test-internal-jwt-secret")
    monkeypatch.setenv("AIREDTEAM_OIDC_ENDPOINT", ISSUER)
    monkeypatch.setenv("AIREDTEAM_OIDC_CLIENT_ID", "airedteam-client")
    monkeypatch.setenv("AIREDTEAM_OIDC_CLIENT_SECRET", "client-secret")
    monkeypatch.setenv("AIREDTEAM_OIDC_CALLBACK_URL", "http://test/api/auth/oidc/callback")
    monkeypatch.setenv("AIREDTEAM_FRONTEND_URL", "http://frontend.example.com")
    monkeypatch.setenv("AIREDTEAM_OIDC_FORCE_AUTH", str(forced).lower())


async def _app(monkeypatch, tmp_path, *, forced: bool = False):
    _configure(monkeypatch, tmp_path, forced=forced)
    import airedteam.api.deps as deps
    from airedteam.api.app import create_app
    from airedteam.storage.db import initialize_database, make_engine

    deps._STATE = None
    app = create_app()
    engine = make_engine(deps.get_state().settings.database_url)
    await initialize_database(engine)
    await engine.dispose()
    return app


@pytest.mark.asyncio
async def test_forced_oidc_disables_password_api(monkeypatch, tmp_path):
    app = await _app(monkeypatch, tmp_path, forced=True)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        config = (await client.get("/api/auth/config")).json()
        assert config == {
            "oidc_enabled": True,
            "oidc_forced": True,
            "password_enabled": False,
            "oidc_start_url": "/api/auth/oidc/start",
        }
        response = await client.post("/api/login", json={"password": "letmein"})
        assert response.status_code == 403
        assert "disabled" in response.json()["detail"]


@pytest.mark.asyncio
@respx.mock
async def test_oidc_start_hides_provider_discovery_failure(monkeypatch, tmp_path):
    app = await _app(monkeypatch, tmp_path)
    respx.get(f"{ISSUER}/.well-known/openid-configuration").mock(
        return_value=httpx.Response(503, text="provider details that must not leak")
    )
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/auth/oidc/start")
        assert response.status_code == 503
        assert response.json() == {"detail": "OIDC is unavailable"}


@pytest.mark.asyncio
@respx.mock
async def test_oidc_authorization_callback_ticket_and_profile(monkeypatch, tmp_path):
    app = await _app(monkeypatch, tmp_path)
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        serialization.Encoding.PEM,
        serialization.PrivateFormat.PKCS8,
        serialization.NoEncryption(),
    )
    public_numbers = private_key.public_key().public_numbers()
    public_jwk = {
        "kty": "RSA",
        "kid": "test-key",
        "use": "sig",
        "alg": "RS256",
        "n": base64url_encode(public_numbers.n.to_bytes((public_numbers.n.bit_length() + 7) // 8, "big")).decode(),
        "e": base64url_encode(public_numbers.e.to_bytes((public_numbers.e.bit_length() + 7) // 8, "big")).decode(),
    }
    discovery = {
        "issuer": ISSUER,
        "authorization_endpoint": f"{ISSUER}/authorize",
        "token_endpoint": f"{ISSUER}/token",
        "jwks_uri": f"{ISSUER}/jwks",
        "userinfo_endpoint": f"{ISSUER}/userinfo",
        "id_token_signing_alg_values_supported": ["RS256"],
    }
    respx.get(f"{ISSUER}/.well-known/openid-configuration").mock(
        return_value=httpx.Response(200, json=discovery)
    )
    respx.get(f"{ISSUER}/jwks").mock(return_value=httpx.Response(200, json={"keys": [public_jwk]}))
    respx.get(f"{ISSUER}/userinfo").mock(
        return_value=httpx.Response(
            200,
            json={
                "sub": "provider-user-1",
                "name": "Ada Lovelace",
                "email": "ada@example.com",
                "picture": "https://images.example.com/ada.png",
            },
        )
    )

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=False,
    ) as client:
        start = await client.get("/api/auth/oidc/start", params={"next": "/runs?target=one"})
        assert start.status_code in (302, 307)
        authorization_query = parse_qs(urlparse(start.headers["location"]).query)
        assert authorization_query["client_id"] == ["airedteam-client"]
        assert authorization_query["scope"] == ["openid profile email"]
        assert authorization_query["code_challenge_method"] == ["S256"]
        state = authorization_query["state"][0]
        nonce = authorization_query["nonce"][0]

        def token_response(request: httpx.Request):
            form = parse_qs(request.content.decode())
            assert form["code"] == ["authorization-code"]
            assert form["code_verifier"][0]
            now = datetime.now(UTC)
            id_token = jwt.encode(
                {
                    "iss": ISSUER,
                    "sub": "provider-user-1",
                    "aud": "airedteam-client",
                    "iat": int(now.timestamp()),
                    "exp": int((now + timedelta(minutes=5)).timestamp()),
                    "nonce": nonce,
                    "name": "Ada",
                },
                private_pem,
                algorithm="RS256",
                headers={"kid": "test-key"},
            )
            return httpx.Response(
                200,
                json={
                    "access_token": "provider-access-token",
                    "token_type": "Bearer",
                    "id_token": id_token,
                },
            )

        respx.post(f"{ISSUER}/token").mock(side_effect=token_response)
        callback = await client.get(
            "/api/auth/oidc/callback",
            params={"code": "authorization-code", "state": state},
        )
        assert callback.status_code == 303
        callback_query = parse_qs(urlparse(callback.headers["location"]).query)
        ticket = callback_query["oidc_ticket"][0]
        assert callback_query["next"] == ["/runs?target=one"]

        exchanged = await client.post("/api/auth/oidc/exchange", json={"ticket": ticket})
        assert exchanged.status_code == 200
        payload = exchanged.json()
        assert payload["account"]["display_name"] == "Ada Lovelace"
        assert payload["account"]["email"] == "ada@example.com"
        assert payload["account"]["auth_method"] == "oidc"
        assert payload["next"] == "/runs?target=one"

        profile = await client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {payload['token']}"},
        )
        assert profile.status_code == 200
        assert profile.json() == payload["account"]

        replay = await client.post("/api/auth/oidc/exchange", json={"ticket": ticket})
        assert replay.status_code == 401
        password = await client.post("/api/login", json={"password": "letmein"})
        assert password.status_code == 200
        assert password.json()["account"]["auth_method"] == "password"


@pytest.mark.asyncio
@respx.mock
async def test_oidc_callback_rejects_state_mismatch_without_details(monkeypatch, tmp_path):
    app = await _app(monkeypatch, tmp_path)
    respx.get(f"{ISSUER}/.well-known/openid-configuration").mock(
        return_value=httpx.Response(
            200,
            json={
                "issuer": ISSUER,
                "authorization_endpoint": f"{ISSUER}/authorize",
                "token_endpoint": f"{ISSUER}/token",
                "jwks_uri": f"{ISSUER}/jwks",
            },
        )
    )
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        follow_redirects=False,
    ) as client:
        await client.get("/api/auth/oidc/start")
        callback = await client.get(
            "/api/auth/oidc/callback",
            params={"code": "code", "state": "wrong-state"},
        )
        assert callback.status_code == 303
        assert callback.headers["location"] == (
            "http://frontend.example.com/login?oidc_error=authentication_failed"
        )
